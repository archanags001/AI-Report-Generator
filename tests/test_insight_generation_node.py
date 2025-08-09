import pytest
import os
import json
from unittest.mock import MagicMock
from langchain_core.messages import AIMessage
from graph.state import GraphState
from src.agents.insight_generation_node import insight_generation_node
from schemas.messages import DataProfile, GeneratedVisual, AnalysisInsight
from pydantic import ValidationError

@pytest.fixture
def mock_graph_state_for_insights():
    """
    Provides a mock GraphState with a valid data profile and generated visuals,
    simulating a successful run of previous nodes.
    """
    mock_data_profile = DataProfile(
        num_rows=100,
        num_columns=5,
        column_details={
            "sales": {"type": "float64", "unique_values_count": 90, "missing_values_percentage": "0.00%"},
            "region": {"type": "object", "unique_values_count": 4, "missing_values_percentage": "0.00%"}
        },
        key_observations="Sales data shows regional variations."
    )
    mock_visuals = [
        GeneratedVisual(
            visual_id="chart_1",
            type="bar_chart",
            file_path="path/to/chart_1.png",
            description="Bar chart showing sales by region.",
            code="mock_code_1",
            suggested_section="Key Findings"
        )
    ]
    return GraphState(
        request_id="insight_test_1",
        instructions="Generate insights on sales trends.",
        dataframe_profile=mock_data_profile,
        generated_visuals=mock_visuals,
        status="initial"
    )

def setup_llm_mock(mocker, content):
    """
    A robust helper function that mocks the entire LLM prompt-response chain.
    """
    wrapped_content = f"```json\n{json.dumps(content)}\n```"
    mock_llm_response = AIMessage(content=wrapped_content)
    mock_llm_class = mocker.patch('src.agents.insight_generation_node.ChatGoogleGenerativeAI', autospec=True)
    mock_llm_instance = mock_llm_class.return_value
    mock_llm_instance.invoke.return_value = mock_llm_response

def test_insight_generation_node_success(mock_graph_state_for_insights, mocker):
    """Tests the successful execution of the insight_generation_node."""
    mocker.patch.dict(os.environ, {'GEMINI_API_KEY': 'mock_api_key'})
    # FIX: Corrected field name from 'summary' to 'narrative'
    mock_insights = [
        {"insight_id": "insight_1", "title": "Sales by Region", "narrative": "North America has the highest sales.", "suggested_section": "Key Findings", "related_visual_ids": ["chart_1"]},
        {"insight_id": "insight_2", "title": "Regional Consistency", "narrative": "Sales are consistent across other regions.", "suggested_section": "Key Findings", "related_visual_ids": []}
    ]
    llm_content = {"insights": mock_insights}
    setup_llm_mock(mocker, llm_content)
    updated_state = insight_generation_node(mock_graph_state_for_insights)
    assert updated_state['status'] == "insights_generated"
    assert len(updated_state['analysis_insights']) == 2
    assert isinstance(updated_state['analysis_insights'][0], AnalysisInsight)
    assert updated_state['analysis_insights'][0].title == "Sales by Region"


def test_insight_generation_node_no_inputs(mocker):
    """
    Tests that the node correctly handles an empty state by returning an error.
    """
    mocker.patch.dict(os.environ, {'GEMINI_API_KEY': 'mock_api_key'})
    empty_state = GraphState(request_id="empty_test", instructions="Summarize the data.", status="initial")

    # Mock LLM output, but the node should fail before this due to missing inputs
    llm_content = {"insights": []}
    setup_llm_mock(mocker, llm_content)
    updated_state = insight_generation_node(empty_state)

    # The node should correctly return an 'error' status because key inputs are missing.
    assert updated_state['status'] == 'error'
    assert "Cannot generate insights" in updated_state['error_message']


def test_insight_generation_node_empty_insights_list(mock_graph_state_for_insights, mocker):
    """
    Tests that the node correctly handles an empty list of insights from the LLM by returning an error.
    """
    mocker.patch.dict(os.environ, {'GEMINI_API_KEY': 'mock_api_key'})
    llm_content = {"insights": []}
    setup_llm_mock(mocker, llm_content)
    updated_state = insight_generation_node(mock_graph_state_for_insights)

    # The node should correctly return an 'error' status because no insights were generated.
    assert updated_state['status'] == "error"
    assert "no insights were generated" in updated_state['error_message'].lower()


def test_insight_generation_node_missing_api_key(mock_graph_state_for_insights, mocker):
    """Tests the function's behavior when the GEMINI_API_KEY is not set."""
    mocker.patch.dict(os.environ, clear=True)
    mocker.patch('os.getenv', return_value=None)
    updated_state = insight_generation_node(mock_graph_state_for_insights)
    assert updated_state['status'] == "error"
    assert "API key for Gemini not found" in updated_state['error_message']

def test_insight_generation_node_llm_invalid_json(mock_graph_state_for_insights, mocker):
    """Tests error handling for invalid JSON from the LLM."""
    mocker.patch.dict(os.environ, {'GEMINI_API_KEY': 'mock_api_key'})
    setup_llm_mock(mocker, "this is not valid json")
    updated_state = insight_generation_node(mock_graph_state_for_insights)
    assert updated_state['status'] == "error"
    assert "LLM output for insights was invalid JSON or schema" in updated_state['error_message']

def test_insight_generation_node_llm_missing_fields(mock_graph_state_for_insights, mocker):
    """Tests operational resilience when LLM returns JSON with missing fields."""
    mocker.patch.dict(os.environ, {'GEMINI_API_KEY': 'mock_api_key'})
    llm_content = {"insights": [{"insight_id": "i1", "narrative": "Missing title.", "suggested_section": "Summary"}]}
    setup_llm_mock(mocker, llm_content)
    updated_state = insight_generation_node(mock_graph_state_for_insights)
    assert updated_state['status'] == "error"
    assert "validation error for GeneratedInsightsOutput" in updated_state['error_message']




