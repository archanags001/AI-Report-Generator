import logging
import pandas as pd
import json
import os
import requests
import time
from typing import List, Dict, Any, Optional
import matplotlib.pyplot as plt
import seaborn as sns
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field, ValidationError
from graph.state import GraphState
from schemas.messages import VisualGenerationInstruction, GeneratedVisual

logger = logging.getLogger(__name__)

CHART_OUTPUT_DIR = os.path.join("local_app_data", "charts")
os.makedirs(CHART_OUTPUT_DIR, exist_ok=True)



class SuggestedVisualizations(BaseModel):
    suggestions: List[VisualGenerationInstruction] = Field(
        description="A list of suggested visualizations, including chart type, columns, title, and description.")


def generate_chart(df: pd.DataFrame, instruction: VisualGenerationInstruction, output_path: str) -> Optional[str]:
    """
    Generates a chart based on the instruction and saves it to the output path.
    Returns the file_path if successful, None otherwise.
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    chart_code_str = ""

    try:
        if not instruction.columns or not all(col in df.columns for col in instruction.columns):
            missing_cols = [col for col in instruction.columns if col not in df.columns]
            logger.warning(
                f"Skipping chart generation: Missing or invalid columns {missing_cols} for instruction: {instruction.model_dump_json()}")
            plt.close(fig)
            return None

        for col in instruction.columns:
            if instruction.type in ["histogram", "boxplot", "line", "scatter"] and not pd.api.types.is_numeric_dtype(
                    df[col]):
                logger.warning(
                    f"Skipping chart {instruction.type}: Column '{col}' is not numeric for numeric plot type. Instruction: {instruction.model_dump_json()}")
                plt.close(fig)
                return None

        if instruction.type == "bar":
            if len(instruction.columns) == 2:
                x_col, y_col = instruction.columns[0], instruction.columns[1]
                sns.barplot(x=x_col, y=y_col, data=df, ax=ax)
                chart_code_str = f"sns.barplot(x='{x_col}', y='{y_col}', data=df, ax=ax)"
            elif len(instruction.columns) == 1:
                # Count plot for a single categorical column
                sns.countplot(x=instruction.columns[0], data=df, ax=ax)
                chart_code_str = f"sns.countplot(x='{instruction.columns[0]}', data=df, ax=ax)"
            else:
                logger.warning(
                    f"Bar chart with {len(instruction.columns)} columns not fully supported without more specific instruction: {instruction.model_dump_json()}")
                plt.close(fig)
                return None
        elif instruction.type == "line":
            if len(instruction.columns) == 2:
                x_col, y_col = instruction.columns[0], instruction.columns[1]
                if pd.api.types.is_object_dtype(df[x_col]) and (
                        'date' in str(df[x_col].dtype).lower() or 'time' in str(df[x_col].dtype).lower()):
                    df_temp = df.copy()
                    df_temp[x_col] = pd.to_datetime(df_temp[x_col], errors='coerce')
                    df_sorted = df_temp.sort_values(by=x_col).dropna(subset=[x_col, y_col])
                else:
                    df_sorted = df.sort_values(by=x_col).dropna(subset=[x_col, y_col])

                if df_sorted.empty:
                    logger.warning(
                        f"Skipping line chart due to no valid data after date conversion/sorting for columns: {instruction.columns}. Instruction: {instruction.model_dump_json()}")
                    plt.close(fig)
                    return None

                sns.lineplot(x=x_col, y=y_col, data=df_sorted, ax=ax)
                chart_code_str = f"df_sorted = df.sort_values(by='{x_col}')\nsns.lineplot(x='{x_col}', y='{y_col}', data=df_sorted, ax=ax)"
            else:
                logger.warning(
                    f"Line chart with {len(instruction.columns)} columns not supported: {instruction.model_dump_json()}")
                plt.close(fig)
                return None
        elif instruction.type == "scatter":
            if len(instruction.columns) == 2:
                x_col, y_col = instruction.columns[0], instruction.columns[1]
                sns.scatterplot(x=x_col, y=y_col, data=df, ax=ax)
                chart_code_str = f"sns.scatterplot(x='{x_col}', y='{y_col}', data=df, ax=ax)"
            else:
                logger.warning(
                    f"Scatter chart requires 2 columns, got {len(instruction.columns)}: {instruction.model_dump_json()}")
                plt.close(fig)
                return None
        elif instruction.type == "histogram":
            if len(instruction.columns) == 1:
                sns.histplot(df[instruction.columns[0]], kde=True, ax=ax)
                chart_code_str = f"sns.histplot(df['{instruction.columns[0]}'], kde=True, ax=ax)"
            else:
                logger.warning(
                    f"Histogram requires 1 column, got {len(instruction.columns)}: {instruction.model_dump_json()}")
                plt.close(fig)
                return None
        elif instruction.type == "boxplot":
            if len(instruction.columns) == 1:
                sns.boxplot(y=df[instruction.columns[0]], ax=ax)
                chart_code_str = f"sns.boxplot(y=df['{instruction.columns[0]}'], ax=ax)"
            elif len(instruction.columns) == 2:
                x_col, y_col = instruction.columns[0], instruction.columns[1]
                sns.boxplot(x=x_col, y=y_col, data=df, ax=ax)
                chart_code_str = f"sns.boxplot(x='{x_col}', y='{y_col}', data=df, ax=ax)"
            else:
                logger.warning(
                    f"Boxplot with {len(instruction.columns)} columns not fully supported: {instruction.model_dump_json()}")
                plt.close(fig)
                return None
        else:
            logger.warning(f"Unsupported chart type: {instruction.type}")
            plt.close(fig)
            return None

        if instruction.title:
            ax.set_title(instruction.title)
        else:
            ax.set_title(instruction.description)

        plt.tight_layout()
        plt.savefig(output_path)
        plt.close(fig)

        logger.info(f"Chart saved to: {output_path}")
        return chart_code_str

    except Exception as e:
        logger.error(f"Error generating {instruction.type} chart for columns {instruction.columns}: {e}", exc_info=True)
        plt.close(fig)
        return None


def visualization_node(state: GraphState) -> GraphState:
    """
    Suggests and generates data visualizations based on the data profile and user instructions.
    """
    request_id = state['request_id']
    file_path = state['file_path']
    instructions = state['instructions']
    dataframe_profile = state['dataframe_profile']

    # chart_output_dir = state.get('chart_output_dir', os.path.join("local_app_data", "charts"))
    # os.makedirs(chart_output_dir, exist_ok=True)

    logger.info(f"VisualizationNode processing request: {request_id}")
    logger.info(f"DEBUG: Entering VisualizationNode. Current status: {state['status']}")

    # Initialize LLM
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        logger.error(f"GEMINI_API_KEY not found for request {request_id}. Please ensure it's set in your .env file.")
        state['status'] = "error"
        state['error_message'] = "API key for Gemini not found. Please set GEMINI_API_KEY in your .env file."
        return state

    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=gemini_api_key, temperature=0.7)
    try:
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=gemini_api_key, temperature=0.7)

    except Exception as e:
        logger.error(f"Failed to initialize LLM for visualization: {e}", exc_info=True)
        state['status'] = "error"
        state['error_message'] = f"Failed to initialize LLM for visualization: {e}"
        return state

    # Load data
    try:
        df = pd.read_csv(file_path)
        if df.empty:
            raise ValueError("Uploaded CSV is empty.")
    except Exception as e:
        logger.error(f"Error loading data for visualization for request {request_id}: {e}", exc_info=True)
        state['status'] = "error"
        state['error_message'] = f"Failed to load or process CSV for visualization: {e}"
        return state

    max_retries = 3
    base_delay = 2  # seconds
    llm_raw_output_str = ""

    for attempt in range(max_retries):

        try:
            logger.info(f"Attempt {attempt + 1}/{max_retries} to invoke LLM for visualization suggestions...")
            # Step 1: Use LLM to suggest visualizations
            parser = JsonOutputParser(pydantic_object=SuggestedVisualizations)
            prompt = PromptTemplate(
                template="""
                You are an AI assistant specialized in recommending data visualizations.
                Given a dataset profile, user instructions, and available column details,
                suggest a list of relevant and insightful visualizations.
    
                For each suggestion, provide the following:
                - `type`: (e.g., 'bar', 'line', 'scatter', 'histogram', 'boxplot'). Choose common types only.
                - `columns`: A list of 1 or 2 relevant column names from the dataset to be used for the chart.
                  Ensure columns exist in the dataset and are appropriate for the chart type.
                  For 'bar' or 'line' charts showing trends over time, ensure one column is suitable for X-axis (e.g., date, category) and another for Y-axis (e.g., numerical value).
                  For 'bar' charts, if only one column is provided, assume it's for a count plot.
                  For 'scatter' charts, provide two numerical columns.
                  For 'histogram' or 'boxplot', provide one numerical column.
                - `title`: A concise title for the chart.
                - `description`: A brief explanation of what the chart aims to convey or highlight.
                - `suggested_section`: Where in a report this visual would best fit (e.g., 'Introduction', 'Sales Analysis', 'Customer Demographics', 'Conclusion').
    
                Dataset Columns and Details:
                {column_details_json}
    
                User Request/Instructions: {instructions}
    
                Aim for 2-8 insightful visualizations. Prioritize clarity and relevance to user instructions.
                Consider the data types and distribution when suggesting. For example, if a column looks like a date, suggest a time-series plot.
                Ensure column names are exact as provided in `column_details_json`.
    
                {format_instructions}
    
                Ensure your response is valid JSON.
                """,
                input_variables=["column_details_json", "instructions"],
                partial_variables={"format_instructions": parser.get_format_instructions()},
            )

            suggested_visuals: List[VisualGenerationInstruction] = []
            logger.info(f"DEBUG: Calling LLM for visualization suggestions.")

            column_details_json = json.dumps(dataframe_profile.model_dump(exclude_unset=True),
                                             indent=2)  # Use model_dump
            llm_response = llm.invoke(prompt.invoke({
                "column_details_json": column_details_json,
                "instructions": instructions
            }))
            llm_raw_output_str = llm_response.content

            stripped_str = llm_raw_output_str.strip()
            if stripped_str.startswith("```json") and stripped_str.endswith("```"):
                json_str = stripped_str[len("```json"):-len("```")].strip()
            else:
                json_str = stripped_str

            parsed_suggestions_output = SuggestedVisualizations.model_validate_json(json_str)  # Use model_validate_json
            suggested_visuals = parsed_suggestions_output.suggestions
            logger.info(f"DEBUG: LLM returned {len(suggested_visuals)} suggestions.")
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
            logger.error(f"LLM output for request {request_id} was invalid JSON or failed Pydantic validation: {e}",
                        exc_info=True)
            logger.error(f"Raw LLM Output: {llm_raw_output_str[:500]}...")
            state['status'] = "error"
            state[
                'error_message'] = f"LLM output for visualization suggestions was invalid JSON or schema: {e}. Raw LLM Output: {llm_raw_output_str[:500]}..."
            return state
        except Exception as e:
            logger.error(
                f"An unexpected error occurred during LLM call for visualization suggestion for request {request_id}: {e}",
                exc_info=True)
            state['status'] = "error"
            state['error_message'] = f"An unexpected error occurred during visualization suggestion LLM call: {e}"
            return state
    if 'suggested_visuals' not in locals():
        state['status'] = "error"
        state['error_message'] = "An unexpected failure occurred after all LLM retries."
        return state
        # Step 2: Generate charts based on suggestions
    generated_visuals_list: List[GeneratedVisual] = []
    logger.info(f"DEBUG: Starting chart generation loop. Found {len(suggested_visuals)} suggestions.")
    for i, instruction in enumerate(suggested_visuals):
        visual_id = f"chart_{request_id}_{i + 1}"
        output_filename = f"{visual_id}.png"
        output_file_path = os.path.join(CHART_OUTPUT_DIR, output_filename)

        logger.info(
            f"DEBUG: Attempting to generate chart {i + 1}: Type={instruction.type}, Columns={instruction.columns}, Description='{instruction.description}'")

        chart_code = generate_chart(df, instruction, output_file_path)

        if chart_code:
            generated_visuals_list.append(GeneratedVisual(
                visual_id=visual_id,
                type=instruction.type,
                description=instruction.description,
                file_path=output_file_path,
                suggested_section=instruction.suggested_section if instruction.suggested_section else "Analysis",
                chart_code=chart_code
            ))
            logger.info(f"DEBUG: Chart {i + 1} generated successfully: {output_file_path}")
        else:
            logger.warning(f"DEBUG: Chart {i + 1} failed to generate. Skipping.")

    state['generated_visuals'] = generated_visuals_list
    state['status'] = "visuals_generated"
    logger.info(
        f"VisualizationNode completed for request: {request_id}. Generated {len(generated_visuals_list)} visuals.")
    return state

    # except Exception as e:
    #     logger.error(f"An unexpected critical error occurred within VisualizationNode for request {request_id}: {e}",
    #                  exc_info=True)
    #     state['status'] = "error"
    #     state['error_message'] = f"A critical error occurred in visualization node: {e}"
    #     return state