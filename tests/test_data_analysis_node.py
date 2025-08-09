import pytest
import pandas as pd
import json
import os
from unittest.mock import MagicMock
from graph.state import GraphState
from src.agents.data_analysis_node import data_analysis_node
from schemas.messages import DataProfile


@pytest.fixture
def mock_graph_state():
    """Provides a default GraphState fixture for tests."""
    return GraphState(
        request_id="test_request_123",
        file_path="mock_data.csv",
        instructions="Analyze the sales data."
    )


def setup_llm_mock(mocker, content):
    """A helper function to set up the LLM mock for different test cases."""
    mock_llm_response = MagicMock()
    mock_llm_response.content = content
    # Patch the LLM where it's imported in data_analysis_node
    mock_llm = mocker.patch('src.agents.data_analysis_node.ChatGoogleGenerativeAI', autospec=True)
    mock_llm_instance = mock_llm.return_value
    mock_llm_instance.invoke.return_value = mock_llm_response

def test_data_analysis_node_success(mock_graph_state, mocker):
    """
    Tests the successful execution of the data_analysis_node.
    Mocks file reading and LLM response.
    """
    # 1. Mock pandas to return a sample DataFrame
    sample_data = {
        'id': [1, 2, 3, 4],
        'sales': [100.5, 200.0, 150.25, 300.75],
        'product': ['A', 'B', 'C', 'A']
    }
    mock_df = pd.DataFrame(sample_data)
    mocker.patch('pandas.read_csv', return_value=mock_df)

    # 2. Mock the environment variable for the API key
    mocker.patch.dict(os.environ, {'GEMINI_API_KEY': 'mock_api_key'})

    # 3. Mock the LLM's invoke method to return a valid JSON string
    llm_content = {
        "num_rows": 4,
        "num_columns": 3,
        "column_details": {},
        "key_observations": "The dataset has 4 rows and 3 columns."
    }
    setup_llm_mock(mocker, json.dumps(llm_content))

    # 4. Call the function
    updated_state = data_analysis_node(mock_graph_state)

    # 5. Assert the results
    assert updated_state['status'] == "data_profiled"
    assert 'error_message' not in updated_state
    assert isinstance(updated_state['dataframe_profile'], DataProfile)
    assert updated_state['dataframe_profile'].num_rows == 4
    assert updated_state['dataframe_profile'].num_columns == 3


@pytest.mark.parametrize("instructions, expected_status, expected_message", [
    ("Tell me a joke about dogs.", "error", "User instructions were not related to data report generation."),
    ("Who is the president of the US?", "error", "User instructions were not related to data report generation."),
])
def test_data_analysis_node_invalid_instructions_parametrized(mock_graph_state, mocker, instructions, expected_status,
                                                              expected_message):
    """
    Tests the safety guardrail with multiple invalid instruction examples
    using pytest.mark.parametrize.
    """
    mock_graph_state['instructions'] = instructions
    mocker.patch.dict(os.environ, {'GEMINI_API_KEY': 'mock_api_key'})
    mocker.patch('pandas.read_csv', return_value=pd.DataFrame({'a': [1, 2]}))

    llm_decline_message = "I am a report generator AI and do not have information on that topic. Please give instructions related to data report generation."
    setup_llm_mock(mocker, llm_decline_message)

    updated_state = data_analysis_node(mock_graph_state)

    assert updated_state['status'] == expected_status
    assert expected_message in updated_state['error_message']



def test_data_analysis_node_llm_missing_json_field(mock_graph_state, mocker):
    """
    Tests error handling when the LLM returns valid JSON but with a required
    field (e.g., 'key_observations') missing.
    """
    mocker.patch.dict(os.environ, {'GEMINI_API_KEY': 'mock_api_key'})
    mocker.patch('pandas.read_csv', return_value=pd.DataFrame({'a': [1, 2]}))

    # Mock LLM to return valid JSON but with a missing required field
    llm_content = {
        "num_rows": 2,
        "num_columns": 1,
        "column_details": {"a": {"type": "int64"}}
        # 'key_observations' is missing
    }
    setup_llm_mock(mocker, json.dumps(llm_content))

    updated_state = data_analysis_node(mock_graph_state)

    assert updated_state['status'] == "error"
    # The assertion is updated to match the actual error message
    assert "1 validation error for DataFrameProfileOutput" in updated_state['error_message']


# -----------------------------------------------------------------------------
# Test for a CSV with only non-numeric columns
# -----------------------------------------------------------------------------
def test_data_analysis_node_non_numeric_only_csv(mock_graph_state, mocker):
    """
    Tests that the node correctly profiles a dataset containing only
    non-numeric columns.
    """
    sample_data = {
        'product': ['A', 'B', 'C', 'A'],
        'category': ['X', 'Y', 'X', 'Z']
    }
    mock_df = pd.DataFrame(sample_data)
    mocker.patch('pandas.read_csv', return_value=mock_df)
    mocker.patch.dict(os.environ, {'GEMINI_API_KEY': 'mock_api_key'})

    llm_content = {
        "num_rows": 4,
        "num_columns": 2,
        "column_details": {},
        "key_observations": "Dataset contains two categorical columns: 'product' and 'category'."
    }
    setup_llm_mock(mocker, json.dumps(llm_content))

    updated_state = data_analysis_node(mock_graph_state)

    assert updated_state['status'] == "data_profiled"
    assert updated_state['dataframe_profile'].num_rows == 4
    assert updated_state['dataframe_profile'].num_columns == 2
    # Verify that no numeric details were added to a non-numeric column
    assert "mean" not in updated_state['dataframe_profile'].column_details['product']
    assert updated_state['dataframe_profile'].column_details['product']['type'] == 'object'
    assert 'top_5_values' in updated_state['dataframe_profile'].column_details['product']


def test_data_analysis_node_missing_api_key(mock_graph_state, mocker):
    # This test remains unchanged
    mocker.patch.dict(os.environ, clear=True)
    mocker.patch('os.getenv', return_value=None)

    updated_state = data_analysis_node(mock_graph_state)

    assert updated_state['status'] == "error"
    assert "API key for Gemini not found" in updated_state['error_message']


def test_data_analysis_node_file_not_found(mock_graph_state, mocker):
    # This test remains unchanged
    mocker.patch.dict(os.environ, {'GEMINI_API_KEY': 'mock_api_key'})
    mocker.patch('pandas.read_csv', side_effect=FileNotFoundError("File not found."))

    updated_state = data_analysis_node(mock_graph_state)

    assert updated_state['status'] == "error"
    assert "Failed to load or process CSV file" in updated_state['error_message']


def test_data_analysis_node_empty_csv(mock_graph_state, mocker):
    # This test remains unchanged
    mocker.patch.dict(os.environ, {'GEMINI_API_KEY': 'mock_api_key'})
    mocker.patch('pandas.read_csv', return_value=pd.DataFrame())

    updated_state = data_analysis_node(mock_graph_state)

    assert updated_state['status'] == "error"
    assert "Uploaded CSV is empty" in updated_state['error_message']


def test_data_analysis_node_llm_invalid_json(mock_graph_state, mocker):
    # This test remains unchanged
    mocker.patch.dict(os.environ, {'GEMINI_API_KEY': 'mock_api_key'})
    mocker.patch('pandas.read_csv', return_value=pd.DataFrame({'a': [1, 2]}))

    setup_llm_mock(mocker, "this is not valid json")

    updated_state = data_analysis_node(mock_graph_state)

    assert updated_state['status'] == "error"
    assert "LLM output was invalid JSON or malformed" in updated_state['error_message']
