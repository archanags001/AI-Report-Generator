import pytest
import os
import re
from unittest.mock import MagicMock, mock_open, patch
from graph.state import GraphState
from src.agents.report_finalization_node import report_finalization_node
from schemas.messages import ReportSectionsDraft, GeneratedVisual, ReportFormat


# --- Fixtures for mock data ---

@pytest.fixture
def mock_graph_state_for_finalization():
    """
    Provides a mock GraphState with all required inputs for the finalization node.
    """
    mock_visual = GeneratedVisual(
        visual_id="chart_1",
        type="bar_chart",
        file_path="local_app_data/charts/chart_1.png",
        description="Bar chart showing sales by region.",
        code="mock_code_1",
        suggested_section="Key Findings"
    )
    mock_draft = ReportSectionsDraft(
        introduction_text="This is a mock introduction.",
        analysis_narratives=["Regional Sales Performance:- The key finding is here, as shown in [FIGURE 1]."],
        key_takeaways_bullet_points=["Key takeaway 1", "Key takeaway 2"],
        conclusion_text="This is a mock conclusion.",
        dataset_title="Mock Data Analysis",
        figure_id_map={"[FIGURE 1]": "chart_1"},
        clarification_questions=[]
    )
    return GraphState(
        request_id="finalization_test_1",
        instructions="Finalize the report.",
        report_sections_draft=mock_draft,
        generated_visuals=[mock_visual],
        status="report_drafted",
        dataset_name="Mock Data"
    )


# --- Test Cases ---

def test_report_finalization_node_success(mock_graph_state_for_finalization, mocker):
    """Tests the successful finalization of a report into Markdown and PDF."""

    # Mock file I/O to prevent actual file creation
    mock_open_func = mock_open()
    mocker.patch('builtins.open', mock_open_func)
    mocker.patch('os.path.exists', return_value=True)
    mocker.patch('os.path.abspath', return_value="/mock/path/chart_1.png")

    # Mock weasyprint to prevent PDF generation
    mocker.patch('src.agents.report_finalization_node.HTML')

    updated_state = report_finalization_node(mock_graph_state_for_finalization)

    # Assertions for the final state
    assert updated_state['status'] == "report_finalized"
    assert isinstance(updated_state['final_report'], ReportFormat)

    # Assertions for the generated Markdown content
    final_content = updated_state['final_report'].content
    assert "# Data Analysis Report: Mock Data Analysis" in final_content
    assert "This is a mock introduction." in final_content
    assert "Figure 1" in final_content
    assert "![Bar chart showing sales by region.](file:////mock/path/chart_1.png)" in final_content
    assert "- Key takeaway 1" in final_content
    assert "This is a mock conclusion." in final_content

    # Assertions for file creation calls
    mock_open_func.assert_called_once()
    assert mock_open_func.call_args[0][0].endswith(".md")

    # Assert PDF generation was attempted
    assert updated_state['final_report'].pdf_file_path is not None
    assert updated_state['final_report'].pdf_file_path.endswith(".pdf")


def test_report_finalization_node_missing_draft(mocker):
    """Tests the node's behavior when the report sections draft is missing."""
    empty_state = GraphState(request_id="finalization_test_2", status="report_drafted")
    updated_state = report_finalization_node(empty_state)
    assert updated_state['status'] == "error"
    assert "Cannot finalize report: Report sections draft is missing." in updated_state['error_message']


def test_report_finalization_node_missing_visual_file(mock_graph_state_for_finalization, mocker):
    """
    Tests handling of a scenario where a visual is referenced but the image file does not exist.
    """
    mocker.patch('os.path.exists', return_value=False)
    mocker.patch('builtins.open', mock_open())
    mocker.patch('os.path.abspath', return_value="/mock/path/chart_1.png")
    mocker.patch('src.agents.report_finalization_node.HTML')

    updated_state = report_finalization_node(mock_graph_state_for_finalization)

    assert updated_state['status'] == "report_finalized"
    assert "*(Visual for [FIGURE 1] missing)*" in updated_state['final_report'].content
    assert "![Bar chart" not in updated_state['final_report'].content


def test_report_finalization_node_missing_figure_map_entry(mock_graph_state_for_finalization, mocker):
    """
    Tests handling of a scenario where a visual placeholder exists but has no
    corresponding entry in the figure_id_map.
    """
    # Remove the figure map entry for the mock draft
    mock_graph_state_for_finalization['report_sections_draft'].figure_id_map = {}
    mocker.patch('os.path.exists', return_value=True)
    mocker.patch('builtins.open', mock_open())
    mocker.patch('src.agents.report_finalization_node.HTML')

    updated_state = report_finalization_node(mock_graph_state_for_finalization)

    assert updated_state['status'] == "report_finalized"
    assert "*(Visual for [FIGURE 1] not mapped)*" in updated_state['final_report'].content


def test_report_finalization_node_pdf_generation_failure(mock_graph_state_for_finalization, mocker):
    """
    Tests that the node handles a failure during PDF generation gracefully,
    still completing the Markdown part.
    """
    mocker.patch('os.path.exists', return_value=True)
    mocker.patch('builtins.open', mock_open())

    # Mock weasyprint's write_pdf to raise an exception
    mocker.patch('src.agents.report_finalization_node.HTML').return_value.write_pdf.side_effect = Exception(
        "PDF generation failed")

    updated_state = report_finalization_node(mock_graph_state_for_finalization)

    assert updated_state['status'] == "report_finalized"  # Markdown part still succeeds
    assert updated_state['final_report'].pdf_file_path is None
    assert "Error generating PDF: PDF generation failed" in updated_state['error_message']


def test_report_finalization_node_empty_inputs(mocker):
    """Tests that the node can produce a valid, albeit minimal, report with empty inputs."""
    empty_draft = ReportSectionsDraft(
        introduction_text="",
        analysis_narratives=[],
        key_takeaways_bullet_points=[],
        conclusion_text="",
        dataset_title="",
        figure_id_map={},
        clarification_questions=[]
    )
    empty_state = GraphState(
        request_id="finalization_test_4",
        report_sections_draft=empty_draft,
        generated_visuals=[],
        status="report_drafted"
    )

    mocker.patch('os.path.exists', return_value=False)
    mocker.patch('builtins.open', mock_open())
    mocker.patch('src.agents.report_finalization_node.HTML')

    updated_state = report_finalization_node(empty_state)

    assert updated_state['status'] == "report_finalized"
    final_content = updated_state['final_report'].content
    assert "# Data Analysis Report" in final_content
    assert updated_state['final_report'].pdf_file_path is not None