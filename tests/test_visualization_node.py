import pytest
import os
import pandas as pd
import json
from unittest.mock import MagicMock
from langchain_core.messages import AIMessage
from graph.state import GraphState
from src.agents.visualization_node import visualization_node, generate_chart, CHART_OUTPUT_DIR
from schemas.messages import DataProfile, VisualGenerationInstruction, GeneratedVisual
from pydantic import ValidationError


# Fixtures for mock data and setup
@pytest.fixture
def mock_dataframe():
    """Provides a mock DataFrame for testing."""
    data = {
        'sales': [100, 150, 200, 120, 180],
        'region': ['North', 'South', 'North', 'East', 'West'],
        'date': pd.to_datetime(['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04', '2023-01-05']),
        'product_category': ['A', 'B', 'A', 'C', 'B']
    }
    return pd.DataFrame(data)


@pytest.fixture
def mock_graph_state_for_visuals():
    """Provides a mock GraphState with necessary inputs."""
    mock_data_profile = DataProfile(
        num_rows=5,
        num_columns=4,
        column_details={
            'sales': {'type': 'int64', 'unique_values_count': 5, 'missing_values_percentage': '0.00%'},
            'region': {'type': 'object', 'unique_values_count': 4, 'missing_values_percentage': '0.00%'},
            'date': {'type': 'datetime64[ns]', 'unique_values_count': 5, 'missing_values_percentage': '0.00%'}
        },
        key_observations="Sales data shows regional variations."
    )
    return GraphState(
        request_id="visual_test_1",
        file_path="mock_file_path.csv",
        instructions="Generate visuals for sales trends by region.",
        dataframe_profile=mock_data_profile,
        status="initial"
    )


@pytest.fixture
def temp_chart_path():
    """Provides a temporary file path for chart saving and cleans up afterward."""
    path = os.path.join(CHART_OUTPUT_DIR, "test_chart.png")
    yield path
    if os.path.exists(path):
        os.remove(path)


# Helper function to mock the LLM response
def setup_llm_mock(mocker, content):
    """Mocks the LLM to return a response with the given content."""
    wrapped_content = f"```json\n{json.dumps(content)}\n```"
    mock_llm_response = AIMessage(content=wrapped_content)
    mock_llm_class = mocker.patch('src.agents.visualization_node.ChatGoogleGenerativeAI', autospec=True)
    mock_llm_instance = mock_llm_class.return_value
    mock_llm_instance.invoke.return_value = mock_llm_response


# --- Test Cases for visualization_node ---

def test_visualization_node_success(mock_graph_state_for_visuals, mock_dataframe, mocker):
    """
    Tests the successful execution of visualization_node.
    Mocks LLM to return valid suggestions and mocks pandas to return a valid DataFrame.
    """
    mock_suggestions_list = [
        {"type": "bar", "columns": ["region", "sales"], "title": "Sales by Region",
         "description": "Bar chart of sales by region", "suggested_section": "Sales Analysis"},
        {"type": "line", "columns": ["date", "sales"], "title": "Sales Over Time",
         "description": "Line chart of sales over time", "suggested_section": "Sales Analysis"}
    ]
    llm_content = {"suggestions": mock_suggestions_list}
    setup_llm_mock(mocker, llm_content)
    mocker.patch('pandas.read_csv', return_value=mock_dataframe)
    mocker.patch('src.agents.visualization_node.generate_chart', return_value="mock_chart_code_string")
    mocker.patch.dict(os.environ, {'GEMINI_API_KEY': 'mock_api_key'})

    updated_state = visualization_node(mock_graph_state_for_visuals)

    assert updated_state['status'] == "visuals_generated"
    assert 'generated_visuals' in updated_state
    assert len(updated_state['generated_visuals']) == 2
    assert isinstance(updated_state['generated_visuals'][0], GeneratedVisual)
    assert updated_state['generated_visuals'][0].visual_id == "chart_visual_test_1_1"
    assert updated_state['generated_visuals'][1].type == "line"


def test_visualization_node_missing_api_key(mock_graph_state_for_visuals, mocker):
    """Tests the function's behavior when the GEMINI_API_KEY is not set."""
    mocker.patch.dict(os.environ, clear=True)
    mocker.patch('os.getenv', return_value=None)

    updated_state = visualization_node(mock_graph_state_for_visuals)

    assert updated_state['status'] == "error"
    assert "API key for Gemini not found" in updated_state['error_message']


