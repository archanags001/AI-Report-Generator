import pytest
from unittest.mock import patch, MagicMock
from schemas.messages import DataProfile, GeneratedVisual, AnalysisInsight, ReportSectionsDraft, ReportFormat
from graph.state import GraphState
from src.graph.builder import create_graph_workflow

# --- Mock data for nodes ---

MOCK_DATA_PROFILE = DataProfile(
    num_rows=100,
    num_columns=5,
    column_details={"sales": {"type": "float64"}, "region": {"type": "object"}},
    key_observations="Sales data shows regional variations."
)

MOCK_VISUALS = [
    GeneratedVisual(
        visual_id="chart_1",
        type="bar_chart",
        file_path="path/to/chart_1.png",
        description="Bar chart showing sales by region.",
        code="mock_code_1",
        suggested_section="Key Findings"
    )
]

MOCK_INSIGHTS = [
    AnalysisInsight(
        insight_id="insight_1",
        title="Regional Sales Performance",
        narrative="North America has the highest sales.",
        suggested_section="Key Findings",
        supporting_visual_ids=["chart_1"]
    )
]

MOCK_REPORT_DRAFT = ReportSectionsDraft(
    introduction_text="This is a mock introduction.",
    analysis_narratives=["Regional Sales Performance:- The key finding is here, as shown in [FIGURE 1]."],
    key_takeaways_bullet_points=["Key takeaway 1", "Key takeaway 2"],
    conclusion_text="This is a mock conclusion.",
    dataset_title="Mock Data Analysis",
    figure_id_map={"[FIGURE 1]": "chart_1"},
    clarification_questions=[]
)

MOCK_FINAL_REPORT = ReportFormat(
    content="# Final Report Content",
    format_type="markdown",
    pdf_file_path="/mock/path/report.pdf"
)

# --- Test Cases ---

@patch('src.graph.builder.report_finalization_node')
@patch('src.graph.builder.report_drafting_node')
@patch('src.graph.builder.insight_generation_node')
@patch('src.graph.builder.visualization_node')
@patch('src.graph.builder.data_analysis_node')
def test_full_workflow_happy_path(mock_data_analysis, mock_visualization, mock_insight_generation, mock_report_drafting, mock_report_finalization):
    """
    Tests the successful execution of the entire workflow from start to end.
    """
    # FIX: Each mock now returns only the data it's responsible for, as a dictionary,
    # and LangGraph handles the merging into the state.
    mock_data_analysis.return_value = {'dataframe_profile': MOCK_DATA_PROFILE, 'status': "data_analyzed", 'file_path': 'dummy/path'}
    mock_visualization.return_value = {'generated_visuals': MOCK_VISUALS, 'status': "visuals_generated"}
    mock_insight_generation.return_value = {'analysis_insights': MOCK_INSIGHTS, 'status': "insights_generated"}
    mock_report_drafting.return_value = {'report_sections_draft': MOCK_REPORT_DRAFT, 'status': "report_drafted"}
    mock_report_finalization.return_value = {'final_report': MOCK_FINAL_REPORT, 'status': "report_finalized"}

    app = create_graph_workflow()
    initial_state = GraphState(request_id="full_run_test")
    final_state = app.invoke(initial_state)

    # Assert that all nodes were called in the correct order
    mock_data_analysis.assert_called_once()
    mock_visualization.assert_called_once()
    mock_insight_generation.assert_called_once()
    mock_report_drafting.assert_called_once()
    mock_report_finalization.assert_called_once()

    # Assert that the final state contains all the expected data
    assert final_state.get('dataframe_profile') == MOCK_DATA_PROFILE
    assert final_state.get('generated_visuals') == MOCK_VISUALS
    assert final_state.get('analysis_insights') == MOCK_INSIGHTS
    assert final_state.get('final_report') == MOCK_FINAL_REPORT


@patch('src.graph.builder.report_finalization_node')
@patch('src.graph.builder.report_drafting_node')
@patch('src.graph.builder.insight_generation_node')
@patch('src.graph.builder.visualization_node')
@patch('src.graph.builder.data_analysis_node')
def test_conditional_end_path(mock_data_analysis, mock_visualization, mock_insight_generation, mock_report_drafting, mock_report_finalization):
    """
    Tests that the graph correctly ends if the data analysis node
    returns a dataframe profile with a low row count.
    """
    low_data_profile = DataProfile(num_rows=2, num_columns=5, column_details={}, key_observations="Not enough data.")
    # FIX: Ensure the mock return value has a file_path to satisfy the `data_analysis_node` logic
    mock_data_analysis.return_value = {'dataframe_profile': low_data_profile, 'status': "data_analyzed", 'file_path': 'dummy/path'}

    app = create_graph_workflow()
    initial_state = GraphState(request_id="low_data_test")
    final_state = app.invoke(initial_state)

    # Assert that only the first node was called
    mock_data_analysis.assert_called_once()
    mock_visualization.assert_not_called()
    mock_insight_generation.assert_not_called()
    mock_report_drafting.assert_not_called()
    mock_report_finalization.assert_not_called()

    # Assert that the final state is the result of the first node
    assert final_state.get('dataframe_profile') == low_data_profile


@patch('src.graph.builder.report_finalization_node')
@patch('src.graph.builder.report_drafting_node')
@patch('src.graph.builder.insight_generation_node')
@patch('src.graph.builder.visualization_node')
@patch('src.graph.builder.data_analysis_node')
def test_missing_profile_end_path(mock_data_analysis, mock_visualization, mock_insight_generation, mock_report_drafting, mock_report_finalization):
    """
    Tests that the graph correctly handles a state with no dataframe_profile.
    """
    # FIX: Ensure the mock return value has a file_path to satisfy the `data_analysis_node` logic
    mock_data_analysis.return_value = {'dataframe_profile': None, 'status': "error", 'file_path': 'dummy/path'}

    app = create_graph_workflow()
    initial_state = GraphState(request_id="missing_profile_test")
    final_state = app.invoke(initial_state)

    # Assert that only the first node was called
    mock_data_analysis.assert_called_once()
    mock_visualization.assert_not_called()
    mock_insight_generation.assert_not_called()
    mock_report_drafting.assert_not_called()
    mock_report_finalization.assert_not_called()

    # Assert the state remains as the result of the first node
    assert final_state.get('dataframe_profile') is None
    assert final_state.get('status') == "error"