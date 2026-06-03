import re

from services.schema_service import get_schema_dict


FORBIDDEN_KEYWORDS = [
    "delete",
    "drop",
    "truncate",
    "update",
    "insert",
    "alter",
    "create",
]


ALLOWED_TABLES = [
    "clinical_subjects",
    "clinical_samples",
    "bm_ctdna_vaf",
    "bm_fc",
    "bm_nanostring",
    "sample_inventory",
]


def extract_table_aliases(sql_query: str):
    aliases = {}

    pattern = (
        r"\b(?:from|join)\s+"
        r"([a-zA-Z_][a-zA-Z0-9_]*)"
        r"(?:\s+(?:as\s+)?([a-zA-Z_][a-zA-Z0-9_]*))?"
    )

    matches = re.findall(
        pattern,
        sql_query,
        flags=re.IGNORECASE,
    )

    for table_name, alias in matches:
        table_lower = table_name.lower()

        if table_lower not in ALLOWED_TABLES:
            raise ValueError(
                f"Unauthorized table access detected: {table_name}"
            )

        aliases[table_lower] = table_lower

        if alias:
            aliases[alias.lower()] = table_lower

    if not aliases:
        raise ValueError("No valid table found in SQL query.")

    return aliases


def validate_column_references(sql_query: str):
    schema = get_schema_dict()
    aliases = extract_table_aliases(sql_query)

    column_refs = re.findall(
        r"\b([a-zA-Z_][a-zA-Z0-9_]*)\.((?:\"[^\"]+\")|(?:[a-zA-Z_][a-zA-Z0-9_]*))",
        sql_query,
    )

    for alias, column in column_refs:
        alias_lower = alias.lower()

        if alias_lower not in aliases:
            raise ValueError(
                f"Unknown table alias detected: {alias}"
            )

        table_name = aliases[alias_lower]
        allowed_columns = schema.get(table_name, [])

        clean_column = column.replace('"', "")

        if clean_column not in allowed_columns:
            raise ValueError(
                f"Invalid column '{clean_column}' for table '{table_name}'."
            )

        if clean_column.isupper() and not column.startswith('"'):
            raise ValueError(
                f"Uppercase column '{clean_column}' must be wrapped in double quotes."
            )


def validate_quoted_columns(sql_query: str):
    schema = get_schema_dict()
    aliases = extract_table_aliases(sql_query)

    real_tables = list(set(aliases.values()))

    if len(real_tables) != 1:
        return

    table_name = real_tables[0]
    allowed_columns = schema.get(table_name, [])

    quoted_columns = re.findall(r'"([^"]+)"', sql_query)

    for column in quoted_columns:
        if column not in allowed_columns:
            raise ValueError(
                f"Invalid quoted column '{column}' for table '{table_name}'."
            )


def validate_sql(sql_query: str):
    if not sql_query:
        raise ValueError("Generated SQL is empty.")

    lower_query = sql_query.lower().strip()

    if not lower_query.startswith("select"):
        raise ValueError("Only SELECT queries are allowed.")

    for keyword in FORBIDDEN_KEYWORDS:
        pattern = rf"\b{keyword}\b"

        if re.search(pattern, lower_query):
            raise ValueError(
                f"Forbidden SQL keyword detected: {keyword}"
            )

    extract_table_aliases(sql_query)
    validate_column_references(sql_query)
    validate_quoted_columns(sql_query)

    return True