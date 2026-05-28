from typing import Any, Dict, List, Optional, Union

from lifescience_prompts.constants import PROMPT_DETAILS
from lifescience_prompts.registry import PromptRegistry
from lifescience_prompts.types import ModelParams, PromptFormat, PromptResult

_SQL_PARAMS = ModelParams(temperature=0.1, max_tokens=4000, stop_sequences=("</SQL>",))
_VERIFICATION_PARAMS = ModelParams(temperature=0.1, max_tokens=500)


@PromptRegistry.register("sql.query", category="sql")
def sql_query_prompt(
    vector_search_metadata: str,
    sql_context_query: str,
    conversation_history: Union[str, List[Dict[str, str]]],
    user_query: str,
    study_name: str,
    vsim_baseline_json: Optional[Dict[str, Any]] = None,
    ebdm_baseline_json: Optional[Dict[str, Any]] = None,
    sample_dataframes: Optional[Dict[str, Any]] = None,
    columns: Optional[Dict[str, List[str]]] = None,
) -> PromptResult:
    """Generate MySQL query from natural language using RAG context."""
    if ebdm_baseline_json is None:
        ebdm_baseline_json = {}

    text = f"""\n\nHuman:
            🚨🚨🚨 CRITICAL SYSTEM REQUIREMENT 🚨🚨🚨
            BEFORE generating ANY SQL query, you MUST follow these absolute rules:

            ❌ FORBIDDEN - THESE WILL CAUSE SYSTEM FAILURE:
            1. NTILE() function → Breaks chart engine, NEVER use
            2. GROUP_CONCAT with SUBSTRING_INDEX for median → Mathematically incorrect
            3. PERCENTILE_CONT() function → NOT supported by MySQL (Oracle/SQL Server only), will cause SQL execution errors

            ✅ REQUIRED for median/percentiles:
            - ONLY use ROW_NUMBER() with AVG of middle values method (see instruction 52a for detailed examples)
            - DO NOT use PERCENTILE_CONT - it does not exist in MySQL
            - NO OTHER METHODS ARE ACCEPTABLE

            If you generate NTILE, GROUP_CONCAT, or PERCENTILE_CONT for median, the query will be REJECTED and you must regenerate.
            🚨🚨🚨 END CRITICAL REQUIREMENT 🚨🚨🚨

            <Instructions>
                Read the database schema inside the <database_schema></database_schema> tags, which contains a JSON list of table names and their pipe-delimited schemas, to do the following:
                1. Create a syntactically correct MySQL query to answer the question.
                2. Never query for all the columns from a specific table; only ask for a few relevant columns given the question.
                3. Pay attention to use only the column names that you can see in the schema description.
                4. Be careful not to query for columns that do not exist.
                5. Pay attention to which column is in which table.
                6. Qualify column names with the table name when needed. You are required to use the following format, each taking one line:
                7. Return the SQL query inside the <SQL></SQL> tag. follow this strictly.
                8. 🚫 CRITICAL: NEVER use NTILE() function - it breaks the chart engine. NEVER use GROUP_CONCAT with SUBSTRING_INDEX for median - it's mathematically wrong. NEVER use PERCENTILE_CONT (not supported by MySQL). For median/percentiles, ONLY use ROW_NUMBER method. This is MANDATORY and NON-NEGOTIABLE.
                9. Please give alias names for the columns and derived columns in the SQL query. Don't give large alias names.
                10. Please do not mention the word query in the SQL explanation part. For example, instead of 'The query aims', use 'The question aims to'.
                11. If the input is a greeting (such as 'Hi', 'Hello', etc.), respond with a polite greeting in return and offer assistance.
                12. Use the conversation history to answer follow-up questions, ensuring consistency and continuity with previous interactions. Extract and reuse relevant details to enhance the current response. Use the SQL query as reference accordingly in the previous question to answer follow-up questions.
                13. When generating SQL queries, always enclose every column name in backticks (`) to handle case sensitivity.
                14. Use the exact SQL query as it is if the user query is the same as in the {sql_context_query}. Follow this strictly.
                15. Pick the SQL query among the SQL queries which is most similar in meaning to the query in {sql_context_query} for the user query. Follow this strictly.
                16. Words like 'study', 'protocol' and 'project' refer to tables in the database.
                17. WHEN comparing string columns, USE "TRIM(<column_name>)" to remove leading and trailing spaces.
                18. YOU MUST USE "lower(<column_name>) = lower(<value>)" function for case-insensitive comparison!
                19. CAST non-string columns to strings when concatenating.
                21. If the user's query involves aging, generate SQL code that calculates the date difference between the current date and the date of the columns specified in user query. Return records in months or years.
                22. Don't consider the context_sql_query while answering follow-up questions instead alter the SQL query from the conversation_history to answer the user_query accordingly.
                23. Consider generating SQL query involving join condition across tables to bring up the appropriate response by altering the previous SQL query from conversation_history for answering follow-up question.
                24. Modify the latest SQL query for follow-ups: When answering follow-up questions, always start with the most recent SQL query from the conversation history.
                25. Normalize column name variations: Map user inputs with common variations (such as spaces, case differences, abbreviations, or synonyms) to the correct column names from the database schema. Ensure that the generated SQL query always uses the exact column names as they appear in the schema, even if the user's input differs in format or naming convention.
                26. Maintain row count in follow-up queries: When performing JOIN operations in follow-up questions, always include a GROUP BY clause with all selected columns to ensure the number of rows remains consistent with the previous response. This will prevent duplicate rows and maintain the same row count unless additional rows are logically added. Follow this strictly.
                27. You are currently in study: {study_name}, so when the user_query is related to study, keep this in context while answering.
                28. Date columns are stored as YYYY-MM-DD. So be careful while generating SQL queries which include Date columns. Even if the SQL query has other date formats in {sql_context_query}, consider the data format as YYYY-MM-DD. Follow this strictly.
                30. While answering follow-up questions, try to modify the SQL query from the previous question to maintain the context. It's not that only if keywords like 'above', 'add' can be considered as follow-up questions. A follow-up question can also be in response to the clarification asked for the previous query from conversation_history. So act accordingly in generating SQL queries. Follow this strictly.
                31. When the user_query is related to data available for a study, you have to list all the tables along with some table description of those tables for that study.
                32. Don't ask the user to involve the "fulfill" keyword in their response. Follow this strictly.
                33. **When generating SQL queries, ensure to handle quoted and non-quoted terms carefully.**
                34. If the user query contains terms in quotes (e.g., "term"), strip the quotes and use the `=` operator for exact matching.
                35. If the user query contains terms not in quotes (e.g.,term), use the `LIKE` operator with `%term%` for partial matching.
                36. If the user_query is a single word or incomplete and does not provide enough information to generate an SQL query, politely ask the user for clarification. Specify that the query is incomplete and explain what additional details are needed to proceed. Use the word 'fulfill' in your response when requesting clarification, but ensure the clarification is phrased in a way that the user understands what is missing or expected.
                37. While generating SQL queries, strictly use the DECIMAL data type instead of FLOAT. Ensure all numerical values are explicitly cast to DECIMAL, and specify an appropriate precision and scale to maintain accuracy and prevent rounding errors.
                38. When the user_query requests any information about a study—such as insights, details, data available, summaries, overviews, or descriptions—you must list all relevant tables for that study along with a brief description of each table. This applies to all generic study-focused queries, not only queries explicitly asking "what data is available."
        {PROMPT_DETAILS}
        </Instructions>
        <sample_dataframe>{sample_dataframes}</sample_dataframe>

        <database_schema>{vector_search_metadata}</database_schema>

        <vsim_details>{vsim_baseline_json}</vsim_details>

        <ebdm_details>{ebdm_baseline_json}</ebdm_details>

        <sql_context>{sql_context_query}</sql_context>

        <conversation_history>{conversation_history}</conversation_history>

        <Question>{user_query}</Question>
      Note:
    🚫🚫🚫 ABSOLUTE PROHIBITION: Do NOT generate SQL with NTILE() under ANY circumstances. Do NOT use GROUP_CONCAT with SUBSTRING_INDEX for median. Do NOT use PERCENTILE_CONT (not supported by MySQL). Your SQL will be REJECTED if it contains these. Use ONLY ROW_NUMBER method for median/percentiles. 🚫🚫🚫

    1)If the user query matches the question in sql_context_query, use the SQL query provided in sql_context_query as it is. Follow this instruction strictly without deviation.
    2)If essential details are missing, infer them from the provided schema. If infeasible, suggest potential tables and columns that may be relevant, guiding the user toward fulfillment without explicitly requesting table names or specific columns. Follow this strictly.
    3)Do not ask for clarification if the user_query is the same as in sql_context_query; just use it as it is without asking for clarification.
    4)Use the word "fulfill" in your response at all times. Do not ask the user to include "fulfill" in their response.
    5)If the user_query is related to data types, ask the user for clarification on whether it's related to data types available in the database or the description of any fields.
    7)If any table name in the SQL query from sql_context_query is not present in the database schema inside the <database_schema></database_schema> tags, do not use the SQL query. Even if the user_query matches a question in sql_context_query, respond with this exact message: "I cannot provide an answer for the given query due to insufficient data." Do not ask for clarification, do not use the word "fulfill," and do not suggest alternatives or provide additional explanations.
    8)If any table name in the SQL query from sql_context_query matches except for an additional word "view" in the base table name in database_schema, then use the SQL query from sql_context_query but alter the table name to match the database_schema.
    9)Ensure that the generated SQL query includes all relevant columns in the SELECT clause, including any key attributes mentioned in the user query, so that the result table provides complete and meaningful information. Follow this strictly.
    10)FILTER_CONDITIONS: Check if the search term is enclosed in double quotes ("term"). If the term is enclosed in quotes, strip the quotes and use the = operator for exact matching. If the term is not enclosed in quotes, use the LIKE operator with %term% for partial matching. Ensure that the query dynamically checks for the presence of quotes and applies the correct matching operator accordingly. Even if the user_query includes wording that suggests exact filtering, use the LIKE operator with %term%. Follow this strictly.
        Ensure that the quoted and non-quoted term handling is applied independently of the sql_context_query or conversation_history.
        Always check for quoted terms in the user query and apply the corresponding matching logic regardless of previous queries or conversation history.
    110Leverage the ebdm_details and vsim_details to generate precise SQL queries by incorporating study-specific baseline details, visit mappings, metadata, sample configurations, data source details, validation rules, plot parameters, and ensuring alignment with predefined schema and data relationships. Use joins with appropriate details from these sources to include conditions mentioned in the user_query.
    12)Do not consider the table name mentioned in the user_query because some tables in sql_context_query might have "view" in the table names. Always consider the table_name from database_schema while generating SQL queries.
    13)Cast to float type while handling numerical columns. Follow this strictly.
    14)Identify biological entities (e.g., genes, proteins) and infer relevant data types without requesting clarification.
    15)While asking for clarification, do not include 'This will help me generate a more accurate SQL query to fulfill your request.' Instead, use 'This will help clarify the request.' Follow this strictly.
    16)Do not include terms like "I'll need to generate an SQL query" or anything related to SQL generation in your response while asking for clarification. Follow this strictly.
    17)Use the exact SQL query from sql_context_query only if the user query exactly matches a question in sql_context_query.
    18)If the user_query and query in sql_context_query are different, generate an SQL query based on the column descriptions in database_schema. Ask for clarification only if the question is very ambiguous; otherwise, try to generate the query based on the schema. Do not ask for clarification for all questions.
    19)If  is a follow-up to a query in <conversation_history>, modify the SQL query to maintain continuity with the previous topic rather than treating it as an independent query.
    20)If the current query is a follow-up to a previous question, modify the SQL query from conversation history by adjusting only the necessary conditions based on the new question. Retain the base structure, tables, and joins used in the previous SQL query.
    21)When determining whether a query is a follow-up:
        If the follow-up lacks specific table or column references, infer them from the previous query rather than using unrelated SQL context.
        If the question is vague, lacks table/column references, or is a phrase rather than a full question, it is likely a follow-up.
        Identify if the new query shares key terms or context with the last question in conversation history.
        If a follow-up lacks sufficient information, prioritize conversation history over predefined SQL contexts to ensure relevance.
    22)Do not assume that similar keywords mean the same topic. If the new query lacks specific biomarker or table details, infer them from the last conversation instead of SQL context.
    23)If the follow-up question lacks a biomarker name but modifies a numeric condition, assume it applies to the last query's biomarker instead of switching contexts.
    24)Before using predefined SQL, check if the follow-up query modifies the last conversation history. If so, update the last SQL instead of selecting a new one from SQL context.
    25)When generating SQL queries, do not use user-defined variables (such as @variable_name or syntax like @row_num := @row_num). Avoid constructs involving session variables, manual counters, or variable assignment.
    26)DO NOT PREFER WITH statement for generating SQL query. Follow this strictly.
    27)Do not use FLOAT Datatype , instead use DECIMAL. follow this strictly.
    28)The SQL query must be generated strictly using the exact column names and their original case (UPPERCASE/lowercase) as they appear in the provided <sample_dataframe>.You are not allowed to assume, infer, or modify column names in any way.All column names must be directly extracted and matched exactly as they appear in the <sample_dataframe>, including letter casing.This rule also applies when reusing or modifying an existing SQL query from the {sql_context_query}.You must carefully scan the <sample_dataframe> and update all column references in the query to match the column names exactly.
    29)If the user is asking about available fields, columns, or structure of a table (for example, "show me all fields", "list columns", "what are the fields in table X"), you must generate an SQL query using the INFORMATION_SCHEMA.COLUMNS system table and use {study_name} as database name.follow this strictly.
    31)Use the {study_name} while generating sql queries involving database name.
    32)Avoid long subqueries, deeply nested expressions, or repeated calculations. Use temporary variables or intermediate steps only when necessary.
    33)Ensure the SQL query remains short and within reasonable length to prevent output truncation.
    34)Strictly verify the similarity between the user query and the provided {sql_context_query}. If the user query does not exactly match the sql_context_query, do not directly use the provided SQL query under any circumstances. Instead, always generate a SQL query based on the user query and conversation history also refer meta schema as well. This rule must be enforced without exception.
    35) Context-Aware Query Handling:
    When processing a user query, check if it contains context-dependent references such as:
        "these", "those", "them"
        "prior query", "previous result", "earlier selection"
        "subjects mentioned above", "identified earlier", or similar phrases
        If such references are present:
        ✅ Treat the current query as a follow-up to the immediately preceding user query found in <conversation_history>.
        ✅ do NOT default to or rely on <sql_context> unless the current user query is an exact match to the one in <sql_context>.
        ✅ The new SQL must reflect the context and constraints established by the last user query, modifying it logically based on the new ask.
        Strictly avoid:
        🚫 Starting a new unrelated SQL query unless the user's language clearly indicates a fresh, independent request.
    37) When selecting columns with the same name from different tables (e.g., subjectid, sampleid, id, etc.), you must always apply distinct and meaningful SQL aliases to each selected column. This is mandatory — failure to alias duplicate column names will cause downstream processing errors. For example, alias table1.subjectid as subjectid_1 and table2.subjectid as subjectid_2. Never include the same column name more than once in the SELECT clause without a unique alias.follow this strictly.
    38)When generating SQL queries, ensure that JOIN operations are performed using direct and meaningful relationships between tables—typically on columns that represent shared identifiers (e.g., subjectid, sampleid). Avoid using functions or transformations (like SUBSTRING, CAST, etc.) in join conditions unless the schema or data structure explicitly requires it. Always prefer clear, natural joins that align with the database schema.
    39)While generating sql queries, please add sample_id column if exist in the required table in select clause. Follow this strictly.
    40)Do not generate an SQL query if the user's question can be answered directly from the database schema metadata (e.g., questions asking about available endpoints, column names, or study definitions). Instead, return a structured summary based on the <database_schema> content.
    41)Assume 'clean data' means records that do not have any associated open queries.
    42)If the user query asks for location, prioritize using country-related columns if available (e.g., 'country', 'country_name'). If no such columns exist, use 'site_id' or similar site-level identifiers instead.
    43)Always format date fields to return values in 'YYYY-MM-DD' format instead of raw timestamps or epoch values.follow this stric    45)If the current user query is vague, generic, or lacks context, analyze the <conversation_history> to infer what the user is referring to. Use the most recent relevant query or topic to construct an appropriate SQL query .
    44)When constructing the WHERE clause, always determine the correct column strictly from database schema, using the column name and description to align with the user's intent. Do not select a column merely because the queried value happens to appear in sample_dataframes; those values are only illustrative samples. Column choice must be schema-driven, while filter values can extend beyond the sampled rows.
    45)If the current user query is vague, generic, or lacks context, analyze the <conversation_history> to infer what the user is referring to. Use the most recent relevant query or topic to construct an appropriate SQL query .
    46)When generating SQL queries with a != condition, always include a check for NULL values separately, such as column IS NULL OR column != 'value', because != alone does not match NULL values in SQL.
    47)If the query requests something unrealistic, impossible, or not logically valid calculations, do not attempt to fulfill with SQL or use sql_context examples, instead, respond clearly that the request cannot be processed with reason.Include the keyword fulfill in your response.
    48)Make all keywords, topics, and headers bold using Markdown syntax (e.g., **bold**) in your response.
    49)Include Markdown structural elements such as headings (using # symbols), unordered and ordered lists, blockquotes, horizontal rules, and definition lists in the response where applicable, formatted using Markdown syntax
    50)If the user's query mentions concepts such as "protocol deviation" (or any other term) that do not have an explicit column or table name in the provided schema, you must not infer, approximate, or rely on column descriptions, synonyms, or semantics. Do not generate any SQL in this case. Respond with fulfill keyword like no particular matching data.
    51)For any question involving only about samples, if the sample_inventory table is part of the SQL query, you must strictly use the column DERIVATIVEID instead of SAMPLEID. But if the question involves patient and sample_inventory table is also part of the SQL query, then you use SUBJID. Follow this strictly.
    52)Box Plot Statistical Components (Mandatory for Box Plot Requests):
        When a query requests a box plot or similar summary of distribution data, ensure that the following statistical components are included:
        Minimum: The smallest data point (excluding outliers).
        First Quartile (Q1): The median of the lower half of the data (25th percentile).
        Median (Q2): The middle value of the dataset (50th percentile).
        Third Quartile (Q3): The median of the upper half of the data (75th percentile).
        Maximum: The largest data point (excluding outliers).
        Optional but Commonly Included:
        Outliers: Data points below Q1 − 1.5×IQR or above Q3 + 1.5×IQR.
        Mean: Sometimes shown as a dot or line, though not part of the traditional box plot.
        Note:
        The Interquartile Range (IQR) is calculated as:
        IQR = Q3 − Q1
    52a)Median and Percentile Calculation (MANDATORY - Critical for Accuracy):
        ⚠️ CRITICAL WARNING: DO NOT USE GROUP_CONCAT with SUBSTRING_INDEX for median calculations! This method is INCORRECT and produces WRONG results for even-sized datasets.

        ❌ FORBIDDEN METHODS (DO NOT USE):
        - GROUP_CONCAT(... ORDER BY ...) with SUBSTRING_INDEX (INCORRECT for even counts)
        - AVG() alone without proper ranking (NOT a median)
        - Manual string concatenation approaches
        - NTILE() function (NOT supported by the chart engine)
        - PERCENTILE_CONT() function (NOT supported by MySQL - this is Oracle/SQL Server syntax only)

        ✅ When calculating median, quartiles, or any percentile values, you MUST use the following MySQL 8.0 compatible method:

        **ONLY CORRECT METHOD - Using Subquery with ROW_NUMBER:**

        For Median (50th percentile):
        SELECT AVG(median_value) AS median
        FROM (
            SELECT CAST(column_name AS DECIMAL(20,10)) AS median_value,
                   ROW_NUMBER() OVER (ORDER BY column_name) AS row_num,
                   COUNT(*) OVER () AS total_count
            FROM table_name
            WHERE column_name IS NOT NULL
        ) AS ranked
        WHERE row_num IN (FLOOR((total_count + 1) / 2), CEIL((total_count + 1) / 2));

        For Q1 (25th percentile):
        SELECT AVG(q1_value) AS q1
        FROM (
            SELECT CAST(column_name AS DECIMAL(20,10)) AS q1_value,
                   ROW_NUMBER() OVER (ORDER BY column_name) AS row_num,
                   COUNT(*) OVER () AS total_count
            FROM table_name
            WHERE column_name IS NOT NULL
        ) AS ranked
        WHERE row_num IN (FLOOR((total_count + 1) * 0.25), CEIL((total_count + 1) * 0.25));

        For Q3 (75th percentile):
        SELECT AVG(q3_value) AS q3
        FROM (
            SELECT CAST(column_name AS DECIMAL(20,10)) AS q3_value,
                   ROW_NUMBER() OVER (ORDER BY column_name) AS row_num,
                   COUNT(*) OVER () AS total_count
            FROM table_name
            WHERE column_name IS NOT NULL
        ) AS ranked
        WHERE row_num IN (FLOOR((total_count + 1) * 0.75), CEIL((total_count + 1) * 0.75));

        **Critical Rules for Median/Percentile Calculations:**
        a) Always use CAST(column_name AS DECIMAL(20,10)) before calculating percentiles to ensure numerical accuracy
        b) Always filter out NULL values using WHERE column_name IS NOT NULL before percentile calculations
        c) Always use ORDER BY column_name in the window function for proper ranking
        d) For grouped medians (e.g., by treatment arm, by visit), add the grouping column to the outer SELECT and include PARTITION BY in the ROW_NUMBER() window function
        e) Alias median as 'median' or 'q2', Q1 as 'q1' or 'first_quartile', Q3 as 'q3' or 'third_quartile'
        f) When user asks for "median", always calculate it using the ROW_NUMBER method - NEVER use AVG() or PERCENTILE_CONT as a substitute
        g) For distribution analysis, always include median alongside mean to provide complete statistical summary
        h) Handle edge cases: if dataset has even number of values, median should be average of two middle values (this is why we use AVG in the outer query)
        i) MANDATORY: Check your SQL before finalizing - if you see GROUP_CONCAT with SUBSTRING_INDEX, NTILE(), or PERCENTILE_CONT for median, REPLACE it with ROW_NUMBER method

        **Example - WRONG vs CORRECT Approach:**
        ❌ WRONG (DO NOT GENERATE THIS):
        SELECT param,
            CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(GROUP_CONCAT(cell_prop ORDER BY cell_prop SEPARATOR ','), ',', CEILING(COUNT(*)/2)), ',', -1) AS DECIMAL(10,4)) AS median
        FROM table_name GROUP BY param;

        ✅ CORRECT (USE THIS):
        SELECT param, AVG(median_value) AS median
        FROM (
            SELECT param,
                   CAST(cell_prop AS DECIMAL(20,10)) AS median_value,
                   ROW_NUMBER() OVER (PARTITION BY param ORDER BY cell_prop) AS row_num,
                   COUNT(*) OVER (PARTITION BY param) AS total_count
            FROM table_name
            WHERE cell_prop IS NOT NULL
        ) AS ranked
        WHERE row_num IN (FLOOR((total_count + 1) / 2), CEIL((total_count + 1) / 2))
        GROUP BY param;

        **Example for Complete Box Plot Query:**
        SELECT
            MIN(CAST(value_column AS DECIMAL(20,10))) AS minimum,
            (SELECT AVG(q1_value) FROM (
                SELECT CAST(value_column AS DECIMAL(20,10)) AS q1_value,
                       ROW_NUMBER() OVER (ORDER BY value_column) AS row_num,
                       COUNT(*) OVER () AS total_count
                FROM table_name WHERE value_column IS NOT NULL
            ) AS q1_ranked WHERE row_num IN (FLOOR((total_count + 1) * 0.25), CEIL((total_count + 1) * 0.25))) AS q1,
            (SELECT AVG(median_value) FROM (
                SELECT CAST(value_column AS DECIMAL(20,10)) AS median_value,
                       ROW_NUMBER() OVER (ORDER BY value_column) AS row_num,
                       COUNT(*) OVER () AS total_count
                FROM table_name WHERE value_column IS NOT NULL
            ) AS median_ranked WHERE row_num IN (FLOOR((total_count + 1) / 2), CEIL((total_count + 1) / 2))) AS median,
            (SELECT AVG(q3_value) FROM (
                SELECT CAST(value_column AS DECIMAL(20,10)) AS q3_value,
                       ROW_NUMBER() OVER (ORDER BY value_column) AS row_num,
                       COUNT(*) OVER () AS total_count
                FROM table_name WHERE value_column IS NOT NULL
            ) AS q3_ranked WHERE row_num IN (FLOOR((total_count + 1) * 0.75), CEIL((total_count + 1) * 0.75))) AS q3,
            MAX(CAST(value_column AS DECIMAL(20,10))) AS maximum,
            AVG(CAST(value_column AS DECIMAL(20,10))) AS mean
        FROM table_name
        WHERE value_column IS NOT NULL;

        Follow these instructions strictly to ensure accurate median and percentile calculations.
    53)If the user query explicitly mentions the term 'samples', always include and reference the sampleid column (or the table's corresponding sample-related column) in the generated SQL query.
    54)All clarification messages and all responses to user queries must mandatorily contain the keyword 'fulfill'. Do not generate any reply without this keyword.follow this strictly
    55)If the user's question is about the study baseline (e.g., 'what is baseline for this study' or any query asking for baseline definition), do NOT generate SQL. Instead, respond using the 'fulfill' keyword and return the baseline details exactly as provided in the
    56)Strictly validate the similarity between the user query and the provided {sql_context_query}.if the user query exactly matches the {sql_context_query}. In such cases, use the same SQL query without modification, except that baseline-related details must be inferred exclusively from vsim_details and ebdm_details, and not from the {sql_context_query}.

    Note: you need to to strictly use the column names in {columns} while generating sql query no matter wether you are going generate sq_query for a new question or going to use sql_query from the {sql_context_query}.follow this strictly.

    Assistant:"""

    return PromptResult(text=text, model_params=_SQL_PARAMS, format=PromptFormat.CLAUDE)


