import logging
import pandas as pd
import json
import os
from typing import Dict, Any, Optional
import numpy as np
from dotenv import load_dotenv
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
from graph.state import GraphState
from schemas.messages import DataProfile
load_dotenv()

logger = logging.getLogger(__name__)

# Define the Pydantic model for the expected LLM output for data profiling
class DataFrameProfileOutput(BaseModel):
    num_rows: int = Field(description="Number of rows in the dataset.")
    num_columns: int = Field(description="Number of columns in the dataset.")
    column_details: Dict[str, Dict[str, Any]] = Field(
        description="Dictionary of column names to their details (e.g., 'type', 'unique_values', 'missing_values_count', 'mean', 'std', 'min', 'max').")
    key_observations: str = Field(
        description="Key observations about the dataset's structure, quality, and potential issues (e.g., missing values, outliers, data types that need conversion).")


def data_analysis_node(state: GraphState) -> GraphState:
    """
    Performs initial data profiling and analysis based on the uploaded CSV.
    """
    request_id = state['request_id']
    file_path = state['file_path']
    instructions = state['instructions']

    logger.info(f"DataAnalysisNode processing request: {request_id}")

    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        logger.error(f"GEMINI_API_KEY not found for request {request_id}. Please ensure it's set in your .env file.")
        state['status'] = "error"
        state['error_message'] = "API key for Gemini not found. Please set GEMINI_API_KEY in your .env file."
        return state

    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=gemini_api_key, temperature=0.7)

    try:
        df = pd.read_csv(file_path)
        if df.empty:
            raise ValueError("Uploaded CSV is empty.")
    except Exception as e:
        logger.error(f"Error loading data for request {request_id}: {e}", exc_info=True)
        state['status'] = "error"
        state['error_message'] = f"Failed to load or process CSV file: {e}"
        return state

    profile_data = {
        "num_rows": len(df),
        "num_columns": len(df.columns),
        "column_details": {},
        "key_observations": ""
    }

    for col in df.columns:
        col_type = str(df[col].dtype)

        # Convert to standard Python int
        unique_values = int(df[col].nunique())
        missing_values_count = int(df[col].isnull().sum())

        detail: Dict[str, Any] = {
            "type": col_type,
            "unique_values_count": unique_values,
            "missing_values_count": missing_values_count,
            "missing_values_percentage": f"{(missing_values_count / len(df) * 100):.2f}%"
        }

        if pd.api.types.is_numeric_dtype(df[col]):
            # Convert to standard Python float/int, handling NaN values
            mean_val = df[col].mean()
            detail["mean"] = float(mean_val) if pd.notna(mean_val) else None

            std_val = df[col].std()
            detail["std"] = float(std_val) if pd.notna(std_val) else None

            min_val = df[col].min()
            if pd.notna(min_val):
                detail["min"] = float(min_val) if isinstance(min_val, (np.floating, float)) else int(min_val)
            else:
                detail["min"] = None

            max_val = df[col].max()
            if pd.notna(max_val):
                detail["max"] = float(max_val) if isinstance(max_val, (np.floating, float)) else int(max_val)
            else:
                detail["max"] = None

            # Convert quantiles to standard Python floats
            quantiles_dict = df[col].quantile([0.25, 0.5, 0.75]).to_dict()
            detail["quantiles"] = {k: float(v) if pd.notna(v) else None for k, v in quantiles_dict.items()}

        elif pd.api.types.is_string_dtype(df[col]) or pd.api.types.is_object_dtype(df[col]):
            # Convert values in top_5_values to native int
            top_5_values_dict = df[col].value_counts().nlargest(5).to_dict()
            detail["top_5_values"] = {k: int(v) for k, v in top_5_values_dict.items()}

        profile_data["column_details"][col] = detail

    parser = JsonOutputParser(pydantic_object=DataFrameProfileOutput)
    prompt = PromptTemplate(
        template="""
        You are an AI assistant specialized in quickly analyzing data profiles.
        Given the following dataset profile, summarize key observations, potential data quality issues,
        and suggest initial steps for cleaning or preparing the data.
        Focus on identifying missing values, outliers, incorrect data types, or any inconsistencies.
        

        Dataset Profile:
        {profile_data}

        User Request/Instructions: {instructions}

        {format_instructions}

        Ensure your response is valid JSON.
        """,
        input_variables=["profile_data", "instructions"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )

    try:
        # profile_data_str is now guaranteed to be JSON serializable
        profile_data_str = json.dumps(profile_data, indent=2)

        llm_response = llm.invoke(prompt.invoke({
            "profile_data": profile_data_str,
            "instructions": instructions
        }))
        llm_raw_output_str = llm_response.content
        stripped_str = llm_raw_output_str.strip()
        if stripped_str.startswith("```json") and stripped_str.endswith("```"):
            json_str = stripped_str[len("```json"):-len("```")].strip()
        else:
            json_str = stripped_str

        parsed_profile_output = DataFrameProfileOutput.parse_obj(json.loads(json_str))

        # Update profile_data with LLM's key_observations
        profile_data["key_observations"] = parsed_profile_output.key_observations

        # Update the state with the DataProfile Pydantic model
        state['dataframe_profile'] = DataProfile(**profile_data)
        state['status'] = "data_profiled"
        logger.info(f"DataAnalysisNode completed for request: {request_id}")
        return state

    except json.JSONDecodeError as e:
        logger.error(f"Error parsing LLM JSON in DataAnalysisNode for request {request_id}: {e}", exc_info=True)
        state['status'] = "error"
        state[
            'error_message'] = f"LLM output for data profile was invalid JSON: {e}. Raw LLM Output: {llm_raw_output_str[:500]}..."  # Log part of raw output for debugging
        return state
    except Exception as e:
        logger.error(f"An unexpected error occurred in DataAnalysisNode for request {request_id}: {e}", exc_info=True)
        state['status'] = "error"
        state['error_message'] = f"An unexpected error occurred during data analysis: {e}"
        return state