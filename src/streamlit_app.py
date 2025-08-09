import re
import base64
import streamlit as st
import os
import uuid
import logging
from datetime import datetime
from graph.state import GraphState
from graph.builder import create_graph_workflow
from schemas.messages import GeneratedVisual, AnalysisInsight, ReportSectionsDraft, ReportFormat
import streamlit.components.v1 as components

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Directory setup ---
LOCAL_APP_DATA_DIR = "local_app_data"
UPLOAD_DIR = os.path.join(LOCAL_APP_DATA_DIR, "uploads")
CHART_OUTPUT_DIR = os.path.join(LOCAL_APP_DATA_DIR, "charts")
REPORT_OUTPUT_DIR = os.path.join(LOCAL_APP_DATA_DIR, "reports")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(CHART_OUTPUT_DIR, exist_ok=True)
os.makedirs(REPORT_OUTPUT_DIR, exist_ok=True)
# load_dotenv()

def sanitize_filename(filename: str) -> str:
    """
    Sanitizes a filename to prevent directory traversal and other security issues.
    Replaces non-alphanumeric characters with underscores.
    """
    sanitized_name = re.sub(r'[^\w\.-]', '_', filename)
    sanitized_name = sanitized_name.strip(' .')
    sanitized_name = sanitized_name.replace('..', '_')
    return sanitized_name

def display_pdf(pdf_bytes):
    """
    Encodes PDF bytes to base64 and displays them in a Streamlit app using an iframe.
    This method is more robust for cloud deployments.
    """
    if pdf_bytes:
        base64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")
        pdf_display_html = f"""
        <div style="width: 100%; height: 600px; border: 1px solid #ccc; border-radius: 8px; overflow: hidden;">
            <iframe 
                src="data:application/pdf;base64,{base64_pdf}" 
                width="100%" 
                height="100%" 
                style="border: none;">
            </iframe>
        </div>
        """
        # Using components.html is often more reliable than st.markdown for custom HTML
        components.html(pdf_display_html, height=620)
    else:
        st.error("No PDF content to display.")


st.set_page_config(page_title="AI Report Generator", layout="wide")
st.title("📊 AI Data Analyst & Report Generator")

st.markdown("""
    Upload your CSV, provide instructions, and let the AI generate a comprehensive report.
""")

uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])

user_instructions = st.text_area(
    "✏️ What kind of report or analysis do you need? (optional)",
    placeholder="e.g., Provide summary statistics and highlight key trends",
    height=120,
    max_chars=200
)
# Sanitize user instructions
user_instructions = user_instructions.strip()
# user_instructions = st.text_area(
#     "Enter your instructions for the report", height=100)
if not user_instructions:
    user_instructions = "data analysis report"

