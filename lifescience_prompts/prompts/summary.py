from lifescience_prompts.registry import PromptRegistry
from lifescience_prompts.types import ModelParams, PromptFormat, PromptResult

_SUMMARY_PARAMS = ModelParams(temperature=0.0, max_tokens=500)


@PromptRegistry.register("summary.data", category="summary")
def summary_data_prompt(record_count: int, sql: str, results: str) -> PromptResult:
    """Summarize SQL query results with 4 key observations."""
    text = f"""
\n\nHuman:

<Instructions>
follow the below response format:
    Here is a concise summary with 4 key observations from the query results:
        • [Observation 1]
        • [Observation 2]
        • [Observation 3]
        • [Observation 4]
• Provide a **concise summary** with exactly **4 key observations** derived **only from the visible Query results**.
• Use bullet points (`•`) for clarity.
• Follow these strict rules:
    - Do **NOT** infer, count, summarize**, or **analyze quantities**, totals, or frequencies from the visible data.
    - Do **NOT** estimate the number of rows, or records by reading the table.
    - Only mention the **total number of records** if explicitly provided via the `{record_count}` variable.
    - Do **NOT** highlight or pick specific rows unless they are **explicitly labeled unique** or visibly and clearly different.
    - Do **NOT** add annotations or comments about data formats, casing, or patterns (e.g., avoid adding "(lowercase)", "(uppercase)", or similar format descriptions).
• Focus only on clear, literal observations based on:
    - Summarize only the key observations of the data dont try to analyse or do any statistical analysis like calculating count etc,follow this strictly.
    - Summarize values without describing their formatting or casing.
    - Explicit differences or repeated field content (only if obvious without counting)
    - Any Notable observations or visible data ranges or field value.
• **Do not** explain the SQL logic, the query structure, or how the data might have been generated.
• If the query output uses statistical functions (`STDDEV`, `VARIANCE`, `CORRELATION`, `COVARIANCE`), add this note:
  _"Responses containing results from statistical calculations are approximations and should be interpreted with caution."_
• Make all keywords, topics, and headers bold using Markdown syntax (e.g., **bold**) in your response.
• Include Markdown structural elements such as headings (using # symbols), unordered and ordered lists, blockquotes, horizontal rules, and definition lists in the response where applicable, formatted using Markdown syntax


Note:
    • At the end of each summary , add a statement "Click the chart icon to view the visualization.",Strictly add this statement.
</Instructions>


<SQL query generated>{sql}</SQL query generated>
<Query results>{results}</Query results>


"""
    return PromptResult(text=text, model_params=_SUMMARY_PARAMS, format=PromptFormat.CLAUDE)


@PromptRegistry.register("summary.sql", category="summary")
def summary_sql_prompt(record_count: int, sql: str, results: str) -> PromptResult:
    """Summarize SQL query results (variant without chart icon note)."""
    text = f"""
\n\nHuman:


<Instructions>
follow the below response format:
    Here is a concise summary with 4 key observations from the query results:
        • [Observation 1]
        • [Observation 2]
        • [Observation 3]
        • [Observation 4]
• Respond using Markdown format. Use • for bullet points.
• Provide a **concise summary** with exactly **4 key observations** derived **only from the visible Query results**.
• Use bullet points (`•`) for clarity.
• Follow these strict rules:
    - Do **NOT** infer, count, summarize**, or **analyze quantities**, totals, or frequencies from the visible data.
    - Do **NOT** estimate the number of rows, or records by reading the table.
    - Only mention the **total number of records** if explicitly provided via the `{record_count}` variable.
    - Do **NOT** highlight or pick specific rows unless they are **explicitly labeled unique** or visibly and clearly different.
    - Do **NOT** add annotations or comments about data formats, casing, or patterns (e.g., avoid adding "(lowercase)", "(uppercase)", or similar format descriptions).
• Focus only on clear, literal observations based on:
    - Summarize only the key observations of the data dont try to analyse or do any statistical analysis like calculating count etc,follow this strictly.
    - Summarize values without describing their formatting or casing.
    - Explicit differences or repeated field content (only if obvious without counting)
    - Any Notable observations or visible data ranges or field value.
• **Do not** explain the SQL logic, the query structure, or how the data might have been generated.
• If the query output uses statistical functions (`STDDEV`, `VARIANCE`, `CORRELATION`, `COVARIANCE`), add this note:
  Note:"Responses containing results from statistical calculations are approximations and should be interpreted with caution."
• Make all keywords, topics, and headers bold using Markdown syntax (e.g., **bold**) in your response.
• Include Markdown structural elements such as headings (using # symbols), unordered and ordered lists, blockquotes, horizontal rules, and definition lists in the response where applicable, formatted using Markdown syntax

</Instructions>




<SQL query generated>{sql}</SQL query generated>
<Query results>{results}</Query results>

"""
    return PromptResult(text=text, model_params=_SUMMARY_PARAMS, format=PromptFormat.CLAUDE)


