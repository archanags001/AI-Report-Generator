import logging
from langgraph.graph import StateGraph, END
from graph.state import GraphState
from agents.data_analysis_node import data_analysis_node
from agents.visualization_node import visualization_node
from agents.insight_generation_node import insight_generation_node
from agents.report_drafting_node import report_drafting_node
from agents.report_finalization_node import report_finalization_node # Import the new report finalization node
from agents.safety_node import safety_check_node

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
def check_analysis_validity(state: GraphState) -> str:
    """
    Decides what to do next based on the result of data_analysis_node.
    Returns the name of the next node or END.
    """
    profile = state.get("dataframe_profile")

    if not profile:
        return END

    # add more checks
    if profile.num_rows < 5 or profile.num_columns < 2:
        return END  # Not enough data to continue

    return "visualization"


# def check_safety_status(state: GraphState) -> str:
#     """
#     Decides whether to proceed to report finalization or stop
#     based on the result of the safety check.
#     """
#     if state.get("status") == "error":
#         logger.error("Safety check failed. Halting workflow.")
#         return END

#     logger.info("Safety check passed. Proceeding to report finalization.")
#     return "report_finalization"

def check_safety_status(state: GraphState) -> str:
    """
    Decides whether to proceed to report finalization, retry, or stop
    based on the result of the safety check.
    """
    max_retries = 2
    current_retries = state.get("safety_check_retries", 0)
    current_status = state.get("status")

    if current_status == "error":
        if current_retries < max_retries:
            logger.warning(f"Safety check failed. Retrying report drafting. Attempt {current_retries + 1}/{max_retries}.")
            state['safety_check_retries'] = current_retries + 1
            state['status'] = "retrying"
            state['error_message'] = "Safety check failed, attempting to redraft the report."
            return "report_drafting"
        else:
            logger.error(f"Safety check failed after {max_retries} retries. Halting workflow.")
            state['status'] = "error"
            state['error_message'] = f"Report generation failed after {max_retries} attempts due to safety checks."
            return END

    logger.info("Safety check passed. Proceeding to report finalization.")
    return "report_finalization"
    

def create_graph_workflow():
    """
    Creates and compiles the LangGraph workflow for report generation.
    """
    workflow = StateGraph(GraphState)

    # Define the nodes in the graph
    workflow.add_node("data_analysis", data_analysis_node)
    workflow.add_node("visualization", visualization_node)
    workflow.add_node("insight_generation", insight_generation_node)
    workflow.add_node("report_drafting", report_drafting_node)
    workflow.add_node("safety_check", safety_check_node)
    workflow.add_node("report_finalization", report_finalization_node)

    # Define the entry point
    workflow.set_entry_point("data_analysis")

    # Define the edges (transitions between nodes)
    workflow.add_conditional_edges("data_analysis", check_analysis_validity, {
        "visualization": "visualization",
        END: END
    })
    workflow.add_edge("visualization", "insight_generation")
    workflow.add_edge("insight_generation", "report_drafting")
    # After report drafting, proceed to report finalization
    # workflow.add_edge("report_drafting", "report_finalization")
    workflow.add_edge("report_drafting", "safety_check")

    workflow.add_conditional_edges(
        "safety_check",
        check_safety_status,
        {
            "report_finalization": "report_finalization",
            "report_drafting": "report_drafting",  
            END: END
        }
    )

    # workflow.add_conditional_edges(
    #     "safety_check",
    #     check_safety_status,
    #     {
    #         "report_finalization": "report_finalization",
    #         END: END
    #     }
    # )
    # After report finalization, the graph ends for now.
    workflow.add_edge("report_finalization", END)

    # Compile the graph
    app = workflow.compile()
    return app