@PromptRegistry.register("sql.statistical_query", category="sql")
def statistical_query_prompt(
    vector_search_metadata: str,
    sql_context_query: str,
    conversation_history: Union[str, List[Dict[str, str]]],
    user_query: str,
    study_name: str,
    vsim_baseline_json: Optional[Dict[str, Any]] = None,
    ebdm_baseline_json: Optional[Dict[str, Any]] = None,
    sample_dataframes: Optional[Dict[str, Any]] = None,
    columns: Optional[Dict[str, List[str]]] = None,
) -> PromptResult:
    """Generate statistical SQL query from natural language using RAG context."""
    if ebdm_baseline_json is None:
        ebdm_baseline_json = {}

    text = f"""\n\nHuman:
            🚨🚨🚨 CRITICAL SYSTEM REQUIREMENT 🚨🚨🚨
            BEFORE generating ANY SQL query, you MUST follow these absolute rules:

            ❌ FORBIDDEN - THESE WILL CAUSE SYSTEM FAILURE:
            1. NTILE() function → Breaks chart engine, NEVER use
            2. GROUP_CONCAT with SUBSTRING_INDEX for median → Mathematically incorrect
            3. PERCENTILE_CONT() function → NOT supported by MySQL (Oracle/SQL Server only), will cause SQL execution errors

            ✅ REQUIRED for median/percentiles (ESPECIALLY FOR STATISTICAL QUERIES):
            - ONLY use ROW_NUMBER() with AVG of middle values method (see instruction 62a for detailed examples)
            - DO NOT use PERCENTILE_CONT - it does not exist in MySQL
            - NO OTHER METHODS ARE ACCEPTABLE

            Statistical accuracy depends on correct median calculation. NTILE, GROUP_CONCAT, and PERCENTILE_CONT produce WRONG results or SQL errors.
            If you generate NTILE, GROUP_CONCAT, or PERCENTILE_CONT for median, the query will be REJECTED and you must regenerate.
            🚨🚨🚨 END CRITICAL REQUIREMENT 🚨🚨🚨

            <Instructions>
                Read the database schema inside the <database_schema></database_schema> tags, which contains a JSON list of table names and their pipe-delimited schemas, to do the following:
                1. Create a syntactically correct MySQL query to answer the question.
                2. Never query for all the columns from a specific table; only ask for a few relevant columns given the question.
                3. Pay attention to use only the column names that you can see in the schema description.
                4. Be careful not to query for columns that do not exist.
                5. Pay attention to which column is in which table.
                6. Qualify column names with the table name when needed. You are required to use the following format, each taking one line:
                7. Return the SQL query inside the <SQL></SQL> tag. follow this strictly.
                8. 🚫 CRITICAL: NEVER use NTILE() function - it breaks the chart engine. NEVER use GROUP_CONCAT with SUBSTRING_INDEX for median - it's mathematically wrong. NEVER use PERCENTILE_CONT (not supported by MySQL). For median/percentiles, ONLY use ROW_NUMBER method. This is MANDATORY and NON-NEGOTIABLE.
                9. Please give alias names for the columns and derived columns in the SQL query. Don't give large alias names.
                10. Please do not mention the word query in the SQL explanation part. For example, instead of 'The query aims', use 'The question aims to'.
                11. If the input is a greeting (such as 'Hi', 'Hello', etc.), respond with a polite greeting in return and offer assistance.
                12. Use the conversation history to answer follow-up questions, ensuring consistency and continuity with previous interactions. Extract and reuse relevant details to enhance the current response. Use the SQL query as reference accordingly in the previous question to answer follow-up questions.
                13. When generating SQL queries, always enclose every column name in backticks (`) to handle case sensitivity.
                14. Use the exact SQL query as it is if the user query is the same as in the {sql_context_query}. Follow this strictly.
                15. Pick the SQL query among the SQL queries which is most similar in meaning to the query in {sql_context_query} for the user query. Follow this strictly.
                16. Words like 'study', 'protocol' and 'project' refer to tables in the database.
                17. WHEN comparing string columns, USE "TRIM(<column_name>)" to remove leading and trailing spaces.
                18. YOU MUST USE "lower(<column_name>) = lower(<value>)" function for case-insensitive comparison!
                19. CAST non-string columns to strings when concatenating.
                21. If the user's query involves aging, generate SQL code that calculates the date difference between the current date and the date of the columns specified in user query. Return records in months or years.
                22. Don't consider the context_sql_query while answering follow-up questions instead alter the SQL query from the conversation_history to answer the user_query accordingly.
                23. Consider generating SQL query involving join condition across tables to bring up the appropriate response by altering the previous SQL query from conversation_history for answering follow-up question.
                24. Modify the latest SQL query for follow-ups: When answering follow-up questions, always start with the most recent SQL query from the conversation history.
                25. Normalize column name variations: Map user inputs with common variations (such as spaces, case differences, abbreviations, or synonyms) to the correct column names from the database schema. Ensure that the generated SQL query always uses the exact column names as they appear in the schema, even if the user's input differs in format or naming convention.
                26. Maintain row count in follow-up queries: When performing JOIN operations in follow-up questions, always include a GROUP BY clause with all selected columns to ensure the number of rows remains consistent with the previous response. This will prevent duplicate rows and maintain the same row count unless additional rows are logically added. Follow this strictly.
                27. You are currently in study: {study_name}, so when the user_query is related to study, keep this in context while answering.
                28. Date columns are stored as YYYY-MM-DD. So be careful while generating SQL queries which include Date columns. Even if the SQL query has other date formats in {sql_context_query}, consider the data format as YYYY-MM-DD. Follow this strictly.
                30. While answering follow-up questions, try to modify the SQL query from the previous question to maintain the context. It's not that only if keywords like 'above', 'add' can be considered as follow-up questions. A follow-up question can also be in response to the clarification asked for the previous query from conversation_history. So act accordingly in generating SQL queries. Follow this strictly.
                31. When the user_query is related to data available for a study, you have to list all the tables along with some table description of those tables for that study.
                32. Don't ask the user to involve the "fulfill" keyword in their response. Follow this strictly.
                33. **When generating SQL queries, ensure to handle quoted and non-quoted terms carefully.**
                34. If the user query contains terms in quotes (e.g., "term"), strip the quotes and use the `=` operator for exact matching.
                35. If the user query contains terms not in quotes (e.g.,term), use the `LIKE` operator with `%term%` for partial matching.
                36. If the user_query is a single word or incomplete and does not provide enough information to generate an SQL query, politely ask the user for clarification. Specify that the query is incomplete and explain what additional details are needed to proceed. Use the word 'fulfill' in your response when requesting clarification, but ensure the clarification is phrased in a way that the user understands what is missing or expected.
                37. While generating SQL queries, strictly use the DECIMAL data type instead of FLOAT. Ensure all numerical values are explicitly cast to DECIMAL, and specify an appropriate precision and scale to maintain accuracy and prevent rounding errors.
                38. For statistical questions such as correlations, t-tests, ANOVA, and standard deviation, generate valid and optimized compatible SQL queries using aggregate functions, CASE statements, and joins where applicable. For chi-square tests, follow instruction 45 instead.
                39. For Pearson correlation between two numeric columns `x` and `y`, use the following formula:
                    (COUNT(*) * SUM(x * y) - SUM(x) * SUM(y)) /
                    (SQRT(COUNT(*) * SUM(x * x) - POWER(SUM(x), 2)) *
                    SQRT(COUNT(*) * SUM(y * y) - POWER(SUM(y), 2)))
                    Replace `x` and `y` with actual column names.
                40. For Point-Biserial correlation (one binary column and one numeric), treat the binary column as 0/1 and apply the same Pearson correlation formula. Ensure data is not NULL.
                41. For Spearman correlation:
                    a. First rank both variables using a derived table or subquery.
                    b. Then apply the Pearson correlation formula on the rank values.
                42. For Kendall's Tau, use:
                    (Number of concordant pairs - Number of discordant pairs) /
                    (0.5 * n * (n - 1))
                    If pairwise comparisons are too complex, state: "Kendall's Tau requires advanced pairwise logic not supported in SQL natively."
                43. For Phi Coefficient (binary-binary correlation), use:
                    (AD - BC) / SQRT((A+B)(C+D)(A+C)(B+D))
                    where A, B, C, D are frequencies in the 2x2 contingency table.
                44. For Cramer's V (nominal association from chi-square), use:
                    SQRT(chi_square / (n * (min(k-1, r-1))))
                    where `k` = number of columns, `r` = number of rows in contingency table. First calculate the chi-square statistic using observed vs expected counts.
                45. For Chi-square test (independence / 2x2 contingency table):
                    a. Generate ONLY a simple crosstab frequency query using GROUP BY.
                    b. Return exactly three columns: the row variable, the column variable, and COUNT(*) AS freq.
                    c. Use the database_schema to identify the correct table and column names that match the user's query.
                       Replace example column names with ACTUAL column names from the schema. NEVER output placeholder
                       or template SQL with comments like "specify the correct table name" -- always generate executable SQL.
                    d. Filter out NULL values in both columns using WHERE ... IS NOT NULL.
                    e. Both variables MUST be binary (exactly 2 categories each) for a valid 2x2 chi-square test.
                       If either variable has more than 2 categories, respond with clarification asking the user
                       to specify which two categories to compare, or suggest using Cramer's V instead.
                    f. Add a SQL comment on the FIRST line: -- STATS_TYPE: CHI_SQUARE
                    g. The chi-square statistic, expected frequencies, and p-value will be computed by the application
                       using scipy. Do NOT calculate these in SQL.
                    h. Do NOT pivot the data with CASE WHEN -- return it in long/stacked format with three columns only.
                    i. Pattern (replace placeholders with actual schema column and table names):
                       -- STATS_TYPE: CHI_SQUARE
                       SELECT `<row_column>`, `<col_column>`, COUNT(*) AS freq
                       FROM `<table_name>`
                       WHERE `<row_column>` IS NOT NULL AND `<col_column>` IS NOT NULL
                       GROUP BY `<row_column>`, `<col_column>`
                46. For one-sample t-test:
                    t = (sample_mean - population_mean) / (sample_stddev / SQRT(n))
                    Require user to provide the population_mean.
                47. For two-sample t-test:
                    t = (mean1 - mean2) / SQRT((s1^2 / n1) + (s2^2 / n2))
                    where s1, s2 = standard deviations of each group, and n1, n2 = their counts.
                48. For paired t-test:
                    a. Compute difference = value1 - value2
                    b. t = mean(diff) / (stddev(diff) / SQRT(n))
                49. For Z-test:
                    z = (sample_mean - population_mean) / (population_stddev / SQRT(n))
                    Require population parameters to be known or passed.
                50. For ANOVA (one-way):
                    a. Calculate group means, grand mean, count of rows per group.
                    b. Between-group SS (SSB) = SUM(n_i * (mean_i - grand_mean)^2)
                    c. Within-group SS (SSW) = SUM((x - mean_i)^2)
                    d. F = (SSB / (k - 1)) / (SSW / (n - k))
                    e. Alias the F-statistic result as f_stat
                51. For MANOVA, respond: "MANOVA requires multivariate matrix operations not supported in SQL directly."
                52. For F-test (variance comparison):
                    F = variance1 / variance2
                    Compute sample variances using VAR_SAMP() or manual method.
                53. For standard deviation and variance:
                    a. STDDEV = SQRT(SUM(POW(x - mean, 2)) / (n - 1))
                    b. Use STDDEV_SAMP() or VAR_SAMP() if available
                54. For hypothesis testing questions:
                    a. For chi-square tests, generate ONLY the crosstab query (see instruction 45).
                       The p-value and test statistic are computed exactly by the application using scipy.
                    b. For other test statistics (z, t, F), compute them in SQL.
                       Mention that exact p-values for these tests require external statistical tools unless approximated.
                55. For Power Analysis or Type I / Type II error calculations, respond:
                    "Power analysis and error rate calculations require statistical modeling and distribution assumptions not supported natively in SQL."
                56. Always alias computed values such as mean, stddev, t_stat, correlation_score, chi_stat, or f_stat to improve result clarity.
                58. If the question requests more than one statistical calculation, ensure the SQL query includes all requested calculations in the same result set or as separate columns.
                59. Generate SQL for linear regression only if the query involves two or more biomarker variables. If fewer than two biomarkers are mentioned, respond only with the fulfill keyword that "Linear regression can be performed only if two or more biomarker variables are involved".do not add explanations, clarifications, or follow-up questions.do add fulfill keyword in your response.
                60. For Pearson correlation, generate SQL only if exactly two biomarker variables are mentioned; otherwise, respond only with the fulfill keyword that "Pearson correlation can be performed only if exactly two biomarker variables are involved".do not add explanations, clarifications, or follow-up questions.do add fulfill keyword in your response.
                61. If the user's query requests distribution-related analysis (e.g., asks for the distribution of a variable, biomarker, or value), automatically include mean, median, and mode as part of the response or SQL/statistical computation — even if not explicitly mentioned.
                62.Box Plot Statistical Components (Mandatory for Box Plot Requests):
                    When a query requests a box plot or similar summary of distribution data, ensure that the following statistical components are included:
                    Minimum: The smallest data point (excluding outliers).
                    First Quartile (Q1): The median of the lower half of the data (25th percentile).
                    Median (Q2): The middle value of the dataset (50th percentile).
                    Third Quartile (Q3): The median of the upper half of the data (75th percentile).
                    Maximum: The largest data point (excluding outliers).
                    Optional but Commonly Included:
                    Outliers: Data points below Q1 − 1.5×IQR or above Q3 + 1.5×IQR.
                    Mean: Sometimes shown as a dot or line, though not part of the traditional box plot.
                    Note:
                    The Interquartile Range (IQR) is calculated as:
                    IQR = Q3 − Q1
                62a.Median and Percentile Calculation (MANDATORY - Critical for Statistical Accuracy):
                    WARNING: DO NOT USE GROUP_CONCAT with SUBSTRING_INDEX for median calculations! This method is INCORRECT and produces WRONG results for even-sized datasets, which will compromise statistical analysis.

                    FORBIDDEN METHODS (DO NOT USE):
                    - GROUP_CONCAT(... ORDER BY ...) with SUBSTRING_INDEX (MATHEMATICALLY INCORRECT for even counts)
                    - AVG() alone without proper ranking (NOT a median - will give incorrect statistical results)
                    - Manual string concatenation approaches (unreliable and limited)
                    - NTILE() function (NOT supported by the chart engine - causes rendering failures)
                    - PERCENTILE_CONT() function (NOT supported by MySQL - this is Oracle/SQL Server syntax only)

                    When calculating median, quartiles, or any percentile values, you MUST use the following MySQL 8.0 compatible method:

                    **ONLY CORRECT METHOD - Using Subquery with ROW_NUMBER:**

                    For Median (50th percentile):
                    SELECT AVG(median_value) AS median
                    FROM (
                        SELECT CAST(column_name AS DECIMAL(20,10)) AS median_value,
                               ROW_NUMBER() OVER (ORDER BY column_name) AS row_num,
                               COUNT(*) OVER () AS total_count
                        FROM table_name
                        WHERE column_name IS NOT NULL
                    ) AS ranked
                    WHERE row_num IN (FLOOR((total_count + 1) / 2), CEIL((total_count + 1) / 2));

                    For Q1 (25th percentile):
                    SELECT AVG(q1_value) AS q1
                    FROM (
                        SELECT CAST(column_name AS DECIMAL(20,10)) AS q1_value,
                               ROW_NUMBER() OVER (ORDER BY column_name) AS row_num,
                               COUNT(*) OVER () AS total_count
                        FROM table_name
                        WHERE column_name IS NOT NULL
                    ) AS ranked
                    WHERE row_num IN (FLOOR((total_count + 1) * 0.25), CEIL((total_count + 1) * 0.25));

                    For Q3 (75th percentile):
                    SELECT AVG(q3_value) AS q3
                    FROM (
                        SELECT CAST(column_name AS DECIMAL(20,10)) AS q3_value,
                               ROW_NUMBER() OVER (ORDER BY column_name) AS row_num,
                               COUNT(*) OVER () AS total_count
                        FROM table_name
                        WHERE column_name IS NOT NULL
                    ) AS ranked
                    WHERE row_num IN (FLOOR((total_count + 1) * 0.75), CEIL((total_count + 1) * 0.75));

                    **Critical Rules for Median/Percentile Calculations:**
                    a) Always use CAST(column_name AS DECIMAL(20,10)) before calculating percentiles to ensure numerical accuracy
                    b) Always filter out NULL values using WHERE column_name IS NOT NULL before percentile calculations
                    c) Always use ORDER BY column_name in the window function for proper ranking
                    d) For grouped medians (e.g., by treatment arm, by visit), add the grouping column to the outer SELECT and include PARTITION BY in the ROW_NUMBER() window function
                    e) Alias median as 'median' or 'q2', Q1 as 'q1' or 'first_quartile', Q3 as 'q3' or 'third_quartile'
                    f) When user asks for "median", always calculate it using the ROW_NUMBER method - NEVER use AVG() or PERCENTILE_CONT as a substitute
                    g) For distribution analysis, always include median alongside mean to provide complete statistical summary
                    h) Handle edge cases: if dataset has even number of values, median should be average of two middle values (this is why we use AVG in the outer query)
                    i) For statistical queries involving median in hypothesis testing or descriptive statistics, ensure accurate calculation as it's critical for data interpretation
                    j) When comparing medians between groups (e.g., Mann-Whitney U test context), calculate group-specific medians using PARTITION BY in the ROW_NUMBER() function
                    k) MANDATORY SELF-CHECK: Before finalizing your SQL, verify it does NOT contain GROUP_CONCAT with SUBSTRING_INDEX, NTILE(), or PERCENTILE_CONT for median - if it does, REPLACE it immediately with ROW_NUMBER method

                    **Example - WRONG vs CORRECT Approach for Statistical Queries:**
                    WRONG (DO NOT GENERATE - This will produce incorrect statistical results):
                    SELECT param,
                        CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(GROUP_CONCAT(cell_prop ORDER BY cell_prop SEPARATOR ','), ',', CEILING(COUNT(*)/2)), ',', -1) AS DECIMAL(10,4)) AS median_cell_prop
                    FROM bm_fc GROUP BY param;

                    CORRECT (USE THIS for accurate statistical analysis):
                    SELECT param, AVG(median_value) AS median_cell_prop
                    FROM (
                        SELECT param,
                               CAST(cell_prop AS DECIMAL(20,10)) AS median_value,
                               ROW_NUMBER() OVER (PARTITION BY param ORDER BY cell_prop) AS row_num,
                               COUNT(*) OVER (PARTITION BY param) AS total_count
                        FROM bm_fc
                        WHERE cell_prop IS NOT NULL
                    ) AS ranked
                    WHERE row_num IN (FLOOR((total_count + 1) / 2), CEIL((total_count + 1) / 2))
                    GROUP BY param;

                    **Example for Complete Box Plot Query:**
                    SELECT
                        MIN(CAST(value_column AS DECIMAL(20,10))) AS minimum,
                        (SELECT AVG(q1_value) FROM (
                            SELECT CAST(value_column AS DECIMAL(20,10)) AS q1_value,
                                   ROW_NUMBER() OVER (ORDER BY value_column) AS row_num,
                                   COUNT(*) OVER () AS total_count
                            FROM table_name WHERE value_column IS NOT NULL
                        ) AS q1_ranked WHERE row_num IN (FLOOR((total_count + 1) * 0.25), CEIL((total_count + 1) * 0.25))) AS q1,
                        (SELECT AVG(median_value) FROM (
                            SELECT CAST(value_column AS DECIMAL(20,10)) AS median_value,
                                   ROW_NUMBER() OVER (ORDER BY value_column) AS row_num,
                                   COUNT(*) OVER () AS total_count
                            FROM table_name WHERE value_column IS NOT NULL
                        ) AS median_ranked WHERE row_num IN (FLOOR((total_count + 1) / 2), CEIL((total_count + 1) / 2))) AS median,
                        (SELECT AVG(q3_value) FROM (
                            SELECT CAST(value_column AS DECIMAL(20,10)) AS q3_value,
                                   ROW_NUMBER() OVER (ORDER BY value_column) AS row_num,
                                   COUNT(*) OVER () AS total_count
                            FROM table_name WHERE value_column IS NOT NULL
                        ) AS q3_ranked WHERE row_num IN (FLOOR((total_count + 1) * 0.75), CEIL((total_count + 1) * 0.75))) AS q3,
                        MAX(CAST(value_column AS DECIMAL(20,10))) AS maximum,
                        AVG(CAST(value_column AS DECIMAL(20,10))) AS mean,
                        STDDEV(CAST(value_column AS DECIMAL(20,10))) AS stddev
                    FROM table_name
                    WHERE value_column IS NOT NULL;

                    **Example for Grouped Statistical Summary with Median:**
                    SELECT
                        group_column,
                        COUNT(*) AS n,
                        AVG(CAST(value_column AS DECIMAL(20,10))) AS mean,
                        (SELECT AVG(median_value)
                         FROM (
                             SELECT CAST(value_column AS DECIMAL(20,10)) AS median_value,
                                    ROW_NUMBER() OVER (PARTITION BY group_column ORDER BY value_column) AS row_num,
                                    COUNT(*) OVER (PARTITION BY group_column) AS total_count
                             FROM table_name
                             WHERE value_column IS NOT NULL
                         ) AS median_calc
                         WHERE row_num IN (FLOOR((total_count + 1) / 2), CEIL((total_count + 1) / 2))
                         AND median_calc.group_column = table_name.group_column) AS median,
                        STDDEV(CAST(value_column AS DECIMAL(20,10))) AS stddev,
                        MIN(CAST(value_column AS DECIMAL(20,10))) AS min_val,
                        MAX(CAST(value_column AS DECIMAL(20,10))) AS max_val
                    FROM table_name
                    WHERE value_column IS NOT NULL
                    GROUP BY group_column;

                    Follow these instructions strictly to ensure accurate median and percentile calculations in all statistical analyses.
        {PROMPT_DETAILS}
        </Instructions>
        <sample_dataframe>{sample_dataframes}</sample_dataframe>

        <database_schema>{vector_search_metadata}</database_schema>

        <vsim_details>{vsim_baseline_json}</vsim_details>

        <ebdm_details>{ebdm_baseline_json}</ebdm_details>

        <sql_context>{sql_context_query}</sql_context>

        <conversation_history>{conversation_history}</conversation_history>

        <Question>{user_query}</Question>
      Note:
    🚫🚫🚫 ABSOLUTE PROHIBITION: Do NOT generate SQL with NTILE() under ANY circumstances. Do NOT use GROUP_CONCAT with SUBSTRING_INDEX for median. Do NOT use PERCENTILE_CONT (not supported by MySQL). Your SQL will be REJECTED if it contains these. Use ONLY ROW_NUMBER method for median/percentiles. 🚫🚫🚫

    1)If the user query matches the question in sql_context_query, use the SQL query provided in sql_context_query as it is. Follow this instruction strictly without deviation.
    2)If essential details are missing, infer them from the provided schema. If infeasible, suggest potential tables and columns that may be relevant, guiding the user toward fulfillment without explicitly requesting table names or specific columns. Follow this strictly.
    3)Do not ask for clarification if the user_query is the same as in sql_context_query; just use it as it is without asking for clarification.
    4)Use the word "fulfill" in your response at all times. Do not ask the user to include "fulfill" in their response.
    5)If the user_query is related to data types, ask the user for clarification on whether it's related to data types available in the database or the description of any fields.
    8)If any table name in the SQL query from sql_context_query matches except for an additional word "view" in the base table name in database_schema, then use the SQL query from sql_context_query but alter the table name to match the database_schema.
    9)Ensure that the generated SQL query includes all relevant columns in the SELECT clause, including any key attributes mentioned in the user query, so that the result table provides complete and meaningful information. Follow this strictly.
    10)FILTER_CONDITIONS: Check if the search term is enclosed in double quotes ("term"). If the term is enclosed in quotes, strip the quotes and use the = operator for exact matching. If the term is not enclosed in quotes, use the LIKE operator with %term% for partial matching. Ensure that the query dynamically checks for the presence of quotes and applies the correct matching operator accordingly. Even if the user_query includes wording that suggests exact filtering, use the LIKE operator with %term%. Follow this strictly.
        Ensure that the quoted and non-quoted term handling is applied independently of the sql_context_query or conversation_history.
        Always check for quoted terms in the user query and apply the corresponding matching logic regardless of previous queries or conversation history.
    110Leverage the ebdm_details and vsim_details to generate precise SQL queries by incorporating study-specific baseline details, visit mappings, metadata, sample configurations, data source details, validation rules, plot parameters, and ensuring alignment with predefined schema and data relationships. Use joins with appropriate details from these sources to include conditions mentioned in the user_query.
    12)Do not consider the table name mentioned in the user_query because some tables in sql_context_query might have "view" in the table names. Always consider the table_name from database_schema while generating SQL queries.
    13)Cast to float type while handling numerical columns. Follow this strictly.
    14)Identify biological entities (e.g., genes, proteins) and infer relevant data types without requesting clarification.
    15)While asking for clarification, do not include 'This will help me generate a more accurate SQL query to fulfill your request.' Instead, use 'This will help clarify the request.' Follow this strictly.
    16)Do not include terms like "I'll need to generate an SQL query" or anything related to SQL generation in your response while asking for clarification. Follow this strictly.
    17)Use the exact SQL query from sql_context_query only if the user query exactly matches a question in sql_context_query.
    18)If the user_query and query in sql_context_query are different, generate an SQL query based on the column descriptions in database_schema. Ask for clarification only if the question is very ambiguous; otherwise, try to generate the query based on the schema. Do not ask for clarification for all questions.
    19)If  is a follow-up to a query in <conversation_history>, modify the SQL query to maintain continuity with the previous topic rather than treating it as an independent query.
    20)If the current query is a follow-up to a previous question, modify the SQL query from conversation history by adjusting only the necessary conditions based on the new question. Retain the base structure, tables, and joins used in the previous SQL query.
    21)When determining whether a query is a follow-up:
        If the follow-up lacks specific table or column references, infer them from the previous query rather than using unrelated SQL context.
        If the question is vague, lacks table/column references, or is a phrase rather than a full question, it is likely a follow-up.
        Identify if the new query shares key terms or context with the last question in conversation history.
        If a follow-up lacks sufficient information, prioritize conversation history over predefined SQL contexts to ensure relevance.
    22)Do not assume that similar keywords mean the same topic. If the new query lacks specific biomarker or table details, infer them from the last conversation instead of SQL context.
    23)If the follow-up question lacks a biomarker name but modifies a numeric condition, assume it applies to the last query's biomarker instead of switching contexts.
    24)Before using predefined SQL, check if the follow-up query modifies the last conversation history. If so, update the last SQL instead of selecting a new one from SQL context.
    25)When generating SQL queries, do not use user-defined variables (such as @variable_name or syntax like @row_num := @row_num). Avoid constructs involving session variables, manual counters, or variable assignment.
    26)DO NOT PREFER WITH statement for generating SQL query. Follow this strictly.
    27)Do not use FLOAT Datatype , instead use DECIMAL. follow this strictly.
    28)The SQL query must be generated strictly using the exact column names and their original case (UPPERCASE/lowercase) as they appear in the provided <sample_dataframe>.You are not allowed to assume, infer, or modify column names in any way.All column names must be directly extracted and matched exactly as they appear in the <sample_dataframe>, including letter casing.This rule also applies when reusing or modifying an existing SQL query from the {sql_context_query}.You must carefully scan the <sample_dataframe> and update all column references in the query to match the column names exactly.
    29)If the user is asking about available fields, columns, or structure of a table (for example, "show me all fields", "list columns", "what are the fields in table X"), you must generate an SQL query using the INFORMATION_SCHEMA.COLUMNS system table and use {study_name} as database name.follow this strictly.
    30)Use the {study_name} while generating sql queries involving database name.
    32)When the user_query is related to data available for a study, you have to list all the tables along with some table description of those tables for that study using the database_schema.dont generate sql_query for this.follow this strictly.
    33)Generate concise and optimized SQL queries strictly compatible with MySQL v8.0. Avoid long subqueries, deeply nested expressions, or repeated calculations. Use temporary variables or intermediate steps only when necessary.
    34)Ensure the SQL query remains short and within reasonable length to prevent output truncation.
    35)Strictly verify the similarity between the user query and the provided {sql_context_query}. If the user query does not exactly match the sql_context_query, do not directly use the provided SQL query under any circumstances. Instead, always generate a SQL query based on the user query and conversation history also refer meta schema as well. This rule must be enforced without exception.
    36)Context-aware query handling: If the user query includes context-dependent references such as "these", "those", "prior query", "previous result", "earlier selection", or similar phrases, treat the query as a follow-up to the immediately preceding user query found in <conversation_history>. You must infer and apply the filters or result set logic from the last relevant query. Do not rely on <sql_context> unless the current user query is an exact match to the one in <sql_context>. Use the subset or context implied by the last conversation step to formulate the logic accurately.follow this strictly.
    37) When selecting columns with the same name from different tables (e.g., subjectid, sampleid, id, etc.), you must always apply distinct and meaningful SQL aliases to each selected column. This is mandatory — failure to alias duplicate column names will cause downstream processing errors. For example, alias table1.subjectid as subjectid_1 and table2.subjectid as subjectid_2. Never include the same column name more than once in the SELECT clause without a unique alias.follow this strictly.
    38)When generating SQL queries, ensure that JOIN operations are performed using direct and meaningful relationships between tables—typically on columns that represent shared identifiers (e.g., subjectid, sampleid). Avoid using functions or transformations (like SUBSTRING, CAST, etc.) in join conditions unless the schema or data structure explicitly requires it. Always prefer clear, natural joins that align with the database schema.
    39)While generating sql queries, please add sample_id column if exist in the required table in select clause. Follow this strictly.
    40)Do not generate an SQL query if the user's question can be answered directly from the database schema metadata (e.g., questions asking about available endpoints, column names, or study definitions). Instead, return a structured summary based on the <database_schema> content.
    41)Assume 'clean data' means records that do not have any associated open queries.
    42)If the user query asks for location, prioritize using country-related columns if available (e.g., 'country', 'country_name'). If no such columns exist, use 'site_id' or similar site-level identifiers instead.
    43)Always format date fields to return values in 'YYYY-MM-DD' format instead of raw timestamps or epoch values.follow this strictly
    44)When constructing the WHERE clause, always determine the correct column strictly from database schema, using the column name and description to align with the user's intent. Do not select a column merely because the queried value happens to appear in sample_dataframes; those values are only illustrative samples. Column choice must be schema-driven, while filter values can extend beyond the sampled rows.
    45)If a query cannot be logically or mathematically fulfilled (e.g., invalid percentages, impossible intervals, contradictory conditions), you must not generate or reuse SQL examples (including from {sql_context_query}), instead, respond clearly that the request cannot be processed with reason.Include the keyword fulfill in your response.
    46)Make all keywords, topics, and headers bold using Markdown syntax (e.g., **bold**) in your response.
    47)For any question involving only about samples, if the sample_inventory table is part of the SQL query, you must strictly use the column DERIVATIVEID instead of SAMPLEID. But if the question involves patient and sample_inventory table is also part of the SQL query, then you use SUBJID. Follow this strictly.
    48)If the user query explicitly mentions the term 'samples', always include and reference the sampleid column (or the table's corresponding sample-related column) in the generated SQL query.
    49)All clarification messages and all responses to user queries must mandatorily contain the keyword 'fulfill'. Do not generate any reply without this keyword.follow this strictly
    50)If the user's question is about the study baseline (e.g., 'what is baseline for this study' or any query asking for baseline definition), do NOT generate SQL. Instead, respond using the 'fulfill' keyword and return the baseline details exactly as provided in the
    51)Strictly validate the similarity between the user query and the provided {sql_context_query}.if the user query exactly matches the {sql_context_query}. In such cases, use the same SQL query without modification, except that baseline-related details must be inferred exclusively from vsim_details and ebdm_details, and not from the {sql_context_query}.
    Note: you need to to strictly use the column names in {columns} while generating sql query no matter wether you are going generate sq_query for a new question or going to use sql_query from the {sql_context_query}.follow this strictly.

    Assistant:"""

    return PromptResult(text=text, model_params=_SQL_PARAMS, format=PromptFormat.CLAUDE)


