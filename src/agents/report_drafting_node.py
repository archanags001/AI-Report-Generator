import logging
import json
import os
import time
import requests
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field, ValidationError
from graph.state import GraphState
from schemas.messages import ReportSectionsDraft

logger = logging.getLogger(__name__)


# The Pydantic model for the LLM's output is already defined in messages.py as ReportSectionsDraft

def report_drafting_node(state: GraphState) -> GraphState:
    """
    Generates the initial draft of the report sections (introduction, narratives, takeaways, conclusion)
    based on the data profile, generated insights, and visuals.
    """
    request_id = state['request_id']
    # instructions = state['instructions']
    # dataframe_profile = state['dataframe_profile']
    # analysis_insights = state['analysis_insights']
    # generated_visuals = state['generated_visuals']
    dataset_name = state.get('dataset_name', 'Unnamed Dataset')

    instructions = state.get('instructions', "")
    dataframe_profile = state.get('dataframe_profile', None)
    analysis_insights = state.get('analysis_insights', None)
    generated_visuals = state.get('generated_visuals', None)

    if not dataframe_profile or not analysis_insights or not generated_visuals:
        logger.error(f"Missing data profile, insights, or visuals for request {request_id}.")
        state['status'] = "error"
        state['error_message'] = "Cannot draft report: Missing data profile, insights, or visuals."
        return state



    logger.info(f"ReportDraftingNode processing request: {request_id}")
    logger.info(f"DEBUG: Entering ReportDraftingNode. Current status: {state['status']}")

    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        logger.error(f"GEMINI_API_KEY not found for request {request_id}. Please ensure it's set in your .env file.")
        state['status'] = "error"
        state['error_message'] = "API key for Gemini not found. Please set GEMINI_API_KEY in your .env file."
        return state

    try:
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=gemini_api_key, temperature=0.7)
    except Exception as e:
        logger.error(f"Failed to initialize LLM for report drafting: {e}", exc_info=True)
        state['status'] = "error"
        state['error_message'] = f"Failed to initialize LLM for report drafting: {e}"
        return state

    # Prepare context for the LLM
    profile_summary = ""
    if dataframe_profile:
        profile_summary = f"Dataset Profile Summary:\nRows: {dataframe_profile.num_rows}\nColumns: {dataframe_profile.num_columns}\nKey Observations: {dataframe_profile.key_observations}\n\nColumn Details:\n"
        for col_name, details in dataframe_profile.column_details.items():
            profile_summary += f"- {col_name} (Type: {details.get('type', 'N/A')}): Unique: {details.get('unique_values_count', 'N/A')}, Missing: {details.get('missing_values_percentage', 'N/A')}%"
            if 'mean' in details:
                profile_summary += f", Mean: {details['mean']:.2f}, Std: {details['std']:.2f}"
            profile_summary += "\n"

    insights_context = ""
    if analysis_insights:
        insights_context = "\n\nKey Insights Derived:\n"
        for i, insight in enumerate(analysis_insights):
            insights_context += f"Insight {i + 1} (ID: {insight.insight_id}):\n"
            insights_context += f"Title: {insight.title}\n"
            insights_context += f"Summary: {insight.narrative}\n"
            if insight.supporting_visual_ids:
                insights_context += f"Supported by Visuals: {', '.join(insight.supporting_visual_ids)}\n"
            insights_context += "---\n"

    visuals_context = ""
    visual_reference_for_llm = []
    if generated_visuals:
        visuals_context = "\n\nGenerated Visualizations (for reference in report):\n"
        for i, visual in enumerate(generated_visuals):
            visuals_context += f"Visual ID: {visual.visual_id}\n"
            visuals_context += f"Description: {visual.description}\n"
            visuals_context += "---\n"
            visual_reference_for_llm.append({
                "visual_id": visual.visual_id,
                "description": visual.description
            })
    max_retries = 3
    base_delay = 2  # seconds
    llm_raw_output_str = ""
    report_draft = None

    for attempt in range(max_retries):
        try:
            logger.info(f"Attempt {attempt + 1}/{max_retries} to invoke LLM for report drafting...")
            parser = JsonOutputParser(pydantic_object=ReportSectionsDraft)
            prompt = PromptTemplate(
                template="""
                You are an expert report writer and data storyteller.
                Based on the provided dataset profile, a list of key analytical insights,
                a list of generated visualizations, and original user instructions,
                draft the core sections of a professional data analysis report.
        
                Your response MUST be a valid JSON object formatted EXACTLY as per the provided schema.
        
                The JSON should contain:
                - `introduction_text`: A comprehensive introduction to the report,
                                        including the purpose, the dataset being analyzed, and what the reader can expect.
                - `analysis_narratives`: A list of detailed narrative strings, where each narrative explains an insight.
                                         **Crucially, refer to the generated visuals using generic placeholders like '[FIGURE 1]', '[FIGURE 2]', etc., in numerical order as you introduce them.**
                                         Ensure each narrative flows logically and explains the finding, its context, and implications. A narrative title is a must, followed by ':-' to separate it from the content.
                - `key_takeaways_bullet_points`: A list of concise, actionable bullet points summarizing the main conclusions or implications.
                - `conclusion_text`: A summary conclusion that reiterates the main findings and suggests potential next steps.
                - `dataset_title`: A concise, descriptive title for the dataset based on its content, suitable for use in the overall report title.
                - `figure_id_map`: A dictionary mapping your generated generic placeholders (e.g., "[FIGURE 1]") to the actual 'visual_id's from the 'Generated Visualizations' list provided below. Make sure the order in this map matches the order you referenced the figures in your narratives.
                - `clarification_questions`: A list of any questions you might have for the user if something is unclear
                                             or if you need more context to improve the report.
        
                ---
                Dataset Profile:
                {profile_summary}
        
                ---
                Key Insights Derived (IMPORTANT: Use these to write your narratives):
                {insights_context}
        
                ---
                Generated Visualizations (Reference these in your narratives and map them):
                {visuals_context}
                Available Visual IDs and Descriptions: {visual_reference_for_llm}
        
                ---
                User Request/Instructions for the Report:
                {instructions}
        
                ---
                Generate a comprehensive report draft.
                Remember to use `[FIGURE N]` placeholders in your narratives and populate the `figure_id_map` accurately.
        
                {format_instructions}
        
                Ensure your response is valid JSON.
                """,
                input_variables=["profile_summary", "insights_context", "visuals_context", "instructions",
                                 "visual_reference_for_llm", "dataset_name"],  # Added visual_reference_for_llm
                partial_variables={"format_instructions": parser.get_format_instructions()},
            )


            llm_response = llm.invoke(prompt.invoke({
                "profile_summary": profile_summary,
                "insights_context": insights_context,
                "visuals_context": visuals_context,
                "instructions": instructions,
                "visual_reference_for_llm": visual_reference_for_llm,
                "dataset_name": dataset_name
            }), config={"request_options": {"timeout": 60}})
            llm_raw_output_str = llm_response.content

            stripped_str = llm_raw_output_str.strip()
            if stripped_str.startswith("```json") and stripped_str.endswith("```"):
                json_str = stripped_str[len("```json"):-len("```")].strip()
            else:
                json_str = stripped_str

            parsed_draft_output_dict = json.loads(json_str)

            report_draft = ReportSectionsDraft.model_validate(parsed_draft_output_dict)

            logger.info(f"DEBUG: LLM returned report draft sections.")

            break

        except (requests.exceptions.RequestException, TimeoutError) as e:
            logger.warning(f"LLM call failed on attempt {attempt + 1}/{max_retries} due to network/timeout: {e}")
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                logger.info(f"Retrying LLM call for request {request_id} in {delay} seconds...")
                time.sleep(delay)
            else:
                logger.error(f"Max retries reached. LLM call failed for request {request_id}.")
                state['status'] = "error"
                state['error_message'] = f"Failed to get a response from the LLM after {max_retries} attempts: {e}"
                return state

        except (json.JSONDecodeError, ValidationError) as e:
            logger.error(f"Error parsing LLM JSON for report draft for request {request_id}: {e}", exc_info=True)
            logger.error(f"Raw LLM Output: {llm_raw_output_str[:1000]}...")
            state['status'] = "error"
            state[
                'error_message'] = f"LLM output for report draft was invalid JSON or schema: {e}. Raw LLM Output: {llm_raw_output_str[:1000]}..."
            return state
        except Exception as e:
            logger.error(f"An unexpected error occurred during LLM call for report drafting for request {request_id}: {e}",
                         exc_info=True)
            state['status'] = "error"
            state['error_message'] = f"An unexpected error occurred during report drafting LLM call: {e}"
            return state
    if report_draft:
        state['report_sections_draft'] = report_draft
        # if report_draft.clarification_questions:
        #     state['status'] = "clarification_needed"
        # else:
        state['status'] = "report_drafted"

        logger.info(f"ReportDraftingNode completed for request: {request_id}. Report drafted.")
    else:
        # Fallback if the loop finishes without a successful break
        state['status'] = "error"
        state['error_message'] = "An unexpected failure occurred after all LLM retries or no report draft was generated."
    return state