if uploaded_file:
    if st.button("Generate Report"):
        # Use a more advanced progress display
        status_message = st.empty()
        progress_bar = st.progress(0)
        # progress_text = st.empty()

        # Define the order of steps for the progress bar
        steps = [
            "data_analysis",
            "visualization",
            "insight_generation",
            "report_drafting",
            "safety_check",
            "report_finalization"
        ]

        # Map node names to user-friendly messages for a more specific UI
        step_messages = {
            "data_analysis": "🔍 Analyzing data and creating a profile...",
            "visualization": "📊 Generating visualizations...",
            "insight_generation": "💡 Generating key insights from the data...",
            "report_drafting": "✍️ Drafting the report content...",
            "safety_check": "🛡️ Performing a safety and accuracy check...",
            "report_finalization": "✅ Finalizing the report and generating output files..."
        }

        request_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Sanitize the filename to prevent security vulnerabilities
        sanitized_filename = sanitize_filename(uploaded_file.name)
        unique_filename = f"{timestamp}_{sanitized_filename}"
        file_save_path = os.path.join(UPLOAD_DIR, unique_filename)

        try:
            with open(file_save_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            logger.info(f"File saved to: {file_save_path}")
        except Exception as e:
            st.info("You can try running the process again.")
            st.error(f"Error saving file: {e}")
            logger.error(f"File saving error: {e}", exc_info=True)
            st.stop()

        initial_state: GraphState = {
            "request_id": request_id,
            "file_path": file_save_path,
            "instructions": user_instructions,
            "dataframe_profile": None,
            "analysis_insights": None,
            "generated_visuals": None,
            "report_sections_draft": None,
            "final_report": None,
            "status": "initial",
            "error_message": None,
            "safety_check_retries": 0,
        }

        try:
            workflow_app = create_graph_workflow()
            final_state = None

            with st.spinner(
                    "Processing data, generating profile, visuals, insights, drafting and finalizing report..."):

                # Display initial message
                status_message.info("Graph workflow started...")
                # progress_text.info("Graph workflow started...")

                # Stream the graph execution to show progress
                for i, state in enumerate(workflow_app.stream(initial_state)):
                    for node, current_state in state.items():
                        if node != "__end__":
                            if current_state.get('status') == 'retrying':
                                retries = current_state.get('safety_check_retries', 0)
                                st.warning(f"⚠️ Safety check failed. Retrying report drafting (Attempt {retries} of 2)...")
                            else:
                                # Otherwise, show the normal progress messages
                                progress_value = (steps.index(node) + 1) / len(steps)
                                progress_bar.progress(progress_value)
                                status_message.info(step_messages.get(node, f'Processing {node}...'))
                            
                            # Update the progress bar and status message
                            # progress_value = (i + 1) / len(steps)
                            # progress_bar.progress(progress_value)
                            # status_message.info(step_messages.get(node, f'Processing {node}...'))
                            final_state = current_state

                # After the loop, hide the progress bar
                progress_bar.empty()
                status_message.empty()

                # Map node names to user-friendly messages
                step_messages = {
                    "data_analysis": "🔍 Analyzing data and creating a profile...",
                    "visualization": "📊 Generating visualizations...",
                    "insight_generation": "💡 Generating key insights from the data...",
                    "report_drafting": "✍️ Drafting the report content...",
                    "safety_check": "🛡️ Performing a safety and accuracy check...",
                    "report_finalization": "✅ Finalizing the report and generating output files..."
                }

                # # Stream the graph execution to show progress
                # for state in workflow_app.stream(initial_state):
                #     for node, current_state in state.items():
                #         if node != "__end__":
                #             progress_text.info(f"{step_messages.get(node, f'Processing {node}...')}")
                #             final_state = current_state

                # After the loop, check the final state for errors
                if final_state.get("status") == "error":
                    st.info("You can try running the process again.")
                    st.error(f"❌ An error occurred: {final_state.get('error_message')}")
                    
                    # Don't proceed to display report content
                elif final_state.get('status') == 'invalid_instructions':
                    st.warning("⚠️ The AI could not process your instructions.")
                    st.info("💡 Please give instructions related to data reporting.")
                else:
                    st.success("🎉 Report Generation Complete!")
                    st.success("Data Profile, Visualizations, Insights, Report Drafted, and Finalized!")
                    st.subheader("📄 Final Report Downloads")

                    # Report display logic
                    if final_state and final_state['final_report']:
                        if final_state['final_report'].pdf_file_path and os.path.exists(final_state['final_report'].pdf_file_path):
                            pdf_file_content = None
                            try:
                                with open(final_state['final_report'].pdf_file_path, "rb") as file:
                                    pdf_file_content = file.read()
                                # st.write(f"PDF content loaded? {pdf_file_content is not None}")
                            except Exception as e:
                                st.info("You can try running the process again.")
                                st.error(f"Error reading PDF file for download/preview: {e}")
                                pdf_file_content = None

                            if pdf_file_content:
                                st.download_button(
                                    label="Download Final Report (PDF)",
                                    data=pdf_file_content,
                                    file_name=os.path.basename(final_state['final_report'].pdf_file_path),
                                    mime="application/pdf",
                                    key="download_pdf_button"
                                )
                                
                                # with st.container():
                                #     st.markdown(
                                #         """
                                #         <style>
                                #         .stContainer > div {
                                #             width: 55%;
                                #             margin: auto;
                                #         }
                                #         </style>
                                #         """,
                                #         unsafe_allow_html=True
                                #     )

                                # display_pdf(pdf_file_content)

                                # base64_pdf = base64.b64encode(pdf_file_content).decode("utf-8")
                                # pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf"></iframe>'
                                # st.markdown(pdf_display, unsafe_allow_html=True)
                            
                                
                            else:
                                st.warning("PDF report content not available for download or preview.")
                                if "Error generating PDF" in (final_state.get('error_message') or ""):
                                    st.info("You can try running the process again.")
                                    st.error("PDF generation failed. Check terminal logs for details.")
                                    
                        else:
                            st.warning("PDF report file not found or could not be generated.")
                            if "Error generating PDF" in (final_state.get('error_message') or ""):
                                st.info("You can try running the process again.")
                                st.error("PDF generation failed. Check terminal logs for details.")
                                
                    else:
                        st.warning("Final report content not available.")

        except Exception as e:
            st.info("You can try running the process again.")
            st.error(f"❌ An unexpected critical error occurred during graph execution: {e}")
            logger.error(f"An unexpected critical error occurred during graph execution:: {e}", exc_info=True)
            st.stop()
