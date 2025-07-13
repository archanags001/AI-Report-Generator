from langgraph.graph import StateGraph, END
from graph.state import GraphState
from agents.data_analysis_node import data_analysis_node
from agents.visualization_node import visualization_node
from agents.insight_generation_node import insight_generation_node
from agents.report_drafting_node import report_drafting_node
from agents.report_finalization_node import report_finalization_node # Import the new report finalization node

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
    workflow.add_node("report_finalization", report_finalization_node) # Add the report finalization node

    # Define the entry point
    workflow.set_entry_point("data_analysis")

    # Define the edges (transitions between nodes)
    workflow.add_edge("data_analysis", "visualization")
    workflow.add_edge("visualization", "insight_generation")
    workflow.add_edge("insight_generation", "report_drafting")
    # After report drafting, proceed to report finalization
    workflow.add_edge("report_drafting", "report_finalization")
    # After report finalization, the graph ends for now.
    workflow.add_edge("report_finalization", END)

    # Compile the graph
    app = workflow.compile()
    return app








# from langgraph.graph import StateGraph, END
# from src.graph.state import GraphState
# from src.agents.data_analysis_node import data_analysis_node
# from src.agents.visualization_node import visualization_node
# from src.agents.insight_generation_node import insight_generation_node
# from src.agents.report_drafting_node import report_drafting_node # Import the new report drafting node
#
# def create_graph_workflow():
#     """
#     Creates and compiles the LangGraph workflow for report generation.
#     """
#     workflow = StateGraph(GraphState)
#
#     # Define the nodes in the graph
#     workflow.add_node("data_analysis", data_analysis_node)
#     workflow.add_node("visualization", visualization_node)
#     workflow.add_node("insight_generation", insight_generation_node)
#     workflow.add_node("report_drafting", report_drafting_node) # Add the report drafting node
#
#     # Define the entry point
#     workflow.set_entry_point("data_analysis")
#
#     # Define the edges (transitions between nodes)
#     workflow.add_edge("data_analysis", "visualization")
#     workflow.add_edge("visualization", "insight_generation")
#     # After insight generation, proceed to report drafting
#     workflow.add_edge("insight_generation", "report_drafting")
#     # After report drafting, for now, the graph ends.
#     # Later, this might lead to refinement or final formatting.
#     workflow.add_edge("report_drafting", END)
#
#     # Compile the graph
#     app = workflow.compile()
#     return app
#