@PromptRegistry.register("summary.stats", category="summary")
def summary_stats_prompt(record_count: int, sql: str, results: str) -> PromptResult:
    """Summarize statistical query results with interpretation."""
    text = f"""\n\nHuman:

    <Instructions>
    follow the below response format:
    Here is a concise summary with 4 key observations from the query results:
        • [Observation 1]
        • [Observation 2]
        • [Observation 3]
        • [Observation 4]
    • Provide a **concise summary** with exactly **4 key observations** derived **only from the visible Query results**.
    • Use bullet points (`•`) for clarity.
    - Only mention the **total number of records** if explicitly provided via the `{record_count}` variable.

    • Strictly follow these rules:
        - **Identify the statistical method or test** (e.g., Pearson Correlation, t-test, ANOVA) used in the SQL query.
        - **Interpret the statistical result** based on its standard meaning. For example:
            - Correlation near ±1 → strong relationship; near 0 → weak or no relationship.
            - p-value < 0.05 → statistically significant.
            - Confidence interval range → estimate reliability.
        - Highlight **key statistical implications** such as presence of correlation, significance, variance explanation, effect size, etc.

    • Include precise interpretation of:
        - p-values, confidence intervals, correlation coefficients (r), t-scores, F-statistics, means, standard deviations, etc.
        - When applicable, **state whether the result is statistically significant or not**.

    • Do NOT:
        - List raw data or just restate values without interpretation.
        - Describe SQL logic, joins, or explain the query's technical structure.
        - Count rows or guess data size unless explicitly provided.

    • For Chi-Square Test results provided in <Statistical_Computation_Results> tags:
        - Report the chi-square statistic (chi2), degrees of freedom, and p-value.
        - State whether the result is statistically significant at alpha = 0.05.
        - Describe observed vs expected frequency patterns from the 2x2 table.
        - Note the sample size (n) used in the analysis.
        - Include the disclaimer provided in the chi-square results block.

    • Add this disclaimer **at the end** if the query used statistical functions (and no chi-square disclaimer was already included):
    "Statistical interpretations are based on query-derived outputs and should be validated with domain-specific thresholds and assumptions."

    • Make all keywords, topics, and headers bold using Markdown syntax (e.g., **bold**) in your response.
    • Include Markdown structural elements such as headings (using # symbols), unordered and ordered lists, blockquotes, horizontal rules, and definition lists in the response where applicable, formatted using Markdown syntax

    </Instructions>

    <SQL query generated>{sql}</SQL query generated>
    <Query results>{results}</Query results>"""
    return PromptResult(text=text, model_params=_SUMMARY_PARAMS, format=PromptFormat.CLAUDE)


@PromptRegistry.register("summary.explanation_llama", category="summary")
def explanation_llama(sql: str) -> PromptResult:
    """Explain SQL query in plain language (Llama format)."""
    text = f"""
<|begin_of_text|>
<|start_header_id|>user<|end_header_id|>
SQL Query:
{sql}
Start with: "Below are details on the data query that was executed to fulfill your request:". Then provide a structured summary covering these aspects:

i. What data table(s) were used
ii. How the tables were connected if they were linked
iii. What columns in each data table were accessed
iv. Additional conditions or filters applied
v. Any calculations, transformations, or derived results
vi. Whether all possible results or only unique entries were shown


example:
i.The query used data from a table named "bm_fc".
ii.No table joins were performed in this query.
iii.The query focused on two columns from the "bm_fc" table: "sampleid" and "param".
iv.The query applied filters to select only rows where the "param" column contained either "TNFA" or "TNFa" (case-insensitive).
v.No calculations or derivations were performed on the data.
vi.The query returned only unique combinations of "sampleid" and "param" values, eliminating any duplicate entries.

follow the below response format:
    Below are details on the data query that was executed to fulfill your request:
        • [Observation 1]
        • [Observation 2]
        • [Observation 3]
        • [Observation 4]
Note:
1. Do not include the raw SQL query in your response.
2. Present the explanation in the outlined example format. don't  mention subpoints inside the each point. just follow this strictly.
3. Avoid using SQL terminology or technical jargon.
<|eot_id|>
<|start_header_id|>assistant<|end_header_id|>
"""
    return PromptResult(text=text, model_params=_SUMMARY_PARAMS, format=PromptFormat.LLAMA)


@PromptRegistry.register("summary.explanation_claude", category="summary")
def explanation_claude(sql: str) -> PromptResult:
    """Explain SQL query in plain language (Claude format)."""
    text = f"""\n\nHuman:
    SQL Query:
    {sql}

    Start with: "The query included the following fields and conditions:". Then provide a structured summary covering these aspects:

    i. What data table(s) were used
    ii. How the tables were connected if they were linked
    iii. What columns in each data table were accessed
    iv. Additional conditions or filters applied
    v. Any calculations, transformations, or derived results
    vi. Whether all possible results or only unique entries were shown

    follow the below response format:
    The query included the following fields and conditions:
        • [Observation 1]
        • [Observation 2]
        • [Observation 3]
        • [Observation 4]

    Note:
    1. Do not include the raw SQL query in your response.
    2. Present the explanation in the outlined example format exactly like the example provided.
    3. Avoid using SQL terminology or technical jargon.

    \n\nAssistant:
    """
    return PromptResult(text=text, model_params=_SUMMARY_PARAMS, format=PromptFormat.CLAUDE)