def test_visualization_node_llm_invalid_json(mock_graph_state_for_visuals, mock_dataframe, mocker):
    """Tests error handling for invalid JSON from the LLM."""
    mocker.patch.dict(os.environ, {'GEMINI_API_KEY': 'mock_api_key'})
    mocker.patch('pandas.read_csv', return_value=mock_dataframe)

    # Mock LLM to return a non-JSON string
    mock_llm_class = mocker.patch('src.agents.visualization_node.ChatGoogleGenerativeAI', autospec=True)
    mock_llm_instance = mock_llm_class.return_value
    mock_llm_instance.invoke.return_value = AIMessage(content="this is not valid json")

    updated_state = visualization_node(mock_graph_state_for_visuals)

    assert updated_state['status'] == "error"
    assert "LLM output for visualization suggestions was invalid JSON or schema" in updated_state['error_message']


# def test_visualization_node_llm_invalid_schema(mock_graph_state_for_visuals, mock_dataframe, mocker):
#     """Tests operational resilience when LLM returns JSON with a schema that doesn't match the Pydantic model."""
#     mocker.patch.dict(os.environ, {'GEMINI_API_KEY': 'mock_api_key'})
#     mocker.patch('pandas.read_csv', return_value=mock_dataframe)
#
#     # Mock LLM to return valid JSON but missing a required field (e.g., 'type')
#     llm_content = {"suggestions": [{"columns": ["region", "sales"], "title": "Sales by Region"}]}
#     setup_llm_mock(mocker, llm_content)
#
#     updated_state = visualization_node(mock_graph_state_for_visuals)
#
#     assert updated_state['status'] == "error"
#     assert "ValidationError" in updated_state['error_message']


def test_visualization_node_llm_invalid_schema(mock_graph_state_for_visuals, mock_dataframe, mocker):
    """Tests operational resilience when LLM returns JSON with a schema that doesn't match the Pydantic model."""
    mocker.patch.dict(os.environ, {'GEMINI_API_KEY': 'mock_api_key'})
    mocker.patch('pandas.read_csv', return_value=mock_dataframe)

    # Mock LLM to return valid JSON but missing a required field (e.g., 'type')
    llm_content = {"suggestions": [{"columns": ["region", "sales"], "title": "Sales by Region"}]}
    setup_llm_mock(mocker, llm_content)

    updated_state = visualization_node(mock_graph_state_for_visuals)

    assert updated_state['status'] == "error"
    assert "2 validation errors for SuggestedVisualizations" in updated_state['error_message']

def test_visualization_node_empty_dataframe(mock_graph_state_for_visuals, mocker):
    """Tests the node's behavior when the loaded DataFrame is empty."""
    mocker.patch.dict(os.environ, {'GEMINI_API_KEY': 'mock_api_key'})
    mocker.patch('pandas.read_csv', return_value=pd.DataFrame())

    updated_state = visualization_node(mock_graph_state_for_visuals)

    assert updated_state['status'] == "error"
    assert "Failed to load or process CSV for visualization: Uploaded CSV is empty" in updated_state['error_message']


# --- Test Cases for generate_chart helper function ---

def test_generate_chart_success(mock_dataframe, temp_chart_path):
    """Tests the successful generation of a chart for a valid instruction."""
    instruction = VisualGenerationInstruction(
        type="bar",
        columns=["region", "sales"],
        title="Sales by Region",
        description="Bar chart showing sales for each region.",
        suggested_section="Analysis"
    )

    chart_code = generate_chart(mock_dataframe, instruction, temp_chart_path)

    assert chart_code is not None
    assert "sns.barplot" in chart_code
    assert os.path.exists(temp_chart_path)
    assert os.path.getsize(temp_chart_path) > 0


def test_generate_chart_invalid_columns(mock_dataframe, temp_chart_path):
    """Tests that the function returns None for invalid column names."""
    instruction = VisualGenerationInstruction(
        type="bar",
        columns=["non_existent_column", "sales"],
        title="Sales by Region",
        description="Invalid columns test.",
        suggested_section="Analysis"
    )

    chart_code = generate_chart(mock_dataframe, instruction, temp_chart_path)

    assert chart_code is None
    assert not os.path.exists(temp_chart_path)


def test_generate_chart_invalid_column_type(mock_dataframe, temp_chart_path):
    """Tests that the function returns None for inappropriate column types."""
    instruction = VisualGenerationInstruction(
        type="histogram",
        columns=["region"],  # Histogram requires a numeric column
        title="Region Histogram",
        description="Invalid column type test.",
        suggested_section="Analysis"
    )

    chart_code = generate_chart(mock_dataframe, instruction, temp_chart_path)

    assert chart_code is None
    assert not os.path.exists(temp_chart_path)