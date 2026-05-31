import re

from services.db_service import run_select_query
from services.sql_validator import validate_sql
from services.llm_service import generate_response


def load_prompt():
    with open("prompts/sql_prompt.txt", "r", encoding="utf-8") as file:
        return file.read()


def clean_sql_response(response: str) -> str:
    if not response:
        raise ValueError("LLM returned empty response")

    text = response.strip()

    text = text.replace("```sql", "")
    text = text.replace("```SQL", "")
    text = text.replace("```", "")
    text = text.strip()

    match = re.search(
        r"(SELECT[\s\S]*?;)",
        text,
        re.IGNORECASE
    )

    if match:
        return match.group(1).strip()

    match = re.search(
        r"(SELECT[\s\S]*)",
        text,
        re.IGNORECASE
    )

    if match:
        sql = match.group(1).strip()
        if not sql.endswith(";"):
            sql += ";"
        return sql

    raise ValueError(
        f"No valid SELECT query found in LLM response: {response}"
    )


def generate_corrected_sql(user_query: str, error_message: str) -> str:
    correction_prompt = f"""
You generated invalid SQL.

Error:
{error_message}

Original user query:
{user_query}

Allowed tables only:
clinical_subjects
clinical_samples
bm_ctdna_vaf
bm_fc
bm_nanostring
sample_inventory

Important mappings:
- ctDNA data means table bm_ctdna_vaf
- nanostring data means table bm_nanostring
- flow cytometry data means table bm_fc
- shipped samples means sample_inventory where "SHIPPED_DATE" IS NOT NULL
- assay failures means sample_inventory with assay failure columns

Return ONLY corrected PostgreSQL SELECT SQL.
The first word must be SELECT.
End with semicolon.
"""

    llm_response = generate_response(correction_prompt)

    print("RETRY RAW LLM SQL RESPONSE:")
    print(llm_response)

    corrected_sql = clean_sql_response(llm_response)

    print("RETRY CLEANED SQL:")
    print(corrected_sql)

    return corrected_sql


def handle_sql_query(user_query: str):
    try:
        prompt_template = load_prompt()

        final_prompt = prompt_template.format(
            user_query=user_query
        )

        llm_response = generate_response(final_prompt)

        print("RAW LLM SQL RESPONSE:")
        print(llm_response)

        try:
            generated_sql = clean_sql_response(llm_response)
        except Exception as error:
            generated_sql = generate_corrected_sql(
                user_query=user_query,
                error_message=str(error)
            )

        print("CLEANED SQL:")
        print(generated_sql)

        try:
            validate_sql(generated_sql)
        except Exception as error:
            generated_sql = generate_corrected_sql(
                user_query=user_query,
                error_message=str(error)
            )

            validate_sql(generated_sql)

        try:
            results = run_select_query(generated_sql)

        except Exception as error:
            generated_sql = generate_corrected_sql(
                user_query=user_query,
                error_message=str(error)
            )

            validate_sql(generated_sql)

            results = run_select_query(generated_sql)

        return {
            "agent": "sql_agent",
            "mode": "llm_generated_sql",
            "status": "success",
            "generated_sql": generated_sql,
            "results": results
        }

    except Exception as error:
        return {
            "agent": "sql_agent",
            "mode": "llm_generated_sql",
            "status": "failed",
            "message": "Unable to generate or execute valid SQL for this query.",
            "error": str(error),
            "suggestion": "Try asking with exact database terms such as: show ctDNA records, show shipped samples, show assay failures."
        }