import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

BASE_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH)

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is missing. Please check your .env file.")

engine = create_engine(DATABASE_URL)


def run_select_query(sql_query: str):
    """
    Executes only SELECT queries and returns result as list of dictionaries.
    """

    if not sql_query.strip().lower().startswith("select"):
        raise ValueError("Only SELECT queries are allowed.")

    with engine.connect() as connection:
        result = connection.execute(text(sql_query))
        rows = result.fetchall()

        return [dict(row._mapping) for row in rows]