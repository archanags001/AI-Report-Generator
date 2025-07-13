import logging
import json
import os
from typing import List
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field, ValidationError
from graph.state import GraphState
from schemas.messages import AnalysisInsight
logger = logging.getLogger(__name__)
class GeneratedInsightsOutput(BaseModel):
    insights: List[AnalysisInsight] = Field(
        description="A list of key insights derived from the data profile and visualizations.")


def insight_generation_node(state: GraphState) -> GraphState:
    """
    Generates high-level analytical insights based on the data profile and generated visuals.
    """
    request_id = state['request_id']
    instructions = state['instructions']
    dataframe_profile = state['dataframe_profile']
    generated_visuals = state['generated_visuals']

    logger.info(f"InsightGenerationNode processing request: {request_id}")
    logger.info(f"DEBUG: Entering InsightGenerationNode. Current status: {state['status']}")

    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        logger.error(f"GEMINI_API_KEY not found for request {request_id}. Please ensure it's set in your .env file.")
        state['status'] = "error"
        state['error_message'] = "API key for Gemini not found. Please set GEMINI_API_KEY in your .env file."
        return state

    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=gemini_api_key, temperature=0.7)

    profile_summary = ""
    if dataframe_profile:
        profile_summary = f"Dataset Profile Summary:\nRows: {dataframe_profile.num_rows}\nColumns: {dataframe_profile.num_columns}\nKey Observations: {dataframe_profile.key_observations}\n\nColumn Details (Type, Missing Values, Stats):\n"
        for col_name, details in dataframe_profile.column_details.items():
            profile_summary += f"- {col_name} (Type: {details.get('type', 'N/A')}): Unique: {details.get('unique_values_count', 'N/A')}, Missing: {details.get('missing_values_percentage', 'N/A')}%"
            if 'mean' in details:
                profile_summary += f", Mean: {details['mean']:.2f}, Std: {details['std']:.2f}"
            profile_summary += "\n"

    visuals_context = ""
    if generated_visuals:
        visuals_context = "\n\nGenerated Visualizations:\n"
        for i, visual in enumerate(generated_visuals):
            visuals_context += f"Chart {i + 1} (ID: {visual.visual_id}, Type: {visual.type}, Suggested Section: {visual.suggested_section}):\n"
            visuals_context += f"Description: {visual.description}\n"
            visuals_context += f"Image File: {visual.file_path}\n"  # Include path for context
            visuals_context += "---\n"

    parser = JsonOutputParser(pydantic_object=GeneratedInsightsOutput)
    prompt = PromptTemplate(
        template="""
        You are an expert data analyst AI.
        Based on the provided dataset profile, user instructions, and a list of generated visualizations,
        identify and summarize key insights.

        Focus on:
        - Major trends or patterns.
        - Anomalies or unexpected findings.
        - Relationships between variables (e.g., correlations, impacts).
        - Answers to questions implied by the user's instructions.
        - Potential implications for the business or next steps.

        For each insight, provide:
        - `insight_id`: A unique identifier for the insight (e.g., 'insight_1', 'insight_churn_rate').
        - `title`: A concise, descriptive title for the insight.
        - `summary`: A detailed explanation of the insight, supported by data points or references to chart descriptions.
        - `suggested_section`: Where this insight would best fit in a report (e.g., 'Key Findings', 'Sales Analysis', 'Customer Segmentation', 'Conclusion').
        - `related_visual_ids`: A list of `visual_id`s (e.g., 'chart_REQUESTID_1', 'chart_REQUESTID_2') that directly support or illustrate this insight. Leave empty if no specific visual supports it.

        ---
        Dataset Profile:
        {profile_summary}

        ---
        {visuals_context}

        ---
        User Request/Instructions:
        {instructions}

        ---
        Generate 3-10 high-quality, distinct insights.

        {format_instructions}

        Ensure your response is valid JSON.
        """,
        input_variables=["profile_summary", "visuals_context", "instructions"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )

    generated_insights: List[AnalysisInsight] = []
    try:
        logger.info(f"DEBUG: Calling LLM for insight generation.")
        llm_response = llm.invoke(prompt.invoke({
            "profile_summary": profile_summary,
            "visuals_context": visuals_context,
            "instructions": instructions
        }))
        llm_raw_output_str = llm_response.content

        stripped_str = llm_raw_output_str.strip()
        if stripped_str.startswith("```json") and stripped_str.endswith("```"):
            json_str = stripped_str[len("```json"):-len("```")].strip()
        else:
            json_str = stripped_str

        parsed_insights_output = GeneratedInsightsOutput.model_validate_json(json_str)
        generated_insights = parsed_insights_output.insights
        logger.info(f"DEBUG: LLM returned {len(generated_insights)} insights.")

    except (json.JSONDecodeError, ValidationError) as e:
        logger.error(f"Error parsing LLM JSON for insights for request {request_id}: {e}", exc_info=True)
        state['status'] = "error"
        state[
            'error_message'] = f"LLM output for insights was invalid JSON or schema: {e}. Raw LLM Output: {llm_raw_output_str[:500]}..."
        return state
    except Exception as e:
        logger.error(
            f"An unexpected error occurred during LLM call for insight generation for request {request_id}: {e}",
            exc_info=True)
        state['status'] = "error"
        state['error_message'] = f"An unexpected error occurred during insight generation LLM call: {e}"
        return state

    state['analysis_insights'] = generated_insights
    state['status'] = "insights_generated"
    logger.info(
        f"InsightGenerationNode completed for request: {request_id}. Generated {len(generated_insights)} insights.")
    return state