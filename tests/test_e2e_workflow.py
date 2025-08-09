import pytest
import os
import pandas as pd
from unittest.mock import patch, MagicMock

# Import all necessary classes and functions
from src.graph.state import GraphState
from src.graph.builder import create_graph_workflow
from schemas.messages import ReportSectionsDraft, ReportFormat, GeneratedVisual, DataProfile, AnalysisInsight, \
    VisualGenerationInstruction
from src.agents.data_analysis_node import data_analysis_node
from src.agents.visualization_node import visualization_node
from src.agents.insight_generation_node import insight_generation_node
from src.agents.report_drafting_node import report_drafting_node
from src.agents.report_finalization_node import report_finalization_node

import json


@pytest.fixture(scope="module")
def setup_test_data(tmpdir_factory):
    """
    Creates a temporary test directory and a dummy CSV file.
    This fixture is crucial for E2E tests as it sets up a real-world file system scenario.
    """
    test_dir = tmpdir_factory.mktemp("e2e_test_data")
    csv_path = os.path.join(test_dir, "e2e_data.csv")
    report_output_dir = os.path.join(test_dir, "reports")
    chart_output_dir = os.path.join(test_dir, "charts")

    os.makedirs(report_output_dir, exist_ok=True)
    os.makedirs(chart_output_dir, exist_ok=True)

    csv_content = """date,sales,category
2023-01-01,150.50,A
2023-01-02,200.75,B
2023-01-03,125.20,A
2023-01-04,300.10,C
2023-01-05,175.90,B
"""
    with open(csv_path, 'w') as f:
        f.write(csv_content)

    yield csv_path, chart_output_dir, report_output_dir

    # Teardown: Clean up the dummy chart file if it exists
    if os.path.exists(csv_path):
        os.remove(csv_path)


# --- Test 1: Test the data_analysis_node in isolation ---
@patch('src.agents.data_analysis_node.ChatGoogleGenerativeAI', api_key='dummy_api_key')
@patch('src.agents.data_analysis_node.pd.read_csv', side_effect=pd.read_csv)
def test_data_analysis_node(mock_pd_read_csv, mock_llm, setup_test_data):
    """
    Tests that the data analysis node correctly processes the CSV and
    generates a data profile.
    """
    csv_path, _, _ = setup_test_data
    mock_llm.return_value.invoke.return_value.content = '{"num_rows": 5, "num_columns": 3, "column_details": {}, "key_observations": "Mock analysis"}'

    initial_state = GraphState(
        request_id="test_analysis",
        file_path=csv_path,
        instructions="Analyze sales data.",
        dataset_name="e2e_data"
    )

    result_state = data_analysis_node(initial_state)

    assert isinstance(result_state.get('dataframe_profile'), DataProfile)
    assert result_state['dataframe_profile'].num_rows == 5
    assert result_state['dataframe_profile'].num_columns == 3


# --- Test 2: Test the visualization_node in isolation ---
@patch('src.agents.visualization_node.ChatGoogleGenerativeAI', api_key='dummy_api_key')
def test_visualization_node(mock_llm, setup_test_data):
    """
    Tests that the visualization node correctly generates a visual instruction
    given a data profile.
    """
    csv_path, _, _ = setup_test_data
    mock_llm.return_value.invoke.return_value.content = json.dumps({
        "suggestions": [
            {"type": "bar", "columns": ["category"], "title": "Sales by Category",
             "description": "Bar chart showing sales by category.", "suggested_section": "Key Findings"}
        ]
    })

    pre_viz_state = GraphState(
        request_id="test_viz",
        file_path=csv_path,
        dataframe_profile=DataProfile(num_rows=5, num_columns=3, column_details={}, key_observations="Mock analysis"),
        instructions="Generate a chart for sales data.",
        dataset_name="e2e_data",
        status="initial"
    )

    result_state = visualization_node(pre_viz_state)

    assert len(result_state.get('generated_visuals')) == 1
    assert isinstance(result_state['generated_visuals'][0], GeneratedVisual)


