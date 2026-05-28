from pathlib import Path

from services.db_service import run_select_query
from services.llm_service import generate_response
from services.sql_validator import validate_sql


PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "sql_prompt.txt"


def load_prompt():

    with open(PROMPT_PATH, "r", encoding="utf-8") as file:
        return file.read()


def clean_sql_response(sql_text: str):

    sql_text = sql_text.strip()

    sql_text = sql_text.replace("```sql", "")
    sql_text = sql_text.replace("```", "")

    return sql_text.strip()


def handle_sql_query(user_query: str):

    prompt_template = load_prompt()

    final_prompt = prompt_template.format(
        user_query=user_query
    )

    generated_sql = generate_response(final_prompt)

    generated_sql = clean_sql_response(generated_sql)

    validate_sql(generated_sql)

    results = run_select_query(generated_sql)

    return {
        "agent": "sql_agent",
        "generated_sql": generated_sql,
        "results": results
    }