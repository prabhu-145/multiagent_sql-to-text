from agents.sql_agent import handle_sql_query
from agents.statistical_agent import handle_statistical_query
from agents.biomarker_agent import handle_biomarker_query
from agents.query_guard_agent import validate_user_query


STAT_KEYWORDS = [
    "t-test",
    "ttest",
    "anova",
    "correlation",
    "mean",
    "median",
    "average",
    "standard deviation",
    "std",
    "variance",
    "regression",
    "compare statistically",
    "compare treatment",
    "p-value",
    "p value",
    "survival analysis",
    "kaplan",
    "os by",
    "pfs by",
    "average os",
    "average pfs",
    "mean os",
    "mean pfs",
    "chi-square",
    "chi square",
]

SQL_KEYWORDS = [
    "show",
    "list",
    "count",
    "how many",
    "top",
    "patients",
    "samples",
    "study",
    "enrollment",
    "records",
    "data",
]

BIOMARKER_KEYWORDS = [
    "biomarker",
    "ctdna",
    "her2",
    "egfr",
    "jak2",
    "pd-l1",
    "pdl1",
    "kras",
    "nsclc",
    "mutation",
    "cancer",
]


def classify_intent(query: str) -> str:
    q = query.lower()

    # Statistical must be checked first.
    # Example: "compare treatment groups by os" also contains "patients/study" sometimes.
    if any(keyword in q for keyword in STAT_KEYWORDS):
        return "statistical_analysis"

    # Biomarker research should catch explanation/scientific questions.
    if any(keyword in q for keyword in BIOMARKER_KEYWORDS):
        if any(word in q for word in ["what is", "explain", "summarize", "research", "latest"]):
            return "biomarker_research"

    # SQL handles structured database retrieval.
    if any(keyword in q for keyword in SQL_KEYWORDS):
        return "sql_query"

    # Biomarker fallback for scientific assistant behavior.
    if any(keyword in q for keyword in BIOMARKER_KEYWORDS):
        return "biomarker_research"

    return "biomarker_research"


INVALID_ATTEMPTS = {}


def route_query(query: str, session_id: str = "default"):
    validation = validate_user_query(query)

    if not validation["valid"]:
        current_attempts = INVALID_ATTEMPTS.get(session_id, 0) + 1
        INVALID_ATTEMPTS[session_id] = current_attempts

        attempts_remaining = 3 - current_attempts

        if current_attempts >= 3:
            INVALID_ATTEMPTS[session_id] = 0

            return {
                "intent": "invalid_query",
                "result": {
                    "agent": "query_guard_agent",
                    "message": "This query cannot be executed because it is unclear or outside the supported scope. Please enter a valid biomarker, SQL, or statistical query.",
                    "suggestions": [
                        "What is HER2 biomarker?",
                        "Show ctDNA records",
                        "Average OS by treatment group"
                    ]
                }
            }

        return {
            "intent": "clarification_required",
            "result": {
                "agent": "query_guard_agent",
                "message": validation["message"],
                "reason": validation["reason"],
                "suggestions": validation["suggestions"],
                "attempts_remaining": attempts_remaining
            }
        }

    INVALID_ATTEMPTS[session_id] = 0

    intent = classify_intent(query)

    if intent == "statistical_analysis":
        result = handle_statistical_query(query)
    elif intent == "sql_query":
        result = handle_sql_query(query)
    else:
        result = handle_biomarker_query(query)

    return {
        "intent": intent,
        "result": result
    }