from sqlalchemy import text
from services.db_service import engine

# Restrict SQL Agent to project-approved tables only.
# This is not query hardcoding; this is table-level safety control.
ALLOWED_TABLES = [
    "clinical_subjects",
    "clinical_samples",
    "bm_ctdna_vaf",
    "bm_fc",
    "bm_nanostring",
    "sample_inventory",
]


def get_schema_dict() -> dict[str, list[str]]:
    query = """
        SELECT table_name, column_name
        FROM information_schema.columns
        WHERE table_schema = 'public'
        ORDER BY table_name, ordinal_position;
    """

    with engine.connect() as connection:
        rows = connection.execute(text(query)).fetchall()

    schema: dict[str, list[str]] = {}

    for table_name, column_name in rows:
        if table_name not in ALLOWED_TABLES:
            continue
        schema.setdefault(table_name, []).append(column_name)

    if not schema:
        raise RuntimeError(
            "No allowed tables found in PostgreSQL. Check DATABASE_URL and loaded tables."
        )

    return schema


def format_column(column_name: str) -> str:
    # PostgreSQL requires quotes for uppercase / mixed-case / special-character identifiers.
    if not column_name.islower() or not column_name.replace("_", "").isalnum():
        return f'"{column_name}"'
    return column_name


def get_database_schema() -> str:
    schema = get_schema_dict()
    lines: list[str] = []

    for table_name, columns in schema.items():
        formatted_columns = ", ".join(format_column(col) for col in columns)
        lines.append(f"Table: {table_name}")
        lines.append(f"Columns: {formatted_columns}")
        lines.append("")

    return "\n".join(lines).strip()
