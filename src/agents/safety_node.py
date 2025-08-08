import logging
import os
import time
from typing import Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field, ValidationError
import requests  # To handle connection-related exceptions

from graph.state import GraphState
from schemas.messages import ReportSectionsDraft

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SafetyCheckResult(BaseModel):
    """
    A Pydantic model to validate the LLM's safety check output.
    """
    is_safe: bool = Field(
        description="True if the content is safe and free of harmful, biased, or inappropriate language.")
    is_accurate: bool = Field(
        description="True if the report is logically consistent with the data profile and user instructions.")
    reasoning: str = Field(description="Explanation for the decision, especially if the check fails.")


def safety_check_node(state: GraphState) -> GraphState:
    """
    Performs a comprehensive safety and accuracy check on the generated report draft.
    This node now uses an LLM to act as a validator.
    """
    logger.info("---PERFORMING COMPREHENSIVE SAFETY AND ACCURACY CHECK---")

    report_draft = state.get("report_sections_draft")
    dataframe_profile = state.get("dataframe_profile")
    instructions = state.get("instructions")

    if not report_draft or not dataframe_profile or not instructions:
        logger.warning("Missing required state information for safety check. Skipping.")
        return state

    # Implement retry logic with exponential backoff for resilience
    max_retries = 3
    base_delay = 2  # seconds

    # Initialize the LLM with a timeout
    try:
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not gemini_api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables.")

        # The 'request_options' parameter allows setting a timeout.
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-pro",
            google_api_key=gemini_api_key,
            temperature=0.2,
        )
    except Exception as e:
        logger.error(f"Failed to initialize LLM for safety check: {e}")
        state['status'] = "error"
        state['error_message'] = f"Failed to initialize LLM for safety check: {e}"
        return state

    for attempt in range(max_retries):
        try:
            logger.info(f"Attempt {attempt + 1}/{max_retries} to invoke LLM for safety check...")

            # Set up the Pydantic parser
            parser = JsonOutputParser(pydantic_object=SafetyCheckResult)

            prompt_template = """
            You are an expert report reviewer. Your task is to validate a drafted report for both safety and accuracy.

            Please review the following:

            1.  **Report Draft**:
                {report_draft}
            2.  **Original Instructions**:
                {instructions}
            3.  **Dataset Profile**:
                {dataframe_profile}

            {format_instructions}

            Do not add any text outside of the JSON object.
            """

            prompt = PromptTemplate.from_template(prompt_template).format(
                report_draft=report_draft.model_dump_json(indent=2),
                instructions=instructions,
                dataframe_profile=dataframe_profile.model_dump_json(indent=2),
                format_instructions=parser.get_format_instructions()
            )

            llm_response = llm.invoke(prompt, config={"request_options": {"timeout": 60}})

            # Use the parser to get a validated dictionary from the LLM response
            validated_result = parser.invoke(llm_response)

            # Check for safety and accuracy
            if not validated_result['is_safe']:
                error_msg = f"Safety check failed: {validated_result['reasoning']}"
                logger.error(error_msg)
                state['status'] = "error"
                state['error_message'] = error_msg
                return state

            if not validated_result['is_accurate']:
                error_msg = f"Accuracy check failed: {validated_result['reasoning']}"
                logger.error(error_msg)
                state['status'] = "error"
                state['error_message'] = error_msg
                return state

            logger.info("Comprehensive safety and accuracy check passed.")
            state['status'] = "safety_checked"
            return state

        # Handle specific exceptions for retries
        except (requests.exceptions.RequestException, TimeoutError) as e:
            logger.warning(f"Attempt {attempt + 1} failed due to a network or timeout error: {e}")
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                logger.info(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                logger.error("Max retries reached. LLM call failed.")
                state['status'] = "error"
                state['error_message'] = f"Failed to get a response from the LLM after {max_retries} attempts: {e}"
                return state

        # Handle parsing or validation errors, which are not retryable
        except (ValidationError, ValueError, Exception) as e:
            logger.error(f"Non-retryable error: LLM response parsing or validation failed: {e}")
            state['status'] = "error"
            state['error_message'] = f"Report validation failed due to an internal error: {e}"
            return state

    # This part should be unreachable due to the return statements inside the loop
    # but serves as a final fallback.
    state['status'] = "error"
    state['error_message'] = "An unexpected error occurred during the safety check."
    return state
