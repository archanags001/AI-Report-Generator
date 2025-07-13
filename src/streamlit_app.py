import base64
import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv
import uuid
import logging
from datetime import datetime
import google.generativeai as genai
from graph.state import GraphState
from graph.builder import create_graph_workflow
from schemas.messages import GeneratedVisual, AnalysisInsight, ReportSectionsDraft, ReportFormat

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Directory setup ---
LOCAL_APP_DATA_DIR = "local_app_data"
UPLOAD_DIR = os.path.join(LOCAL_APP_DATA_DIR, "uploads")
CHART_OUTPUT_DIR = os.path.join(LOCAL_APP_DATA_DIR, "charts")
REPORT_OUTPUT_DIR = os.path.join(LOCAL_APP_DATA_DIR, "reports")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(CHART_OUTPUT_DIR, exist_ok=True)
os.makedirs(REPORT_OUTPUT_DIR, exist_ok=True)
load_dotenv()
try:
    gemini_api_key = os.getenv("GEMINI_API_KEY") # Use os.environ.get for consistency
    if not gemini_api_key:
        logger.warning("GOOGLE_API_KEY environment variable not set. LLM calls may fail.")
        st.error("GOOGLE_API_KEY environment variable not set. Please set it to use the AI features.")
        st.stop() # Stop the app if API key is critical and missing/invalid
    genai.configure(api_key=gemini_api_key)
except Exception as e:
    logger.error(f"Failed to configure Google Gemini API: {e}. Ensure GOOGLE_API_KEY is set.")
    st.error("Failed to configure Google Gemini API. Please ensure GOOGLE_API_KEY is set in your environment variables.")
    st.stop() # St


def check_instruction_relevance(uploaded_file, user_instructions: str) -> str:
    """
    Uses an LLM to determine if the user's instruction is relevant for data report generation.
    Returns 'YES' if relevant, or a polite rejection message otherwise.
    """
    model = genai.GenerativeModel('gemini-2.5-flash')

    try:

        try:
            df = pd.read_csv(uploaded_file)
        except Exception as e:
            st.error(f"Error reading file: {e}")

        if df.empty:
            return "The uploaded CSV file is empty. Please upload a file with data."

        # Create a summary of the DataFrame to send to the LLM
        # Avoid sending the entire DataFrame for token efficiency and context
        # dataframe_summary = f"First 5 rows of the data:\n{df.head().to_string()}\n\n" \
        #                     f"Data Info:\n{df.info(buf=None, verbose=True, show_counts=True)}"

        # Craft the prompt for the LLM
        prompt = f"""
        You are an AI assistant whose sole purpose is to determine if a user's instruction
        is suitable for generating a data analysis report based on a given dataset.

        The instruction is relevant if it asks for:
        - Data analysis (e.g., trends, patterns, correlations, outliers).
        - Report generation (e.g., "generate a report", "summarize data").
        - Insights or findings from the data.

        The instruction is NOT relevant if it is:
        - A general question unrelated to data.
        - A request for creative writing.
        - A question about topics outside of data analysis or report generation.
        - A request to perform actions not related to generating a report (e.g., "send an email").
        - A question about your own internal workings or safety settings.

        Here is the provided data:
        {df}

        User Instruction: "{user_instructions}"

        If the instruction is directly related to analyzing this data or generating a report about it, reply ONLY with the word 'YES'.
        Otherwise, politely decline to answer by stating: "I am a report generator AI and do not have information on that topic. Please give instructions related to data report generation."
        Do NOT provide any other information or explanation if you are declining.
        """

        response = model.generate_content(prompt)
        return response.text.strip()

    except pd.errors.EmptyDataError:
        return "The uploaded CSV file is empty. Please upload a file with data."
    except Exception as e:
        logger.error(f"Error checking instruction relevance with LLM or reading file: {e}", exc_info=True)
        return f"An error occurred while checking your instruction. Please try again."


st.set_page_config(page_title="AI Report Generator", layout="wide")
st.title("📊 AI-Powered Data Analysis & Report Generator")

st.markdown("""
    Upload your CSV, provide instructions, and let the AI generate a comprehensive report.
""")

uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])
user_instructions = st.text_area(
    "Enter your instructions for the report",height=100)
if not user_instructions:
    user_instructions = "data analysis report"
if uploaded_file:
    if st.button("Generate Report"):
        with st.spinner("Checking your instruction..."):
            relevance_reply = check_instruction_relevance(uploaded_file, user_instructions)

        if relevance_reply != 'YES':
            st.warning(relevance_reply)
            st.stop()
        with st.spinner("Processing data, generating profile, visuals, insights, drafting and finalizing report..."):
            request_id = str(uuid.uuid4())
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_filename = f"{timestamp}_{uploaded_file.name}"
            file_save_path = os.path.join(UPLOAD_DIR, unique_filename)
            # Save the uploaded file
            try:
                with open(file_save_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                logger.info(f"File saved to: {file_save_path}")
            except Exception as e:
                st.error(f"Error saving file: {e}")
                logger.error(f"File saving error: {e}", exc_info=True)
                st.stop()

            # Initialize GraphState for this request
            initial_state: GraphState = {
                "request_id": request_id,
                "file_path": file_save_path,
                "instructions": user_instructions,
                "dataframe_profile": None,
                "analysis_insights": None,
                "generated_visuals": None,
                "report_sections_draft": None,
                "final_report": None,
                "feedback_history": [],
                "status": "initial",
                "error_message": None,
            }

            # Initialize and run the graph workflow
            try:
                workflow_app = create_graph_workflow()

                final_state = workflow_app.invoke(initial_state)

                if final_state and final_state['status'] == "report_finalized":
                    st.success("🎉 Report Generation Complete!")
                    st.success("Data Profile, Visualizations, Insights, Report Drafted, and Finalized !")
                    st.subheader("📄 Final Report Downloads")
                    if final_state['final_report']:
                        if final_state['final_report'].pdf_file_path and os.path.exists(
                                final_state['final_report'].pdf_file_path):
                            pdf_file_content = None
                            try:
                                with open(final_state['final_report'].pdf_file_path, "rb") as file:
                                    pdf_file_content = file.read()
                            except Exception as e:
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
                                with st.container():
                                    st.markdown(
                                        """
                                        <style>
                                        /* This targets Streamlit's internal div for the container. May not be stable across versions. */
                                        /* A more robust way for centering iframes might be to wrap it in a div with specific CSS */
                                        .stContainer > div {
                                            width: 55%; /* This might affect all st.container elements */
                                            margin: auto;
                                        }
                                        </style>
                                        """,
                                        unsafe_allow_html=True
                                    )

                                    base64_pdf = base64.b64encode(pdf_file_content).decode(
                                        "utf-8")
                                    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf"></iframe>'
                                    st.markdown(pdf_display, unsafe_allow_html=True)
                            else:
                                st.warning("PDF report content not available for download or preview.")
                                if "Error generating PDF" in (final_state.get('error_message') or ""):
                                    st.error("PDF generation failed. Check terminal logs for details.")
                        else:
                            st.warning("PDF report file not found or could not be generated.")
                            if "Error generating PDF" in (final_state.get('error_message') or ""):
                                st.error("PDF generation failed. Check terminal logs for details.")

                    else:
                        st.warning("Final report content not available.")

            except Exception as e:
                st.error(f"An unexpected critical error occurred during graph execution: {e}")
                logger.error(f"Streamlit App Graph Execution Error: {e}", exc_info=True)