@patch('src.agents.report_drafting_node.ChatGoogleGenerativeAI', api_key='dummy_api_key')
def test_report_drafting_node(mock_llm, setup_test_data):
    """
    Tests that the report drafting node correctly creates a report draft
    from a set of insights and visuals.
    """
    csv_path, chart_output_dir, report_output_dir = setup_test_data
    mock_llm.return_value.invoke.return_value.content = json.dumps({
        "introduction_text": "Mock intro.",
        "analysis_narratives": ["Mock narrative for Category C with a reference to [FIGURE 1]."],
        "key_takeaways_bullet_points": ["Mock takeaway."],
        "conclusion_text": "Mock conclusion.",
        "dataset_title": "E2E Report",
        "figure_id_map": {"[FIGURE 1]": "chart_1"},
        "clarification_questions": []
    })

    mock_visual = GeneratedVisual(
        visual_id="chart_1",
        type="bar",
        description="Mock bar chart for testing",
        file_path=os.path.join(chart_output_dir, "chart_1.png"),
        suggested_section="Key Findings"
    )

    # Added a mock dataframe_profile to the state to satisfy the node's initial check
    mock_profile = DataProfile(
        num_rows=5,
        num_columns=3,
        column_details={"sales": {"type": "float"}},
        key_observations="Sales show a clear trend."
    )

    pre_draft_state = GraphState(
        request_id="test_draft",
        file_path=csv_path,
        instructions="Draft a report.",
        dataframe_profile=mock_profile,
        generated_visuals=[mock_visual],
        analysis_insights=[AnalysisInsight(insight_id="insight_1", title="Test", narrative="Test narrative.")],
        status="insights_generated",
        dataset_name="e2e_data"
    )

    result_state = report_drafting_node(pre_draft_state)

    assert isinstance(result_state.get('report_sections_draft'), ReportSectionsDraft)
    assert result_state['report_sections_draft'].dataset_title == "E2E Report"


# --- Test 4: Test the report_finalization_node in isolation ---
@patch('src.agents.report_finalization_node.HTML')
def test_report_finalization_node_direct(mock_weasyprint_html, setup_test_data):
    """
    Tests the report_finalization_node in isolation to verify its logic.
    """
    csv_path, chart_output_dir, report_output_dir = setup_test_data
    mock_write_pdf = MagicMock()
    mock_weasyprint_html.return_value.write_pdf = mock_write_pdf

    mock_visual = GeneratedVisual(
        visual_id="chart_1",
        type="bar",
        description="Mock bar chart for testing",
        file_path=os.path.join(chart_output_dir, "chart_1.png"),
        suggested_section="Key Findings"
    )
    with open(mock_visual.file_path, "w") as f:
        f.write("mock chart content")

    mock_draft = ReportSectionsDraft(
        introduction_text="Mock intro.",
        analysis_narratives=["Mock narrative with [FIGURE 1]"],
        key_takeaways_bullet_points=["Mock takeaway."],
        conclusion_text="Mock conclusion.",
        dataset_title="E2E Report",
        figure_id_map={"[FIGURE 1]": "chart_1"},
        clarification_questions=[]
    )

    test_state = GraphState(
        request_id="isolated_test",
        file_path=csv_path,
        instructions="Isolated test.",
        dataset_name="e2e_data",
        chart_output_dir=chart_output_dir,
        report_output_dir=report_output_dir,
        status="report_drafted",
        report_sections_draft=mock_draft,
        generated_visuals=[mock_visual]
    )

    final_state = report_finalization_node(test_state)

    assert final_state['status'] == "report_finalized"
    mock_weasyprint_html.return_value.write_pdf.assert_called_once()

    os.remove(mock_visual.file_path)


# --- Test 5: End-to-end test of the full workflow ---
# NOTE: The mocks for the LLM and plt.savefig have been removed
# to allow for a true end-to-end test. This test will now use the actual LLM and
# chart generation logic.
def test_full_e2e_workflow_unmocked(setup_test_data):
    """
    Performs a full end-to-end test of the entire LangGraph workflow.
    This test now runs with the real LLM and chart generation.
    """
    csv_path, chart_output_dir, report_output_dir = setup_test_data

    # Instantiate the workflow and initial state
    workflow = create_graph_workflow()
    initial_state = {
        "request_id": "test_full_e2e",
        "file_path": csv_path,
        "instructions": "Generate a full report.",
        "dataset_name": "e2e_data",
        "chart_output_dir": chart_output_dir,
        "report_output_dir": report_output_dir
    }

    # Run the workflow
    final_state = workflow.invoke(initial_state)

    # Assertions for the final state
    assert final_state['status'] == "report_finalized"
    assert isinstance(final_state['report_sections_draft'], ReportSectionsDraft)
    # The key must exist before we can check its length.
    assert 'generated_visuals' in final_state
    # Corrected assertion to be more flexible, matching the LLM's prompt.
    assert 1 <= len(final_state['generated_visuals']) <= 3
