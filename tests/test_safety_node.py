import pytest
import os
import json
from unittest.mock import patch, MagicMock
from requests.exceptions import RequestException
from pydantic import ValidationError
from langchain_core.messages import AIMessage

from src.agents.safety_node import safety_check_node, SafetyCheckResult
from schemas.messages import ReportSectionsDraft, DataProfile
from graph.state import GraphState

# Mock environment variables to ensure the LLM initialization doesn't fail
@pytest.fixture(autouse=True)
def mock_env_vars():
    with patch.dict(os.environ, {"GEMINI_API_KEY": "mock_api_key"}):
        yield

@pytest.fixture
def initial_state():
    """
    Fixture to create a valid initial state for testing the safety node.
    """
    mock_report_draft = ReportSectionsDraft(
        introduction_text="This is a safe and accurate report.",
        analysis_narratives=["Finding 1:- The data shows a clear trend."],
        key_takeaways_bullet_points=["Key takeaway one."],
        conclusion_text="In conclusion, the data is great.",
        dataset_title="Mock Dataset",
        figure_id_map={"[FIGURE 1]": "visual_1"},
        clarification_questions=[]
    )
    mock_dataframe_profile = DataProfile(
        num_rows=100,
        num_columns=5,
        column_details={},
        key_observations="No issues found."
    )
    return GraphState(
        request_id="test_safety",
        file_path="/mock/path/data.csv",
        instructions="Create a report on the mock data.",
        report_sections_draft=mock_report_draft,
        dataframe_profile=mock_dataframe_profile,
        status="report_drafted",
        error_message=None
    )

@pytest.fixture
def mock_llm_with_response():
    """
    A reusable fixture to mock the LLM's ChatGoogleGenerativeAI class.
    This allows us to configure the return value of the LLM's invoke() method
    for each test case, reducing code duplication.
    """
    with patch('src.agents.safety_node.ChatGoogleGenerativeAI') as mock_llm_class:
        mock_llm_instance = MagicMock()
        mock_llm_class.return_value = mock_llm_instance
        yield mock_llm_instance

# --- Test Cases for safety_check_node ---

@patch('src.agents.safety_node.ChatGoogleGenerativeAI')
def test_safety_check_node_success(mock_llm, initial_state):
    """
    Tests the scenario where the LLM returns a successful safety check.
    """
    mock_llm_instance = MagicMock()
    # Correctly mock the LLM to return a langchain AIMessage object
    mock_llm_instance.invoke.return_value = AIMessage(content=json.dumps({
        "is_safe": True,
        "is_accurate": True,
        "reasoning": "The report is safe and accurate."
    }))
    mock_llm.return_value = mock_llm_instance

    result_state = safety_check_node(initial_state)

    assert result_state['status'] == "safety_checked"
    assert result_state['error_message'] is None
    mock_llm_instance.invoke.assert_called_once()


@patch('src.agents.safety_node.ChatGoogleGenerativeAI')
def test_safety_check_node_failed_safety(mock_llm, initial_state):
    """
    Tests the scenario where the LLM fails the safety check.
    """
    mock_llm_instance = MagicMock()
    # Correctly mock the LLM to return a langchain AIMessage object
    mock_llm_instance.invoke.return_value = AIMessage(content=json.dumps({
        "is_safe": False,
        "is_accurate": True,
        "reasoning": "The report contains harmful language."
    }))
    mock_llm.return_value = mock_llm_instance

    result_state = safety_check_node(initial_state)

    assert result_state['status'] == "error"
    assert "Safety check failed" in result_state['error_message']
    mock_llm_instance.invoke.assert_called_once()


@patch('src.agents.safety_node.ChatGoogleGenerativeAI')
def test_safety_check_node_failed_accuracy(mock_llm, initial_state):
    """
    Tests the scenario where the LLM fails the accuracy check.
    """
    mock_llm_instance = MagicMock()
    # Correctly mock the LLM to return a langchain AIMessage object
    mock_llm_instance.invoke.return_value = AIMessage(content=json.dumps({
        "is_safe": True,
        "is_accurate": False,
        "reasoning": "The report's conclusion is not supported by the data."
    }))
    mock_llm.return_value = mock_llm_instance

    result_state = safety_check_node(initial_state)

    assert result_state['status'] == "error"
    assert "Accuracy check failed" in result_state['error_message']
    mock_llm_instance.invoke.assert_called_once()


def test_safety_check_node_invalid_json(mock_llm_with_response, initial_state):
    """Tests the scenario where the LLM returns invalid JSON, leading to a parsing error."""
    mock_response_content = '{"is_safe": true, "is_accurate": true, "reasoning": "The JSON is invalid"'
    mock_llm_with_response.invoke.return_value = MagicMock(content=mock_response_content)

    result_state = safety_check_node(initial_state)

    assert result_state.get('status') == "error"
    assert "Report validation failed due to an internal error" in result_state.get('error_message')


@patch('src.agents.safety_node.ChatGoogleGenerativeAI')
def test_safety_check_node_retry_then_success(mock_llm, initial_state):
    """
    Tests that the node retries on a network error and succeeds on a subsequent attempt.
    """
    mock_llm_instance = MagicMock()
    # First two calls raise an exception, third call returns success
    mock_llm_instance.invoke.side_effect = [
        RequestException("Mock network error"),
        RequestException("Another mock network error"),
        AIMessage(content=json.dumps({"is_safe": True, "is_accurate": True, "reasoning": "All good."}))
    ]
    mock_llm.return_value = mock_llm_instance

    result_state = safety_check_node(initial_state)

    assert result_state['status'] == "safety_checked"
    assert result_state['error_message'] is None
    # Ensure three calls were made
    assert mock_llm_instance.invoke.call_count == 3


@patch('src.agents.safety_node.ChatGoogleGenerativeAI')
def test_safety_check_node_max_retries_fail(mock_llm, initial_state):
    """
    Tests that the node fails after reaching the max number of retries for a network error.
    """
    mock_llm_instance = MagicMock()
    # All three calls raise an exception
    mock_llm_instance.invoke.side_effect = RequestException("Persistent mock network error")
    mock_llm.return_value = mock_llm_instance

    result_state = safety_check_node(initial_state)

    assert result_state['status'] == "error"
    assert "Failed to get a response from the LLM after 3 attempts" in result_state['error_message']
    # Ensure three calls were made
    assert mock_llm_instance.invoke.call_count == 3


def test_safety_check_node_missing_input(initial_state):
    """
    Tests that the node handles missing a required input gracefully without crashing.
    """
    # Create a state with a missing report draft
    initial_state_missing_draft = initial_state.copy()
    initial_state_missing_draft['report_sections_draft'] = None

    result_state = safety_check_node(initial_state_missing_draft)

    # The node should return the state unchanged, with no error message,
    # as it should log a warning and skip the check.
    assert result_state == initial_state_missing_draft
    assert result_state['status'] == "report_drafted" # Status should not change
    assert result_state['error_message'] is None



