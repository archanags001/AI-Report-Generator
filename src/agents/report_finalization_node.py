import logging
import os
import re
from datetime import datetime
import traceback
import markdown
from weasyprint import HTML
from graph.state import GraphState
from schemas.messages import ReportFormat

logger = logging.getLogger(__name__)

# LOCAL_APP_DATA_DIR = "local_app_data"
# REPORT_OUTPUT_DIR = os.path.join(LOCAL_APP_DATA_DIR, "reports")
# CHART_OUTPUT_DIR = os.path.join(LOCAL_APP_DATA_DIR, "charts")
#
# os.makedirs(REPORT_OUTPUT_DIR, exist_ok=True)
# os.makedirs(CHART_OUTPUT_DIR, exist_ok=True)


def report_finalization_node(state: GraphState) -> GraphState:
    """
    Finalizes the report by assembling all drafted sections and generated visuals
    into a complete document (e.g., Markdown), saves it, and also generates a PDF.
    """
    request_id = state['request_id']
    # report_sections_draft = state['report_sections_draft']
    # generated_visuals = state['generated_visuals']
    # dataset_name = state.get('dataset_name','Unnamed Dataset')
    report_sections_draft = state.get('report_sections_draft', None)
    generated_visuals = state.get('generated_visuals', [])
    dataset_name = state.get('dataset_name', 'Unnamed Dataset')
    report_output_dir = state.get('report_output_dir', os.path.join("local_app_data", "reports"))
    chart_output_dir = state.get('chart_output_dir', os.path.join("local_app_data", "charts"))

    logger.info(f"ReportFinalizationNode processing request: {request_id}")
    logger.info(f"DEBUG: Entering ReportFinalizationNode. Current status: {state['status']}")

    os.makedirs(report_output_dir, exist_ok=True)
    os.makedirs(chart_output_dir, exist_ok=True)

    if not report_sections_draft:
        logger.error(f"Report sections draft is missing for request {request_id}.")
        state['status'] = "error"
        state['error_message'] = "Cannot finalize report: Report sections draft is missing."
        return state

    final_report_content_md_sections = []
    pdf_file_path = None
    try:
        # Add title and metadata
        dataset_name =  report_sections_draft.dataset_title
        final_report_content_md_sections.append(f"# Data Analysis Report: {dataset_name}\n\n")
        final_report_content_md_sections.append(f"**Date Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        final_report_content_md_sections.append("---")

        # 1. Introduction
        final_report_content_md_sections.append("\n## 1. Introduction\n")
        final_report_content_md_sections.append(report_sections_draft.introduction_text)

        # 2. Analysis Narratives and Visuals
        final_report_content_md_sections.append("\n## 2. Analysis and Findings\n")
        visuals_by_id = {visual.visual_id: visual for visual in generated_visuals} if generated_visuals else {}
        for i, narrative_original_md in enumerate(report_sections_draft.analysis_narratives):
            current_narrative_text = narrative_original_md
            embedded_visuals_markdown_for_this_narrative = []
            figure_id_map = report_sections_draft.figure_id_map or {}
            figure_placeholders_in_narrative = re.findall(r'\[FIGURE (\d+)\]', narrative_original_md)
            unique_figure_numbers = sorted(list(set(figure_placeholders_in_narrative)), key=int)

            for fig_num_str in unique_figure_numbers:
                generic_figure_placeholder = f"[FIGURE {fig_num_str}]"
                if generic_figure_placeholder in figure_id_map:
                    visual_id_from_map = figure_id_map[generic_figure_placeholder]
                    visual_obj = visuals_by_id.get(visual_id_from_map)

                    if visual_obj and os.path.exists(visual_obj.file_path):
                        current_narrative_text = current_narrative_text.replace(
                            generic_figure_placeholder,
                            f"Figure {fig_num_str}"
                        )
                        abs_chart_path_url = f"file:///{os.path.abspath(visual_obj.file_path).replace(os.sep, '/')}"
                        embedded_visuals_markdown_for_this_narrative.append(
                            f"\n![{visual_obj.description}]({abs_chart_path_url})\n")
                        embedded_visuals_markdown_for_this_narrative.append(
                            f"**Figure {fig_num_str}:** {visual_obj.description}\n")
                    else:
                        logger.warning(
                            f"Visual ID '{visual_id_from_map}' mapped to '{generic_figure_placeholder}' not found or file missing at '{visual_obj.file_path if visual_obj else 'N/A'}' for request {request_id}.")
                        current_narrative_text = current_narrative_text.replace(
                            generic_figure_placeholder,
                            f"*(Visual for {generic_figure_placeholder} missing)*"
                        )
                else:
                    logger.warning(
                        f"'{generic_figure_placeholder}' found in narrative but no corresponding 'visual_id' in 'figure_id_map' for request {request_id}.")
                    current_narrative_text = current_narrative_text.replace(
                        generic_figure_placeholder,
                        f"*(Visual for {generic_figure_placeholder} not mapped)*"
                    )
            if current_narrative_text:
                parts = current_narrative_text.split(":-", 1)
                title_from_narrative = parts[0].strip()
                body_from_narrative = parts[1].strip() if len(parts) > 1 else ''
            else:
                title_from_narrative = 'Finding'
                body_from_narrative = ''

            final_report_content_md_sections.append(f"\n### 2.{i + 1}. {title_from_narrative}\n")
            final_report_content_md_sections.append(body_from_narrative)
            final_report_content_md_sections.extend(embedded_visuals_markdown_for_this_narrative)
            final_report_content_md_sections.append("\n")

        # 3. Key Takeaways
        final_report_content_md_sections.append("\n## 3. Key Takeaways\n")
        for takeaway in report_sections_draft.key_takeaways_bullet_points:
            final_report_content_md_sections.append(f"- {takeaway}\n")

        # 4. Conclusion
        final_report_content_md_sections.append("\n## 4. Conclusion\n")
        final_report_content_md_sections.append(report_sections_draft.conclusion_text)

        # # 5. Clarification Questions (if any)
        # if report_sections_draft.clarification_questions:
        #     final_report_content_md_sections.append("\n## 5. Clarification Questions\n")
        #     final_report_content_md_sections.append(
        #         "To further enhance this report, please consider the following questions:\n")
        #     for q in report_sections_draft.clarification_questions:
        #         final_report_content_md_sections.append(f"- {q}\n")

        full_report_string_md = "\n".join(final_report_content_md_sections)
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename_base = f"report_{timestamp_str}"
        report_md_file_path = os.path.join(report_output_dir, f"{report_filename_base}.md")
        try:
            with open(report_md_file_path, "w", encoding="utf-8") as f:
                f.write(full_report_string_md)
            logger.info(f"Final Markdown report saved to: {report_md_file_path}")
        except Exception as e:
            logger.error(f"Error saving final Markdown report to file for request {request_id}: {e}", exc_info=True)
            state['status'] = "error"
            state['error_message'] = f"Error saving final Markdown report: {e}"
            return state

        try:
            html_content = f"""
            <html>
            <head>
                <title>Data Analysis Report - {dataset_name}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 20mm; color: #333; }}
                    h1 {{ color: #1a237e; border-bottom: 2px solid #1a237e; padding-bottom: 10px; }}
                    h2 {{ color: #283593; border-bottom: 1px solid #c5cae9; padding-bottom: 5px; margin-top: 25px; }}
                    h3 {{ color: #3949ab; margin-top: 20px; }}
                    img {{ max-width: 90%; height: auto; display: block; margin: 15px auto; border: 1px solid #ddd; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); }}
                    pre {{ background-color: #f4f4f4; padding: 10px; border-radius: 5px; overflow-x: auto; font-family: 'Courier New', Courier, monospace; font-size: 0.9em; }}
                    p, ul, ol {{ margin-bottom: 1em; }}
                    strong {{ font-weight: bold; }}
                    em {{ font-style: italic; }}
                    code {{ font-family: 'Courier New', Courier, monospace; background-color: #eee; padding: 2px 4px; border-radius: 3px; }}
                    hr {{ border: 0; height: 1px; background: #eee; margin: 2em 0; }}
                </style>
            </head>
            <body>
                {markdown.markdown(full_report_string_md, extensions=['fenced_code', 'tables', 'nl2br'])}
            </body>
            </html>
            """

            report_pdf_file_path = os.path.join(report_output_dir, f"{report_filename_base}.pdf")
            HTML(string=html_content, base_url=report_output_dir).write_pdf(report_pdf_file_path)
            pdf_file_path = report_pdf_file_path
            logger.info(f"Final PDF report saved to: {pdf_file_path}")


        except Exception as e:
            logger.error(f"Error generating PDF report for request {request_id}: {e}", exc_info=True)
            if 'error_message' in state:
                state['error_message'] += f"\nError generating PDF: {e}"
            else:
                state['error_message'] = f"Error generating PDF: {e}"
            pdf_file_path = None
            # logger.error(f"Error generating PDF report for request {request_id}: {e}", exc_info=True)
            # state['error_message'] = (state['error_message'] or "") + f"\nError generating PDF: {e}"
            # pdf_file_path = None

        # Update state with the final report details
        state['final_report'] = ReportFormat(
            content=full_report_string_md,
            format_type="markdown",
            pdf_file_path=pdf_file_path
        )
        state['status'] = "report_finalized"
        logger.info(f"ReportFinalizationNode completed for request: {request_id}. Report finalized and saved.")
        return state

    except Exception as e:
        logger.error(f"An unexpected error occurred in ReportFinalizationNode for request {request_id}: {e}",
                     exc_info=True)
        state['status'] = "error"
        state['error_message'] = f"An unexpected error occurred during report finalization: {e}"
        return state
