from agents.sql_agent import handle_sql_query
from agents.statistical_agent import handle_statistical_query
from agents.biomarker_agent import handle_biomarker_query

STAT_KEYWORDS = ["t-test", "anova", "correlation", "mean", "median", "regression", "compare statistically", "p-value"]
SQL_KEYWORDS = ["show", "list", "count", "how many", "top", "patients", "samples", "study", "enrollment"]
BIOMARKER_KEYWORDS = ["biomarker", "ctdna", "her2", "egfr", "jak2", "pd-l1", "kras", "nsclc", "mutation"]

def classify_intent(query: str) -> str:
    q = query.lower()
    if any(k in q for k in STAT_KEYWORDS):
        return "statistical_analysis"
    if any(k in q for k in SQL_KEYWORDS):
        return "sql_query"
    if any(k in q for k in BIOMARKER_KEYWORDS):
        return "biomarker_research"
    return "biomarker_research"

def route_query(query: str):
    intent = classify_intent(query)
    if intent == "sql_query":
        result = handle_sql_query(query)
    elif intent == "statistical_analysis":
        result = handle_statistical_query(query)
    else:
        result = handle_biomarker_query(query)
    return {"intent": intent, "result": result}
