import pytest
import os
import json
from unittest.mock import MagicMock
from langchain_core.messages import AIMessage
from graph.state import GraphState
from src.agents.report_drafting_node import report_drafting_node
from schemas.messages import DataProfile, GeneratedVisual, AnalysisInsight, ReportSectionsDraft


# --- Fixtures for mock data ---

@pytest.fixture
def mock_graph_state_for_report():
    """
    Provides a mock GraphState with all required inputs for the report drafting node.
    """
    mock_data_profile = DataProfile(
        num_rows=100,
        num_columns=5,
        column_details={"sales": {"type": "float64"}, "region": {"type": "object"}},
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
    mock_insights = [
        AnalysisInsight(
            insight_id="insight_1",
            title="Regional Sales Performance",
            narrative="North America has the highest sales.",
            suggested_section="Key Findings",
            supporting_visual_ids=["chart_1"]
        )
    ]
    return GraphState(
        request_id="report_test_1",
        instructions="Generate a report on sales performance.",
        dataframe_profile=mock_data_profile,
        generated_visuals=mock_visuals,
        analysis_insights=mock_insights,
        status="insights_generated",
        dataset_name="Sales Data Q1"
    )


def setup_llm_mock(mocker, content):
    """Mocks the LLM to return a response with the given content."""
    wrapped_content = f"```json\n{json.dumps(content)}\n```"
    mock_llm_response = AIMessage(content=wrapped_content)
    mock_llm_class = mocker.patch('src.agents.report_drafting_node.ChatGoogleGenerativeAI', autospec=True)
    mock_llm_instance = mock_llm_class.return_value
    mock_llm_instance.invoke.return_value = mock_llm_response


# --- Test Cases ---

def test_report_drafting_node_success(mock_graph_state_for_report, mocker):
    """
    Tests the successful generation of a report draft.
    """
    mocker.patch.dict(os.environ, {'GEMINI_API_KEY': 'mock_api_key'})

    # Mock LLM to return a valid ReportSectionsDraft object
    llm_content = {
        "introduction_text": "This report analyzes sales data for Q1.",
        "analysis_narratives": [
            "Regional Sales Performance:- North America showed the strongest sales. This is supported by the regional breakdown as seen in [FIGURE 1]."],
        "key_takeaways_bullet_points": ["North America leads in sales."],
        "conclusion_text": "In conclusion, regional performance varies significantly.",
        "dataset_title": "Q1 Sales Analysis Report",
        "figure_id_map": {"[FIGURE 1]": "chart_1"},
        "clarification_questions": []
    }
    setup_llm_mock(mocker, llm_content)

    updated_state = report_drafting_node(mock_graph_state_for_report)

    assert updated_state['status'] == "report_drafted"
    assert isinstance(updated_state['report_sections_draft'], ReportSectionsDraft)
    assert updated_state['report_sections_draft'].dataset_title == "Q1 Sales Analysis Report"
    assert "[FIGURE 1]" in updated_state['report_sections_draft'].analysis_narratives[0]


def test_report_drafting_node_missing_api_key(mock_graph_state_for_report, mocker):
    """Tests the function's behavior when the GEMINI_API_KEY is not set."""
    mocker.patch.dict(os.environ, clear=True)
    mocker.patch('os.getenv', return_value=None)

    updated_state = report_drafting_node(mock_graph_state_for_report)

    assert updated_state['status'] == "error"
    assert "API key for Gemini not found" in updated_state['error_message']


def test_report_drafting_node_llm_invalid_json(mock_graph_state_for_report, mocker):
    """Tests error handling for invalid JSON from the LLM."""
    mocker.patch.dict(os.environ, {'GEMINI_API_KEY': 'mock_api_key'})

    # Mock LLM to return a non-JSON string
    mock_llm_class = mocker.patch('src.agents.report_drafting_node.ChatGoogleGenerativeAI', autospec=True)
    mock_llm_instance = mock_llm_class.return_value
    mock_llm_instance.invoke.return_value = AIMessage(content="this is not valid json")

    updated_state = report_drafting_node(mock_graph_state_for_report)

    assert updated_state['status'] == "error"
    assert "LLM output for report draft was invalid JSON or schema" in updated_state['error_message']


def test_report_drafting_node_llm_missing_fields(mock_graph_state_for_report, mocker):
    """Tests operational resilience when LLM returns JSON with missing fields."""
    mocker.patch.dict(os.environ, {'GEMINI_API_KEY': 'mock_api_key'})

    # Mock LLM to return valid JSON but with a missing required field (e.g., 'introduction_text')
    llm_content = {
        "analysis_narratives": ["Regional Sales Performance:- North America showed the strongest sales."],
        "key_takeaways_bullet_points": ["North America leads in sales."],
        "conclusion_text": "In conclusion, regional performance varies significantly.",
        "dataset_title": "Q1 Sales Analysis Report",
        "figure_id_map": {},
        "clarification_questions": []
    }
    setup_llm_mock(mocker, llm_content)

    updated_state = report_drafting_node(mock_graph_state_for_report)

    assert updated_state['status'] == "error"
    assert "validation error for ReportSectionsDraft" in updated_state['error_message']

def test_report_drafting_node_empty_inputs(mocker):
    """Tests that the node correctly handles an empty state with no inputs by returning an error."""
    mocker.patch.dict(os.environ, {'GEMINI_API_KEY': 'mock_api_key'})

    empty_state = GraphState(request_id="empty_report_test", instructions="Draft a report.",
                             status="insights_generated")

    # Mock LLM to return a valid but empty-context report. The node itself should still fail
    # because the input lists are missing, not because of the LLM output.
    llm_content = {
        "introduction_text": "This report lacks data, insights, or visuals.",
        "analysis_narratives": [],
        "key_takeaways_bullet_points": ["No data available for analysis."],
        "conclusion_text": "Conclusion is pending.",
        "dataset_title": "Empty Report",
        "figure_id_map": {},
        "clarification_questions": ["What data should be analyzed?"]
    }
    setup_llm_mock(mocker, llm_content)

    updated_state = report_drafting_node(empty_state)

    assert updated_state['status'] == "error"
    assert "Cannot draft report: Missing data profile, insights, or visuals" in updated_state['error_message']