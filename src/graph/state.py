from typing import List, Optional, TypedDict
from schemas.messages import DataProfile, AnalysisInsight, GeneratedVisual, ReportSectionsDraft, ReportFormat, UserFeedback

class GraphState(TypedDict):
    """
    Represents the state of our graph.

    Attributes:
        request_id (str): A unique identifier for the current report generation request.
        file_path (str): The path to the uploaded CSV file.
        instructions (str): User's original instructions for the report.
        dataframe_profile (Optional[DataProfile]): Profile of the uploaded dataframe after initial analysis.
        analysis_insights (Optional[List[AnalysisInsight]]): List of key insights derived from the data.
        generated_visuals (Optional[List[GeneratedVisual]]): List of paths to generated visualization images.
        report_sections_draft (Optional[ReportSectionsDraft]): The drafted sections of the report.
        final_report (Optional[ReportFormat]): The assembled final report.
        feedback_history (Optional[List[UserFeedback]]): History of user feedback for iterative refinement.
        status (str): Current status of the report generation process (e.g., "pending", "data_profiled", "visuals_generated", "insights_generated", "draft_ready", "clarification_needed", "completed", "error").
        error_message (Optional[str]): Any error message if the process fails.
    """
    request_id: str
    file_path: str
    instructions: str
    dataframe_profile: Optional[DataProfile]
    analysis_insights: Optional[List[AnalysisInsight]]
    generated_visuals: Optional[List[GeneratedVisual]]
    report_sections_draft: Optional[ReportSectionsDraft]
    final_report: Optional[ReportFormat]
    feedback_history: Optional[List[UserFeedback]]
    status: str
    error_message: Optional[str]
    safety_check_retries: int
