import re


FORBIDDEN_KEYWORDS = [
    "delete",
    "drop",
    "truncate",
    "update",
    "insert",
    "alter",
    "create"
]


ALLOWED_TABLES = [
    "clinical_subjects",
    "clinical_samples",
    "bm_ctdna_vaf",
    "bm_fc",
    "bm_nanostring",
    "sample_inventory"
]


def validate_sql(sql_query: str):
    lower_query = sql_query.lower().strip()

    for keyword in FORBIDDEN_KEYWORDS:
        if keyword in lower_query:
            raise ValueError(f"Forbidden SQL keyword detected: {keyword}")

    if not lower_query.startswith("select"):
        raise ValueError("Only SELECT queries are allowed.")

    # Block unknown tables after FROM or JOIN
    table_matches = re.findall(
        r"\b(?:from|join)\s+([a-zA-Z_][a-zA-Z0-9_]*)",
        lower_query
    )

    for table in table_matches:
        if table not in ALLOWED_TABLES:
            raise ValueError(f"Invalid or hallucinated table detected: {table}")

    return True