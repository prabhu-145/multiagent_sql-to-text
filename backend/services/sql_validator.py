FORBIDDEN_KEYWORDS = [
    "delete",
    "drop",
    "truncate",
    "update",
    "insert",
    "alter",
    "create"
]


def validate_sql(sql_query: str):

    lower_query = sql_query.lower()

    for keyword in FORBIDDEN_KEYWORDS:

        if keyword in lower_query:
            raise ValueError(
                f"Forbidden SQL keyword detected: {keyword}"
            )

    if not lower_query.strip().startswith("select"):
        raise ValueError(
            "Only SELECT queries are allowed."
        )

    return True