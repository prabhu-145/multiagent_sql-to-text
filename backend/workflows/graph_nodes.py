from workflows.agent_state import AgentState

from agents.query_guard_agent import validate_user_query
from agents.sql_agent import handle_sql_query
from agents.biomarker_agent import handle_biomarker_query
from agents.statistical_agent import handle_statistical_query


def add_trace(state: AgentState, node_name: str):
    return state.get("route_trace", []) + [node_name]


def input_node(state: AgentState) -> AgentState:
    query = state.get("query", "")

    return {
        **state,
        "query": query.strip() if query else "",
        "intent": state.get("intent"),
        "result": state.get("result"),
        "error": state.get("error"),
        "attempts": state.get("attempts", 0),
        "route_trace": add_trace(state, "input_node"),
    }


def query_guard_node(state: AgentState) -> AgentState:
    query = state.get("query", "")

    try:
        guard_response = validate_user_query(query)

        guard_intent = guard_response.get("intent")
        guard_result = guard_response.get("result")

        # If Query Guard says clarification or invalid query, stop workflow later.
        if guard_intent in {
            "clarification_required",
            "invalid_query",
            "unsupported_query",
        }:
            return {
                **state,
                "intent": guard_intent,
                "result": guard_result,
                "error": None,
                "route_trace": add_trace(state, "query_guard_node"),
            }

        # Otherwise continue to router.
        return {
            **state,
            "intent": None,
            "result": None,
            "error": None,
            "route_trace": add_trace(state, "query_guard_node"),
        }

    except Exception as error:
        return {
            **state,
            "intent": "workflow_error",
            "result": {
                "agent": "query_guard_agent",
                "status": "failed",
                "message": "Query Guard node failed.",
                "error": str(error),
            },
            "error": str(error),
            "route_trace": add_trace(state, "query_guard_node"),
        }


def router_node(state: AgentState) -> AgentState:
    query = state.get("query", "").lower()

    try:
        statistical_keywords = [
            "average",
            "mean",
            "median",
            "standard deviation",
            "std",
            "correlation",
            "anova",
            "t-test",
            "ttest",
            "chi-square",
            "chisquare",
            "regression",
            "kaplan",
            "survival",
            "os by treatment",
            "pfs by treatment",
        ]

        biomarker_keywords = [
            "biomarker",
            "pubmed",
            "her2",
            "egfr",
            "kras",
            "pd-l1",
            "pdl1",
            "alk",
            "braf",
            "tp53",
            "msi",
            "tmb",
            "mutation in cancer",
            "explain",
            "what is",
        ]

        sql_keywords = [
            "show",
            "list",
            "count",
            "top",
            "highest",
            "lowest",
            "records",
            "patients",
            "samples",
            "ctdna records",
            "nanostring records",
            "assay",
            "shipped",
            "inventory",
            "clinical subjects",
            "clinical samples",
        ]

        if any(keyword in query for keyword in statistical_keywords):
            intent = "statistical_analysis"

        elif any(keyword in query for keyword in sql_keywords):
            intent = "sql_query"

        elif any(keyword in query for keyword in biomarker_keywords):
            intent = "biomarker_research"

        else:
            intent = "clarification_required"

        return {
            **state,
            "intent": intent,
            "route_trace": add_trace(state, "router_node"),
        }

    except Exception as error:
        return {
            **state,
            "intent": "workflow_error",
            "result": {
                "agent": "router_node",
                "status": "failed",
                "message": "Router node failed.",
                "error": str(error),
            },
            "error": str(error),
            "route_trace": add_trace(state, "router_node"),
        }


def sql_agent_node(state: AgentState) -> AgentState:
    query = state.get("query", "")

    try:
        result = handle_sql_query(query)

        return {
            **state,
            "intent": "sql_query",
            "result": result,
            "error": None,
            "route_trace": add_trace(state, "sql_agent_node"),
        }

    except Exception as error:
        return {
            **state,
            "intent": "sql_query",
            "result": {
                "agent": "sql_agent",
                "status": "failed",
                "message": "SQL Agent node failed.",
                "error": str(error),
            },
            "error": str(error),
            "route_trace": add_trace(state, "sql_agent_node"),
        }


def statistical_agent_node(state: AgentState) -> AgentState:
    query = state.get("query", "")

    try:
        result = handle_statistical_query(query)

        return {
            **state,
            "intent": "statistical_analysis",
            "result": result,
            "error": None,
            "route_trace": add_trace(state, "statistical_agent_node"),
        }

    except Exception as error:
        return {
            **state,
            "intent": "statistical_analysis",
            "result": {
                "agent": "statistical_agent",
                "status": "failed",
                "message": "Statistical Agent node failed.",
                "error": str(error),
            },
            "error": str(error),
            "route_trace": add_trace(state, "statistical_agent_node"),
        }


def biomarker_agent_node(state: AgentState) -> AgentState:
    query = state.get("query", "")

    try:
        result = handle_biomarker_query(query)

        return {
            **state,
            "intent": "biomarker_research",
            "result": result,
            "error": None,
            "route_trace": add_trace(state, "biomarker_agent_node"),
        }

    except Exception as error:
        return {
            **state,
            "intent": "biomarker_research",
            "result": {
                "agent": "biomarker_agent",
                "status": "failed",
                "message": "Biomarker Agent node failed.",
                "error": str(error),
            },
            "error": str(error),
            "route_trace": add_trace(state, "biomarker_agent_node"),
        }


def clarification_node(state: AgentState) -> AgentState:
    existing_result = state.get("result")

    if existing_result:
        result = existing_result
    else:
        result = {
            "agent": "query_guard_agent",
            "status": "clarification_required",
            "message": "Your query is unclear. Please ask a valid biomarker, SQL, or statistical query.",
            "suggestions": [
                "What is HER2 biomarker?",
                "Show ctDNA records",
                "Average OS by treatment group",
            ],
        }

    return {
        **state,
        "intent": state.get("intent") or "clarification_required",
        "result": result,
        "route_trace": add_trace(state, "clarification_node"),
    }


def error_node(state: AgentState) -> AgentState:
    return {
        **state,
        "intent": "workflow_error",
        "result": {
            "agent": "langgraph_workflow",
            "status": "failed",
            "message": "Workflow failed before reaching an agent.",
            "error": state.get("error") or "Unknown workflow error.",
        },
        "route_trace": add_trace(state, "error_node"),
    }


def final_node(state: AgentState) -> AgentState:
    result = state.get("result")

    if isinstance(result, dict):
        result["route_trace"] = add_trace(state, "final_node")

    return {
        **state,
        "result": result,
        "route_trace": add_trace(state, "final_node"),
    }


def should_continue_after_guard(state: AgentState) -> str:
    intent = state.get("intent")

    if intent in {
        "clarification_required",
        "invalid_query",
        "unsupported_query",
    }:
        return "clarification_node"

    if intent == "workflow_error":
        return "error_node"

    return "router_node"


def route_by_intent(state: AgentState) -> str:
    intent = state.get("intent")

    if intent == "sql_query":
        return "sql_agent_node"

    if intent == "statistical_analysis":
        return "statistical_agent_node"

    if intent == "biomarker_research":
        return "biomarker_agent_node"

    if intent == "workflow_error":
        return "error_node"

    return "clarification_node"