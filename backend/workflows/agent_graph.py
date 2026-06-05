# backend/workflows/agent_graph.py

from langgraph.graph import StateGraph, END
from workflows.agent_state import AgentState
from workflows.graph_nodes import (
    input_node,
    query_guard_node,
    router_node,
    sql_agent_node,
    statistical_agent_node,
    biomarker_agent_node,
    clarification_node,
    error_node,
    final_node,
    should_continue_after_guard,
    route_by_intent,
)


class GraphExecutionTrace:
    def __init__(self):
        self.trace = []

    def log(self, node_name: str, result: dict):
        self.trace.append({
            "node": node_name,
            "result": result
        })

    def get_trace(self):
        return self.trace

    def clear_trace(self):
        self.trace = []


def build_agent_graph():
    graph = StateGraph(AgentState)

    # Add all nodes
    graph.add_node("input_node", input_node)
    graph.add_node("query_guard_node", query_guard_node)
    graph.add_node("router_node", router_node)
    graph.add_node("sql_agent_node", sql_agent_node)
    graph.add_node("statistical_agent_node", statistical_agent_node)
    graph.add_node("biomarker_agent_node", biomarker_agent_node)
    graph.add_node("clarification_node", clarification_node)
    graph.add_node("error_node", error_node)
    graph.add_node("final_node", final_node)

    # Entry point
    graph.set_entry_point("input_node")

    # Linear flow: input → query_guard
    graph.add_edge("input_node", "query_guard_node")

    # Conditional edges after query guard
    graph.add_conditional_edges(
        "query_guard_node",
        should_continue_after_guard,
        {
            "router_node": "router_node",
            "clarification_node": "clarification_node",
            "error_node": "error_node",
        },
    )

    # Route by intent
    graph.add_conditional_edges(
        "router_node",
        route_by_intent,
        {
            "sql_agent_node": "sql_agent_node",
            "statistical_agent_node": "statistical_agent_node",
            "biomarker_agent_node": "biomarker_agent_node",
            "clarification_node": "clarification_node",
            "error_node": "error_node",
        },
    )

    # All agent outputs → final
    graph.add_edge("sql_agent_node", "final_node")
    graph.add_edge("statistical_agent_node", "final_node")
    graph.add_edge("biomarker_agent_node", "final_node")
    graph.add_edge("clarification_node", "final_node")
    graph.add_edge("error_node", "final_node")

    # Final node → END
    graph.add_edge("final_node", END)

    return graph.compile()


agent_graph = build_agent_graph()


def run_agent_graph(query: str) -> dict:
    initial_state: AgentState = {
        "query": query,
        "intent": None,
        "result": None,
        "error": None,
        "attempts": 0,
        "route_trace": [],
    }

    final_state = agent_graph.invoke(initial_state)

    return {
        "intent": final_state.get("intent") or "workflow_unknown",
        "result": final_state.get("result") or {
            "agent": "langgraph_workflow",
            "status": "failed",
            "message": "No result returned from graph.",
            "route_trace": final_state.get("route_trace", []),
        },
    }