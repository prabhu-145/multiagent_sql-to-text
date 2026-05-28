from sqlalchemy import text
from services.db_service import engine


def get_database_schema():

    query = """
    SELECT table_name, column_name
    FROM information_schema.columns
    WHERE table_schema = 'public'
    ORDER BY table_name;
    """

    with engine.connect() as connection:
        result = connection.execute(text(query))

        rows = result.fetchall()

    schema = {}

    for row in rows:

        table = row[0]
        column = row[1]

        if table not in schema:
            schema[table] = []

        schema[table].append(column)

    return schema