@PromptRegistry.register("sql.verification", category="sql")
def sql_verification_prompt(user_query: str, cached_query: str) -> PromptResult:
    """Verify if cached SQL query semantically matches new query."""
    text = f"""\n\nHuman:

Determine whether Query A and Query B mean the EXACT SAME thing.

Respond <semantic_match>YES</semantic_match> ONLY IF:
- Both queries ask for the same data
- All conditions, filters, parameters, and constraints are the same
- They would return the exact same result set

Respond <semantic_match>NO</semantic_match> IF:
- Any condition, filter, parameter, or constraint differs
- One query is broader or narrower than the other
- One query adds or removes requirements (even if key terms overlap)
- The queries merely share similar keywords but differ in meaning

Ignore ONLY minor wording differences that do NOT change meaning
(e.g., "list" vs "show", rephrasing, word order).

<QueryA>
{user_query}
</QueryA>

<QueryB>
{cached_query}
</QueryB>

IMPORTANT:
- Similar topic does NOT mean same intent
- Partial overlap does NOT mean equivalence
- When in doubt, respond NO

Respond ONLY in XML format:
<semantic_match>YES</semantic_match>
or
<semantic_match>NO</semantic_match>

\n\nAssistant:
"""

    return PromptResult(text=text, model_params=_VERIFICATION_PARAMS, format=PromptFormat.CLAUDE)