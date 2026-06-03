import os
import re
from pathlib import Path

from dotenv import load_dotenv

from services.db_service import run_select_query
from services.llm_service import generate_response
from services.schema_service import get_database_schema
from services.sql_validator import validate_sql

load_dotenv()


def load_prompt() -> str:
    prompt_path = (
        Path(__file__)
        .resolve()
        .parents[1]
        / "prompts"
        / "sql_prompt.txt"
    )

    print("SQL PROMPT PATH:", prompt_path)

    with open(prompt_path, "r", encoding="utf-8") as file:
        return file.read()


def clean_sql_response(response: str) -> str:
    if not response or not response.strip():
        raise ValueError("LLM returned empty response.")

    text = response.strip()

    text = (
        text.replace("```sql", "")
        .replace("```SQL", "")
        .replace("```", "")
        .strip()
    )

    match = re.search(
        r"(SELECT[\s\S]*?;)",
        text,
        re.IGNORECASE,
    )

    if match:
        return match.group(1).strip()

    match = re.search(
        r"(SELECT[\s\S]*)",
        text,
        re.IGNORECASE,
    )

    if match:
        sql = match.group(1).strip()

        if not sql.endswith(";"):
            sql += ";"

        return sql

    raise ValueError(
        f"No SELECT query found in LLM response: {response}"
    )


def build_query_hint(user_query: str) -> str:
    q = user_query.lower()

    hints = []

    if "ctdna" in q or "vaf" in q or "mutation" in q:
        hints.append("Relevant table: bm_ctdna_vaf")
        hints.append(
            "Relevant columns: sampleid, param, vaf, mutation_status"
        )

    if "nanostring" in q or "gene" in q or "expression" in q:
        hints.append("Relevant table: bm_nanostring")
        hints.append(
            "Relevant columns: sampleid, param, count_raw, count_norm"
        )

    if (
        "patient" in q
        or "patients" in q
        or "os" in q
        or "pfs" in q
        or "treatment group" in q
        or "gender" in q
        or "region" in q
        or "dose" in q
        or "disease" in q
    ):
        hints.append("Relevant table: clinical_subjects")
        hints.append(
            "Relevant columns: subjectid, subjid, trtgrp, gender, region, disease, os, pfs, dose"
        )

    if (
        "clinical sample" in q
        or "sample type" in q
        or "sampletype" in q
        or "visit" in q
        or "qc" in q
    ):
        hints.append("Relevant table: clinical_samples")
        hints.append(
            "Relevant columns: sampleid, subjectid, sampletype, visitc, labdt, qc"
        )

    if (
        "shipped" in q
        or "shipment" in q
        or "assay" in q
        or "inventory" in q
        or "enrolled" in q
    ):
        hints.append("Relevant table: sample_inventory")
        hints.append(
            'Relevant columns: "SHIPPED_DATE", "SHIPPED_TO", "ASSAY_STATUS", '
            '"ASSAY_ANALYSIS_STATUS", "ASSAY_REASON_NOTDONE", "ENROLLED", "TREATMENT_GROUP"'
        )

    if "top" in q or "highest" in q or "maximum" in q or "max" in q:
        hints.append(
            "Operation: order by the relevant numeric column in descending order and use LIMIT 10"
        )

    if "lowest" in q or "minimum" in q or "min" in q:
        hints.append(
            "Operation: order by the relevant numeric column in ascending order and use LIMIT 10"
        )

    if "count" in q and " by " in q:
        hints.append("Operation: use COUNT(*) with GROUP BY")

    if "average" in q or "avg" in q or "mean" in q:
        hints.append(
            "Operation: use AVG() with GROUP BY if a grouping field is mentioned"
        )

    if "greater than" in q or ">" in q:
        hints.append("Operation: use WHERE with greater-than comparison")

    if "less than" in q or "<" in q:
        hints.append("Operation: use WHERE with less-than comparison")

    if not hints:
        return "No additional hint."

    return "\n".join(hints)


def build_prompt(user_query: str) -> str:
    prompt_template = load_prompt()
    database_schema = get_database_schema()
    query_hint = build_query_hint(user_query)

    return prompt_template.format(
        database_schema=database_schema,
        query_hint=query_hint,
        user_query=user_query,
    )


def generate_sql(user_query: str) -> str:
    prompt = build_prompt(user_query)

    model = os.getenv(
        "SQL_AGENT_MODEL",
        "qwen2.5-coder:1.5b",
    )

    response = generate_response(
        prompt=prompt,
        model=model,
        temperature=0.0,
        num_ctx=1024,
        num_predict=80,
        timeout=120,
    )

    print("\nQUERY HINT:")
    print(build_query_hint(user_query))

    print("\nRAW SQL LLM RESPONSE:")
    print(response)

    sql = clean_sql_response(response)

    print("\nCLEANED SQL:")
    print(sql)

    return sql


def correct_sql(
    user_query: str,
    invalid_sql: str,
    error_message: str,
) -> str:
    database_schema = get_database_schema()
    query_hint = build_query_hint(user_query)

    correction_prompt = f"""
You are a PostgreSQL SQL correction assistant.

The previous SQL was invalid.

User Query:
{user_query}

Query Hint:
{query_hint}

Invalid SQL:
{invalid_sql}

Validation or execution error:
{error_message}

Database Schema:
{database_schema}

Rules:
- Return only one corrected PostgreSQL SELECT query.
- The first word must be SELECT.
- End with semicolon.
- Do not explain.
- Do not use markdown.
- Do not add comments.
- Use only the schema provided.
- Use the Query Hint to choose the right table and operation.
- Do not invent tables or columns.
- Quote uppercase/mixed-case columns with double quotes.
- Add LIMIT 10 unless the query asks for count, average, sum, min, max, or grouped aggregation.

Corrected SQL:
"""

    model = os.getenv(
        "SQL_AGENT_MODEL",
        "qwen2.5-coder:1.5b",
    )

    response = generate_response(
        prompt=correction_prompt,
        model=model,
        temperature=0.0,
        num_ctx=1024,
        num_predict=80,
        timeout=120,
    )

    print("\nRAW SQL CORRECTION RESPONSE:")
    print(response)

    sql = clean_sql_response(response)

    print("\nCLEANED CORRECTED SQL:")
    print(sql)

    return sql


def handle_sql_query(user_query: str) -> dict:
    try:
        generated_sql = generate_sql(user_query)

        try:
            validate_sql(generated_sql)

        except Exception as validation_error:
            print(f"\nVALIDATION FAILED: {validation_error}")

            generated_sql = correct_sql(
                user_query=user_query,
                invalid_sql=generated_sql,
                error_message=str(validation_error),
            )

            validate_sql(generated_sql)

        try:
            results = run_select_query(generated_sql)

        except Exception as execution_error:
            print(f"\nEXECUTION FAILED: {execution_error}")

            generated_sql = correct_sql(
                user_query=user_query,
                invalid_sql=generated_sql,
                error_message=str(execution_error),
            )

            validate_sql(generated_sql)
            results = run_select_query(generated_sql)

        return {
            "agent": "sql_agent",
            "mode": "schema_grounded_text_to_sql",
            "status": "success",
            "generated_sql": generated_sql,
            "row_count": len(results),
            "results": results,
        }

    except Exception as error:
        return {
            "agent": "sql_agent",
            "mode": "schema_grounded_text_to_sql",
            "status": "failed",
            "message": "SQL Agent could not generate or execute a valid safe SELECT query.",
            "error": str(error),
            "suggestion": "Try a clearer database query such as show ctdna records, count patients by treatment group, or show top 10 ctdna mutations with highest vaf.",
        }