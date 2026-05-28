import json
from typing import Dict, List, Optional, Tuple

from lifescience_prompts.registry import PromptRegistry
from lifescience_prompts.types import ModelParams, PromptFormat, PromptResult

_CLASSIFY_PARAMS = ModelParams(temperature=0.1, max_tokens=4000)


# ---------------------------------------------------------------------------
# Sub-prompts (individually registered for discoverability)
# ---------------------------------------------------------------------------

@PromptRegistry.register("classification.sub.sql", category="classification")
def sql_sub_prompt() -> PromptResult:
    """SQL classification sub-prompt block used inside the main classifier."""
    text = """
    - 'sql_query': Questions that require generating or using SQL queries to fetch data from a database. These questions often involve specific data retrieval tasks, even if they include biomarker terms. Carefully consider the schema of the database tables provided below to identify terms associated with SQL queries.Check if the user query implies data retrieval or manipulation tasks by understanding the context, even if specific SQL operations are not explicitly mentioned.These questions often involve specific data retrieval tasks, even if they mention biomarkers.
        Context Consideration: If a question relates to database terms (e.g., "study," "project," "protocol"), classify it as sql_query, even if the context is limited. Follow-up questions that imply continuation of previous database queries should also be classified as sql_query.
        If the user_query is a raw SQL query (e.g., starting with SELECT, INSERT, UPDATE, or DELETE), classify it as 'general'. These should not be routed to the 'sql_query' agent, as users are expected to interact using natural language.follow this strictly.
        -If the user's query is **highly related to nav_ai** based on reference documents or documentation content,
but also contains overlapping signals that relate to **SQL/database intent** (such as mentions of "data", "tables", "retrieval", "records", "queries"),
THEN ask for clarification **instead of classifying as sql_query**.


        examples:
        "Find all records where the biomarker level is greater than 10."
        "List the top 5 patients with the highest STAT1 expression."
        "What are the different biomarker data for this study?"
        "Get the total number of studies conducted in the last year."
        "What is the baseline value of IL2 in this dataset?"
        "Show me the 95% CI for the difference between baseline and post-baseline visits for JAK2"


    1. **Use the conversation history**: If the question appears to be a follow-up, classify it according to the context of the previous query. For example:
       - If the follow-up is about data retrieval related to a previous SQL question, classify it as 'sql_query'.
       - If the user query is the response related to clarification asked for the previous user query related to data retrieval, then classify it accordingly by going through the previous conversation history properly.it may look like general question but go through the conversation_history to look for relation with the previous clarification asked beacuse it can be generic as well.classify it as "sql_query"
       - **If the user is responding to a clarification request regarding a previous SQL-related query, ensure it is classified as "sql_query" and not "general" or "unknown".**
       - If a clarification was previously issued (e.g., nav_ai_clarification or sql_query clarification), and the user's intent is clarified in a later message, ensure that follow-up questions are classified based on the established context — even if the latest query appears ambiguous when viewed in isolation. Use the full conversation history to preserve and apply clarification context, unless the user explicitly shifts to a new topic.
    2. **Clarification Responses**: If the user is responding to a clarification request regarding a previous sql_query, ensure the response is classified as sql_query, even if it seems generic. Use the conversation history to determine if the original question required SQL-based data retrieval. Do not classify as general or report just because the response is vague or uncertain.
    3. **Schema awareness**: Even if a user query is short, it should still be classified as 'sql_query' if it references database-related terms like "study," "protocol," or "project."
    4. **If the query contains the keyword "study" (or related database schema terms like "protocol", "project"), classify it as sql_query regardless of the presence of biomarker keywords. Do not classify it as biomarker simply because biomarker terms appear alongside these database-related terms.**


    -   **'statistical'** : Questions that request statistical calculations, interpretations, or analyses not primarily related to visualizations or DEA reports, but rather to statistical metrics and hypothesis testing. These questions often involve statistical methods such as correlation coefficients, hypothesis tests, or confidence intervals — either requested directly, or indirectly implied.
            These questions may include requests for formulas, statistical explanations, or generating SQL to compute statistical metrics. Even if the query contains biomarker or database terms, classify it as 'statistical' if the user's primary intent is to perform or understand a statistical operation.
            Only classify a query as 'statistical' if it involves any of the following concepts, whether directly or indirectly through SQL/statistical computation requests:
        Core Statistical Keywords:

        Correlation & Association:
            Pearson correlation, Spearman correlation, Kendall's Tau, Point-Biserial, Phi Coefficient, Cramer's V

        Tests & Hypothesis Testing:
            p-value, hypothesis testing, null/alternative hypothesis
            t-test (one-sample, two-sample, paired), z-test, chi-square test
            ANOVA, MANOVA, F-test

        Descriptive Stats & Inference:
            Confidence interval (CI), mean, median, mode
            standard deviation, variance, range
            power analysis, effect size
            Type I / Type II error, statistical significance

        Explicitly requests a statistical method or mathematical estimate, such as:
            Pearson/Spearman correlation, regression, p-value, hypothesis testing, confidence interval, ANOVA, t-test, etc.
            Asks to calculate, estimate, perform, or compute a statistical metric.
            Involves statistical interpretation, formulas, or inference rather than exploratory analysis.

        Example queries that must be classified as 'statistical':

            1."What is the p-value for difference in VAF between treatment groups?"
            2."Can I compute the 95% confidence interval for this biomarker?"
            3."Perform a paired t-test between baseline and post-treatment expression."
            4."Explain Type I and Type II error in the context of gene expression."
            5."How to calculate power analysis for a two-sample t-test?"
            6."Compare the average ILG expression between patients on Monotherapy at Visit 1 and patients on Combination therapy at Visit 12"
            7. "What is the correlation between JAK2 and STAT1 gene expression for samples in this study?"
            8. "Perform a chi-square test between gender and response in survey table"
            9. "Run a chi-square test of independence between treatment arm and outcome"

        STRICT Classification Rules:

            1.If the query contains statistical keywords from the above list, classify it as 'statistical', regardless of whether it also includes biomarkers, genes, or database terms like "study" or "project".
            2.If the query requests SQL to compute a statistical metric (e.g., Pearson correlation, CI, t-test, chi-square test, ANOVA), classify it as 'statistical', even if SQL is involved.
            3.Do NOT classify statistical questions as 'chart_query' unless they explicitly mention visualization (e.g., "plot a histogram of standard deviation values" -> chart_query).
            4.Do NOT classify statistical queries as 'report' unless they explicitly request a DEA report or involve known DEA trigger phrases.
              Only classify as 'statistical' if the query explicitly requests computation of statistical tests, correlation coefficients, or related numeric metrics (e.g., "compute Pearson correlation", "calculate correlation coefficient", "find correlation p-value", "perform chi-square test", "run a t-test", "compute ANOVA").
            If the query only mentions "correlation", "relationship", or "association" in the context of biomarkers and clinical variables (e.g., treatment, disease stage, response), classify it as 'report' instead.
            If it refers to biological or clinical correlations (e.g., "correlation between disease severity and biomarker X" or "relationship between treatment response and age") without explicit data analysis intent, -> classify as report.
            However, if the query explicitly compares two measurable variables or genes (e.g., "correlation between JAK2 and STAT1 gene expression" or "relationship between protein levels and mRNA expression"), it should still be classified as statistical, even if no test name is mentioned.
            If a query uses wording like "please report" but the context shows the user is asking for data-driven analysis — such as comparing results across treatment arms, identifying drugs with the most assessments, analyzing measurements, trends, or group differences — always classify it as *statistical*, and only route to the report agent when the user explicitly requests generating or summarizing a narrative report.

    - **'chart_query'**: Questions that request any form of data visualization or graphical representation, regardless of the specific plot type. If the user query includes a request for **any type of plot that has ever existed**, classify it as **'chart_query'**. This includes standard visualizations (e.g., bar charts, line charts, scatter plots) as well as advanced statistical or domain-specific plots (e.g., Kaplan-Meier curves, heatmaps, survival plots).

        - **CRITICAL: Apply These Rules in STRICT Order (Highest Priority First)**:

            **RULE 1 - MANDATORY EXPLICIT VISUALIZATION CHECK** (Check this FIRST before any other rule):
                A query MUST ONLY be classified as 'chart_query' if it **explicitly mentions** one of these:
                - A chart type (bar chart, pie chart, line chart, scatter plot, box plot, violin plot, histogram, stacked bar chart, etc.)
                - A plot type (Kaplan-Meier, survival plot, heatmap, expression heat map, etc.)
                - Visualization keywords (plot, graph, visualize, chart, diagram)

                If NONE of these are present -> **IMMEDIATELY classify as 'sql_query'** and SKIP all other chart_query rules.

                Examples that should NOT be chart_query (no visualization keyword):
                - "Show me participant counts for top 5 sites"
                - "Can you show the gender distribution by site"
                - "Give me the biomarker levels across treatment groups"
                - "Display the patient demographics"

                Examples that SHOULD be chart_query (has visualization keyword):
                - "Plot the participant counts for top 5 sites"
                - "Create a bar chart of gender distribution by site"
                - "Visualize biomarker levels across treatment groups"

            **RULE 2 - CONVERSATION CONTEXT TAKES PRECEDENCE** (Check this SECOND):
                If the current query is a follow-up to previous SQL queries (check conversation_history):
                - And previous queries were about data retrieval (sql_query)
                - And current query continues the same topic
                - And current query does NOT explicitly mention visualization
                -> Classify as 'sql_query' to maintain context continuity

                Example flow:
                - Query 1: "How many participants are in the study?" -> sql_query
                - Query 2: "How many participants from each site?" -> sql_query
                - Query 3: "Can you show the top 5 sites?" -> sql_query (follow-up context)
                - Query 4: "Plot the top 5 sites" -> chart_query (explicit "plot")

            **RULE 3 - "SHOW/GIVE" WITHOUT VISUALIZATION = SQL** (Check this THIRD):
                If query starts with "show me", "give me", "display", "tell me", "can you show":
                - AND does NOT mention chart/plot/graph/visualize
                -> Classify as 'sql_query'

                These phrases indicate data display, not visualization.

            **RULE 4 - Only After Above Checks Pass, Apply These**:
            - If the user explicitly requests a data retrieval **AND visualization**, classify as 'chart_query'
            - If query mentions specific medical/scientific visualizations (Kaplan-Meier, heatmap), classify as 'chart_query'
            - If query asks about available charts/plots, classify as 'chart_query'

            **Additional Clarification Rules**:

                    Clarification Trigger:
                    If the query includes a chart/plot term AND mentions platform-related actions like:
                        - "configure"
                        - "customize"
                        - "set up"
                        - "in the view"
                        - "using filters"
                        - "on the dashboard"
                        - or other UI-oriented language
                    -> Then return:
                            {{
                            "classification": "nav_ai_clarification",
                            "clarification": "Just to clarify — are you asking me to generate a chart for this query, or are you seeking information on how to perform this action using the QuartzBio platform (e.g., through filters, views, or settings) from the nav_ai documentation?"
                            }}
                    Example:

                    "What is the correlation between JAK2 and STAT1 gene expression?" -> NOT chart_query

                    "Create a box plot of JAK2 expression levels." -> chart_query

                    "Show me gender distribution by site." (no visualization mentioned) -> NOT chart_query

                    "Plot the gender distribution by site." -> chart_query

             - **Examples for chart_query**:
                - "Compare the average IL-6 levels between two groups in a bar chart."
                - "Graph the correlation between cholesterol and blood pressure."
                - "Generate a pie chart for the percentage of different biomarkers found in samples."
                - "Can you create a Kaplan-Meier survival curve for this study?"
                - "Visualize a  box plot of TNF levels across different sample groups."
                - "Create a bar chart of number of samples by subject and site in sample inventory."
                - "Show a histogram of patient ages across treatment groups."
                - "Create a stacked bar chart of biomarker levels by treatment arm."

            **Important Notes**:
            1) If query asks to generate a report and includes terms like 'visualization', classify as 'report', NOT 'chart_query'.
            2) If user asks "show me available charts/plots", classify as 'chart_query' (asking about chart options).
            3) If query mentions "survival" or "survival analysis" WITH visualization intent ("plot survival", "survival curve"), classify as 'chart_query'.
            4) If query mentions "survival" WITHOUT visualization intent ("survival data", "survival rates"), classify as 'sql_query'.

            **Context Continuation Rules**:
            1. **Use conversation history for follow-ups** (already covered in RULE 2 above):
            - If follow-up continues SQL data retrieval context without mentioning visualization -> 'sql_query'
            - If the user query is the response related to clarification asked for the previous user query related to data retrieval, then classify it accordingly by going through the previous conversation history properly.it may look like general question but go through the conversation_history to look for relation with the previous clarification asked beacuse it can be generic as well.classify it as "sql_query"
            - **If the user is responding to a clarification request regarding a previous SQL-related query, ensure it is classified as "sql_query" and not "general" or "unknown".**
            - If a clarification was previously issued (e.g., nav_ai_clarification or sql_query clarification), and the user's intent is clarified in a later message, ensure that follow-up questions are classified based on the established context — even if the latest query appears ambiguous when viewed in isolation. Use the full conversation history to preserve and apply clarification context, unless the user explicitly shifts to a new topic.
            2. **Clarification Responses**: If the user is responding to a clarification request regarding a previous sql_query, ensure the response is classified as sql_query, even if it seems generic. Use the conversation history to determine if the original question required SQL-based data retrieval. Do not classify as general or report just because the response is vague or uncertain.
            3. If a follow-up query contains similar or overlapping keywords (e.g., "samples," "collected," "status") as a previous sql_query, but is phrased in a way that suggests platform usage (e.g., "How can I check...", "Where do I see...", "How do I find...") — then:
                - Do NOT assume continuation of SQL intent just because of keyword overlap.
                - Instead, trigger nav_ai_clarification if the phrasing suggests a potential platform interaction.
                - This applies even if the previous query was SQL and involved similar domain terms.
                - Treat the new query as independent and assess based on phrasing, not just term similarity.
            4. **Schema awareness**: Even if a user query is short, it should still be classified as 'sql_query' if it references database-related terms like "study," "protocol," or "project."
            5. **If the query contains the keyword "study" (or related database schema terms like "protocol", "project"), classify it as sql_query regardless of the presence of biomarker keywords. Do not classify it as biomarker simply because biomarker terms appear alongside these database-related terms.**


    """
    return PromptResult(text=text, model_params=_CLASSIFY_PARAMS)


@PromptRegistry.register("classification.sub.biomarker", category="classification")
def biomarker_sub_prompt() -> PromptResult:
    """Biomarker classification sub-prompt block used inside the main classifier."""
    text = """

    - 'biomarker': Questions related to the definitions, explanations, or general information about biomarkers, including research and clinical trial concepts where biomarkers play a role (e.g., trial stratification, surrogate endpoints, validation methods, predictive modeling for biomarkers). These questions do not involve data retrieval tasks, or tasks related to reports. If a question discusses research methodologies or trial designs commonly used in biomarker studies, classify it as 'biomarker' even if the word "biomarker" is not explicitly mentioned. Avoid classifying questions as 'biomarker' if they contain unrelated general knowledge topics.If a question references research, clinical studies, PubMed, trial design, biological samples, or data derived from experimental or clinical research, classify it as biomarker-related — these contexts inherently fall within biomarker research even when the word "biomarker" is not mentioned.
    If a question includes any internal, proprietary, or sample-specific identifiers (e.g., subject IDs, sample IDs, visit codes, dataset names, file names, schema fields, or any metadata that implies access to internal experimental or clinical data), do NOT classify it as biomarker; instead, route it to 'general', even if the question has relevance to 'biomarker'.
            Examples:
            "What is KRAS in colorectal cancer?"
            "In the context of PubMed, explain the role of TP53 mutations in breast cancer."
            "Give me an overview of MET amplification in lung cancer research."
            "Provide insights on MSI-H in colorectal cancer from 2020 to 2023."


        Important note on agent keyword matching:
        - If the question contains biomarker-related terms, it must be treated as related to the Biomarker agent.
        - If Biomarker is not in the available agents list, classify the question strictly as "out_of_scope".
        - Do NOT classify such questions as "general" under any circumstance.

"""
    return PromptResult(text=text, model_params=_CLASSIFY_PARAMS)


@PromptRegistry.register("classification.sub.viq", category="classification")
def viq_sub_prompt() -> PromptResult:
    """VIQ classification sub-prompt block used inside the main classifier."""
    text = """
- 'viq':
  Classify the question as 'viq' if it involves monitoring, analyzing, or forecasting clinical trial quality metrics and protocol compliance signals.

  **Core Vigilant IQ (VIQ) Domains:**
  - Metrics and Signal digest or KPI monitoring
  - Out-of-protocol collections and protocol deviations
  - Missed sample collections
  - Missed EDC (Electronic Data Capture) entries or data discrepancies
  - PK (Pharmacokinetic) sample compliance
  - Trend analysis over time periods (months, quarters, years)
  - Forecasting future metrics, signals, risks, or compliance issues
  - Correlation analysis between metrics (e.g., missed samples vs out-of-protocol collections)
  - Alerts, thresholds, or notification configuration
  - Explanation of alert behavior or triggers

  **Key Metric/Signal Patterns:**
  - Temporal indicators: "trend over X months", "last 12/24/36 months", "in 2024", "next quarter", "forecast", "predict", "projection"
  - Metric terms: "missed EDC entries", "missed sample collections", "out-of-protocol collections", "PK samples", "EDC discrepancies"
  - Actions: "show trend", "forecast", "predict", "list metrics", "filter by", "highest/lowest", "compare with other metrics"
  - Aggregations: Study/site/subject-level metric or signal evaluation, compliance analysis, deviation tracking

  **Examples (MUST classify as 'viq'):**
  - "Show me the trend of missed EDC data entries over the last 36 months"
  - "Show me the trend of missed EDC data entries over the last 12 months"
  - "Show me the current data and trends for missed sample collections over the last 24 months and compare it with other related metrics"
  - "Show me all active metrics"
  - "Show me all the issues related to 'Missed Sample Collections' in 2024"
  - "List all metrics in the Sample Metrics category"
  - "Which month had the highest out-of-protocol collections in the last 36 months?"
  - "Forecast missed EDC data entries for the next quarter"
  - "Predict out-of-protocol collections for the next 6 months"
  - "Show trend projection for EDC discrepancies"
  - "Give me my signal digest"
  - "Show all out-of-protocol collections for the last 2 months"

  **Do NOT classify as 'viq' if:**
  - Raw data retrieval without quality/compliance context -> 'sql_query'
  - Biomarker expression or biological insights -> 'biomarker'
  - Statistical analysis without compliance context -> 'statistical'
  - Platform navigation or UI operations -> 'nav_ai'
"""
    return PromptResult(text=text, model_params=_CLASSIFY_PARAMS)


# ---------------------------------------------------------------------------
# Main classification prompt
# ---------------------------------------------------------------------------

# Maps agent short codes to (category_name, sub_prompt_registry_key)
_BUILTIN_AGENT_MAP: Dict[str, Tuple[str, str]] = {
    "DataQuery": ("sql_query", "classification.sub.sql"),
    "Biomarker": ("biomarker", "classification.sub.biomarker"),
    "VIQ": ("viq", "classification.sub.viq"),
}

# Categories automatically added when DataQuery is present
_DATAQUERY_EXTRA_CATEGORIES = ["chart_query", "statistical"]


@PromptRegistry.register("classification.classify", category="classification")
def classification_classify_prompt(
    user_query: str,
    meta_schema: str,
    conversation_history: str,
    docs: str = "",
    ai_agents: Optional[List[str]] = None,
    extra_sub_prompts: Optional[Dict[str, Tuple[str, str]]] = None,
) -> PromptResult:
    """Classify a user query into the appropriate agent category.

    Parameters
    ----------
    user_query : str
        The user's question to classify.
    meta_schema : str
        Formatted database schema for context.
    conversation_history : str
        Prior conversation turns.
    docs : str
        Reference support documents (used by Navigator sub-prompt).
    ai_agents : list[str] | None
        Agent short codes enabled for this context (e.g. ["DataQuery", "Biomarker", "VIQ"]).
        Defaults to all built-in agents if *None*.
    extra_sub_prompts : dict | None
        Injected sub-prompts for agents NOT in the package (e.g. NavAI, EDP, Analytics).
        Mapping of ``{agent_code: (category_name, prompt_text)}``.
        Example: ``{"Navigator": ("nav_ai", nav_prompt_text), "Analytics": ("report", report_text)}``
    """
    if ai_agents is None:
        ai_agents = list(_BUILTIN_AGENT_MAP.keys())
    if extra_sub_prompts is None:
        extra_sub_prompts = {}

    categories: List[str] = ["general"]
    prompt_blocks: List[str] = []

    for agent in ai_agents:
        if agent in _BUILTIN_AGENT_MAP:
            cat_name, registry_key = _BUILTIN_AGENT_MAP[agent]
            sub_result = PromptRegistry.get(registry_key)()
            prompt_blocks.append(sub_result.text)
            if cat_name not in categories:
                categories.append(cat_name)
        elif agent in extra_sub_prompts:
            cat_name, prompt_text = extra_sub_prompts[agent]
            prompt_blocks.append(prompt_text)
            if cat_name not in categories:
                categories.append(cat_name)

    # DataQuery agent implies chart_query + statistical categories
    if "DataQuery" in ai_agents:
        for cat in _DATAQUERY_EXTRA_CATEGORIES:
            if cat not in categories:
                categories.append(cat)

    selected_prompts = "\n".join(prompt_blocks)
    all_agents_list_str = (
        "sql_query,report,nav_ai,biomarker,viq,general,chart_query,statistical"
    )

    categories_str = ", ".join(f"'{c}'" for c in categories)

    text = (
        "\n\nHuman:\n\n"
        "<instructions>\n"
        f"Classify the following question into one of the categories: {categories_str}.\n"
        "\n"
        "As a first step, identify the language of the user_query (it can be an abbreviation, a single word, or a sentence). If it is not English, return the following JSON response exactly:\n"
        '    {"classification": "language_block",\n'
        '    "language_check": "This chatbot supports only English."}\n'
        "\n"
        "Categories:\n"
        "\n"
        "- 'general':\n"
        '  Ensure that factual, open-ended, or general knowledge questions are always classified as "general" unless they explicitly request a report.\n'
        "  Additionally, if the question includes general knowledge entities—such as names of people, places, or unrelated broad topics—that don't logically align with document or database contexts, classify it as 'general', even if paired with domain-related keywords. If the overall intent is unclear or doesn't indicate a structured data request, treat it as a general inquiry.\n"
        "  If the user_query is a direct SQL query (e.g., starting with SELECT, INSERT, UPDATE, or DELETE), it must always be classified as 'general', regardless of whether the query references valid tables or columns from the meta schema. These should never be routed to the 'sql_query' agent. Users are expected to interact using natural language for query generation and interpretation.\n"
        "  Any user_query that requests information about the study itself—including descriptions, insights, summaries, overviews, or details—must be classified as sql_query, regardless of phrasing or level of specificity. These study-focused queries should never fall under the general category.\n"
        "  General Classification is also the fallback category for questions related to agents that are NOT in the current available agent list.\n"
        "\n"
        "Examples:\n"
        '"select * from patients_data limit 500" -> \'general\'\n'
        '"What is the capital of France?" -> \'general\'\n'
        '"How does a combustion engine work?" -> \'general\'\n'
        '"What is quantum mechanics?" -> \'general\'\n'
        '"Who was Albert Einstein?" -> \'general\'\n'
        '"Explain Newton\'s laws of motion." -> \'general\'\n'
        '"What is biomarker Sachin?" -> \'general\'  # even if biomarker agent is unavailable, classify as general\n'
        '"Show me how to export a report" -> \'general\'\n'
        '"Can I filter this view by category?" -> \'general\'\n'
        '"SELECT * FROM query_tracker_view" -> \'general\'\n'
        '"DELETE FROM error_logs WHERE status = \'failed\'" -> \'general\'\n'
        "\n"
        f"{selected_prompts}\n"
        "\n"
        "Note: The full list of agent types and their display names is:\n"
        "\n"
        f"{all_agents_list_str}\n"
        "\n"
        "Rules (Apply in this order):\n"
        "\n"
        "1. Classification scope:\n"
        f"   - Only classify the question into categories present in the current list: {categories}. Follow this strictly.\n"
        "   - Questions referencing specialized domain keywords related to unavailable agents should be classified as 'general' by fallback.\n"
        "\n"
        "2. Use 'general' as a fallback category for any question that does not explicitly fit available specialized agents.\n"
        "\n"
        "3. General category usage is strict: classify as 'general' only if the question matches the broad definition above.\n"
        "\n"
        "4. Do not create separate out-of-scope classifications. Instead, rely on 'general' classification as fallback.\n"
        "\n"
        "</instructions>\n"
        "\n"
        "<schema>\n"
        "Here is the schema of the database tables:\n"
        "\n"
        f"{meta_schema}\n"
        "</schema>\n"
        "\n"
        f"<Question>{user_query}</Question>\n"
        "\n"
        f"<conversation_history>{conversation_history}</conversation_history>\n"
        "\n"
        "Additionally, before classifying:\n"
        f"1. Analyze the {user_query} and correct any typos present in the question.\n"
        "2. Do not alter or add anything in the user query. Only correct spelling typos of general words.\n"
        "3. If the query has no typos, keep it exactly as is.\n"
        "4. Always preserve numbers, even if they look unrealistic (e.g., 110% confidence interval).\n"
        "\n"
        "Important:\n"
        "- Only correct spelling mistakes (typos). Do not remove or rephrase content.\n"
        "\n"
        "Always return your answer in JSON format like below.\n"
        "\n"
        "Example for clear and unambiguous queries:\n"
        "{\n"
        f'"classification": f"<one of: {categories_str}>",\n'
        '"query": "Corrected or unchanged user_query here"\n'
        "}\n"
        "\n"
        "Example for ambiguous queries:\n"
        "{\n"
        '"classification": "nav_ai_clarification",\n'
        '"clarification": "...",\n'
        '"query": "Corrected or unchanged user_query here"\n'
        "}\n"
        "\n"
        "Note:\n"
        "1) Use conversation history to identify follow-up questions based on previous questions to classify as sql_query instead of general. Follow strictly.\n"
        '2) Classify the user_query as "sql_query" if it has terms like study, protocol, project ONLY when the intent is to retrieve raw study data or schema-level information.If the intent is KPI monitoring, signal analysis, compliance trends, alerts, or forecasts,classify it as "viq" when available.\n'
        "\n"
        "Assistant:\n"
    )
    return PromptResult(
        text=text, model_params=_CLASSIFY_PARAMS, format=PromptFormat.CLAUDE
    )


# ---------------------------------------------------------------------------
# Ambiguity detection prompt
# ---------------------------------------------------------------------------

@PromptRegistry.register("classification.ambiguity", category="classification")
def ambiguity_prompt(meta_schema: str, user_query: str) -> PromptResult:
    """Detect if a query is ambiguous or clearly biomarker-related.

    Parameters
    ----------
    meta_schema : str
        Database schema (will be JSON-serialized if not already a string).
    user_query : str
        The user's question to analyze.
    """
    schema_str = json.dumps(meta_schema, indent=4) if not isinstance(meta_schema, str) else meta_schema

    text = f"""
        <|begin_of_text|>
        <|start_header_id|>user<|end_header_id|>
        Determine if the user query is ambiguous or biomarker-related based on the following instructions:

        <Instructions>
        Classify the following user query into one of the categories: **'ambiguous'** or **'biomarker'**.

                **Categories**:
                - **'ambiguous'**: The query is unclear or can be interpreted in multiple ways. This includes:
                    - Queries that involve both biological concepts (e.g., biomarkers) and data-related tasks (e.g., SQL, data retrieval, or statistical analysis) without clear intent.
                      Categorize single word or incomplete sentences as well into 'ambiguous' category strictly.
                    - Queries asking for relationships, statistics, or data manipulation involving biomarkers, where it is not clear if the focus is biological insight or data retrieval.

                - **'biomarker'**: The query is focused purely on biological details or insights related to biomarkers, without involving data manipulation or database tasks. This includes:
                    - Questions specifically about the biological role, function, or significance of biomarkers.
                    - Queries about biological processes or molecular interactions related to diseases or conditions.
                    - Queries that are not related to data tasks and are entirely focused on biological concepts, such as asking about the function of a gene or the role of a specific biomarker in a disease.

                **Guidelines**:
                1. If the query is a single word or incomplete sentence (e.g., just a term like "JAK2" or "average"), classify it as 'ambiguous'.
                2. If the query is about biological insights or functions of biomarkers without any data manipulation or database tasks, classify it as 'biomarker'.
                3. If the query involves biological terms but also suggests a potential data-related task (e.g., asking about data retrieval, table identification, or statistical analysis), classify it as **'ambiguous'**.

                **Respond only with 'ambiguous' or 'biomarker' based on the user query.**
        </Instructions>

        <database_schema>{schema_str}</database_schema>

        <Question>{user_query}</Question>
        <|eot_id|>
        <|start_header_id|>assistant<|end_header_id|>
        """
    return PromptResult(
        text=text,
        model_params=ModelParams(temperature=0.0, max_tokens=1000),
        format=PromptFormat.LLAMA,
    )


# ---------------------------------------------------------------------------
# Score prompt (confidence scoring across agents)
# ---------------------------------------------------------------------------

_AGENT_MAP = {
    "DataQuery": "Data Query Agent",
    "Biomarker": "Precision Medicine IQ Agent",
    "Analytics": "Analytics Agent",
    "Navigator": "Navigator Agent",
    "EDP": "EDP Agent",
    "VIQ": "VIQ Agent",
}

_ALL_AGENTS = {
    "Data Query Agent",
    "Precision Medicine IQ Agent",
    "General Agent",
    "Analytics Agent",
    "Visualization Agent",
    "Navigator Agent",
    "Statistical Agent",
    "EDP Agent",
    "VIQ Agent",
}


@PromptRegistry.register("classification.score", category="classification")
def score_prompt(
    user_query: str,
    meta_schema: str,
    conversation_history: str,
    docs: str = "",
    ai_agents: Optional[List[str]] = None,
    independent_prompt: str = "",
    dependent_prompt: str = "",
) -> PromptResult:
    """Score a user query with confidence across all available agents.

    Parameters
    ----------
    user_query : str
        The user's question to score.
    meta_schema : str
        Formatted database schema.
    conversation_history : str
        Prior conversation turns.
    docs : str
        Reference support documents.
    ai_agents : list[str] | None
        Agent short codes enabled (e.g. ["DataQuery", "Biomarker"]).
    independent_prompt : str
        Analytics independent variables text (injected by consumer from DB).
    dependent_prompt : str
        Analytics dependent variables text (injected by consumer from DB).
    """
    if ai_agents is None:
        ai_agents = list(_AGENT_MAP.keys())

    available_agents = [_AGENT_MAP.get(a.strip(), a.strip()) for a in ai_agents]

    if "General Agent" not in available_agents:
        available_agents.append("General Agent")

    if "Data Query Agent" in available_agents:
        for extra in ["Visualization Agent", "Statistical Agent"]:
            if extra not in available_agents:
                available_agents.append(extra)

    disabled_agents = _ALL_AGENTS - set(available_agents)
    disabled_note = (
        f"The following agents are NOT available in the current context: {', '.join(disabled_agents)}. "
        f'If a question belongs to any of these categories, assign 1.0 to "General Agent" and 0.0 to all others.'
        if disabled_agents
        else ""
    )

    scoring_categories = "\n".join([f"- '{a}'" for a in sorted(available_agents)])
    example_output = ",\n".join([f'  "{a}": 0.0' for a in sorted(available_agents)])

    dep_var_prompt = dependent_prompt
    indep_var_prompt = independent_prompt

    text = f"""
Human:

<instructions>
Score the following question into these categories with a confidence score (between 0 and 1) for each:

{scoring_categories}

The output must be a JSON object with confidence scores for **each** category, and the scores must **sum up to 1.0**.

Example Output:
{{
{example_output}
}}

Analyze the user query, database schema, and conversation history to assign appropriate confidence scores to each category.

{disabled_note}

IMPORTANT SCORING OVERRIDE RULE:
- You must only assign scores to the agents listed under the {scoring_categories} section above.
- Absolutely never assign a nonzero score to any agent that does not appear in the {scoring_categories} section above.
- If a query matches an agent that is NOT listed under "available_agents", you must:
    1. Assign 1.0 to "General Agent".
    2. Assign 0.0 to all other available agents.
- Remove any unavailable agent from your result. Your output must NEVER include a category that is not in available_agents (not even with a zero score).
- Ignore all other scoring rules in such cases: if the match is not in available_agents, only "General Agent" may receive a nonzero score.
- Scores must always sum to 1.0, distributed only among the available_agents.
follow the above rules strictly at any cost.



IMPORTANT NEGATIVE SCORING RULE:
- If the query does NOT clearly match any available agent category above, do NOT assign 0.0 to every agent.
- Instead, assign a score of 1.0 to "General Agent" (if present), and 0.0 to all other available agents.
- Your output must always sum to 1.0 and only include categories from the current available_agents list.
- Never return an output with all scores at 0.0.


<examples>
If the user's query does not match any {scoring_categories}(i.e., all agents in the list are unrelated to the question):
    Assign a score of 1.0 to "General Agent" (if present in available_agents).
    Assign a score of 0.0 to all other available agents.
    Never include an unavailable agent (disabled or missing) in the scoring output.
    Your output must always sum to 1.0, only among available agents.



Example:
Available agents:
'Data Query Agent'
'General Agent'
'Statistical Agent'
'Visualization Agent'

User query:
"What are the eligibility criteria for EDP?"
(EDP Agent is NOT available)

Required Output:

{{
  "Data Query Agent": 0.0,
  "General Agent": 1.0,
  "Statistical Agent": 0.0,
  "Visualization Agent": 0.0
}}
<examples/>

<Scoring Guidelines>


- 'Data Query Agent': Assign high confidence score if the question requires generating or using SQL queries to fetch data from a database. These questions often involve specific data retrieval tasks, even if they include biomarker terms. Carefully consider the schema of the database tables provided below to identify terms associated with SQL queries. Check if the user query implies data retrieval or manipulation tasks by understanding the context, even if specific SQL operations are not explicitly mentioned.

  - Context Consideration: If a question relates to database terms (e.g., "study," "project," "protocol"), assign high score to 'Data Query Agent', even if the context is limited. Follow-up questions that imply continuation of previous database queries should also receive high score for 'Data Query Agent'.

  - Examples:
    - "Find all records where the biomarker level is greater than 10."
    - "List the top 5 patients with the highest STAT1 expression."
    - "What are the different biomarker data for this study?"
    - "Get the total number of studies conducted in the last year."
    - "What is the baseline value of IL2 in this dataset?"

- 'Precision Medicine IQ Agent': Assign high score if the question is related to definitions, explanations, or general information about biomarkers. These questions do not involve data retrieval tasks or tasks related to reports. Prioritize checking whether the query requires data retrieval using the schema, even if the keyword "biomarker" is present in the query.

- 'General Agent': Assign high score if the question is not related to SQL queries, biomarkers, reports, or charts. Questions about system functionalities, user interactions, or data presentation (e.g., exporting, filtering, or viewing) should get high score for 'General Agent', even if they mention database-related terms. Only assign high score to 'Data Query Agent' if they explicitly require data retrieval or manipulation.

  - Examples:
    - "What is the capital of France?" -> high score for 'General Agent'
    - "How does a combustion engine work?" -> high score for 'General Agent'
    - "Who was Albert Einstein?" -> high score for 'General Agent'
    - "Explain Newton's laws of motion." -> high score for 'General Agent'

- 'Visualization Agent': Assign high score if the question requests any form of data visualization or graphical representation, regardless of the specific plot type. This includes bar charts, line charts, scatter plots, Kaplan-Meier curves, heatmaps, survival plots, etc.

  Key Scoring Rules for Chart Queries:
  1. If the user explicitly requests a data retrieval and its visualization, assign high score to 'Visualization Agent', even if the exact chart type is unclear.
  2. If the query involves generating or analyzing data with a graphical output, assign high score to 'Visualization Agent' instead of 'Data Query Agent'.
  3. If the query requires both SQL retrieval and a visualization, assign high score to 'Visualization Agent' since charts rely on data processing.
  4. If the query mentions statistical or categorical comparisons that imply graphical representation, assign high score to 'Visualization Agent' only if they clearly mention visualization.
  5. If a follow-up question asks for a plot based on a previous SQL query result, assign high score to 'Visualization Agent'.
  6. If the query references specific medical or scientific statistical visualizations (e.g., Kaplan-Meier plots, box plots), assign high score to 'Visualization Agent'.
  7. If a user query is about any charts available or plotting options, assign high score to 'Visualization Agent'.
  8. If the query starts with "show me" or "give me" but has no mention of a visualization or specific chart type, assign 0 score to 'Visualization Agent'. Follow this strictly.
  9. Analytical or statistical queries must not receive high score for 'Visualization Agent' unless they explicitly request a visualization.

  STRICT RULES (MUST FOLLOW):
  - Only assign high score to 'Visualization Agent' if it **explicitly mentions** a chart, plot, graph, or visualization (e.g., bar chart, box plot, scatter plot, Kaplan-Meier curve, heatmap).
  - DO NOT assume visualization unless explicitly stated.
  - NO GUESSING OR ASSUMPTIONS.

  DO NOT classify a query as 'Visualization Agent' if:
  - It involves statistical terms, gene expression, correlations, comparisons, confidence intervals, or mentions of biomarkers BUT **does not explicitly** mention any chart, plot, graph, or visualization.
  - It starts with phrases like "show me", "give me", or "tell me" but does not directly mention a chart/plot/visualization.

  Examples:
    - "What is the correlation between JAK2 and STAT1 gene expression?" -> NOT Visualization Agent
    - "Create a box plot of JAK2 expression levels." -> Visualization Agent
    - "Show me gender distribution by site." -> NOT Visualization Agent
    - "Plot the gender distribution by site." -> Visualization Agent

- 'Analytics Agent': Assign high score if the question is about report generation or report status.

  Report generation must meet ALL conditions:
    - a) Contains comparison intent (explicit or implied)
    - b) References biomarker/expression data from:
        {dep_var_prompt}
    - c) Uses clinical characteristics (Independent Variables) from:
        {indep_var_prompt}
    OR includes keywords/phrases like:
      - "Differentially expressed"
      - "Gene expression differences"
      - "Fold change in expression"
      - "Responders vs non-responders"
      - "upregulated/downregulated"
      - "DEA", "differential expression analysis"
      - "compare expression levels"
      - "significant gene difference"
      - "pre vs post"
      - "is this gene differentially expressed?"
      - "DEA analysis", "perform DEA", "analyze differential"

  Report status includes queries like:
    - "Give me list of analytics reports"
    - "How many analytics reports are completed"
    - "analytics reports?"
    - "link to download analytics reports"
    - "show list of analysis run by me"
    - Questions with "report status" or "status of reports"
    - "Where is my VAF comparison report?"
    - "Show completed DEA analyses."

  STRICT RULES:
  - Only assign high score to 'Analytics Agent' if exact patterns or keywords are matched
  - Do not assign score to 'Analytics Agent' for general biomarker questions or SQL requests
  - Report generation needs clear intent with structured parameters
  - If the user asks for a correlation analysis between any two variables ,always assign the highest score to the Analytics Agent.

-  'Navigator Agent': Classify a query as Navigator Agent only if its intent is clearly related to QuartzBio platform usage, UI features, documentation support, or operations tasks that are performed via the platform interface and not through backend SQL.
             This includes:
     - Navigating or using QuartzBio products like vSIM, EDP, REST API, dashboards, or file management features
     - Performing UI actions (e.g., uploading/downloading files, adding widgets, filtering, syncing, managing display settings)
     - Accessing help documentation, submitting support requests, resetting passwords
     - Interacting with platform-specific visual features such as plots, summary modals, or notification settings

     Classify as **Navigator Agent** only when ALL of the following are true:
     1. The user's question is about **platform functionality, UI interaction, or help documentation**
     2. The question's intent matches known **QuartzBio product support topics**
     Even if documentation appears relevant, you must confirm contextual alignment with platform usage intent — do NOT rely solely on content overlap.

     Do NOT classify as **Navigator Agent** if:
     The query is about retrieving or manipulating structured data (e.g., using SQL, filtering patients, generating summaries)
     The question relates to charting, plotting, or visualization logic
     Documentation similarity is surface-level — strong match in text alone is not enough to classify as **Navigator Agent**

     Use document similarity matches only as supportive signals — never route to **Navigator Agent** unless the intent clearly aligns with platform usage.
     <docs>
     These are reference support documents related to QuartzBio platform functionality, user operations, or documentation help. Use them **only** if the question appears to be related to QuartzBio UI, platform usage, or documentation support.
     Do NOT rely on these documents alone to classify the question as **Navigator Agent**. Use them only to validate if the question matches the intent of navigating or using the QuartzBio platform.
     {docs}
     </docs>

     Examples (**Navigator Agent**):
     - "How do I reset my password?" -> **Navigator Agent**
     - "Where do I upload a CSV to EDP?" -> **Navigator Agent**
     - "Can I filter by visit in vSIM?" -> **Navigator Agent**
     - "Navigate to the vSIM knowledge base" -> **Navigator Agent**
     - "How to view clinical summary modal?" -> **Navigator Agent**

    - 'EDP Agent':
        Score a query as edp if its intent is to retrieve, explore, or list data entities directly from the Enterprise Data Platform (EDP) — typically involving structured datasets, trials, drugs, vaults, studies, or therapeutic areas managed within the EDP ecosystem.
        The EDP agent specializes in metadata and entity-level data exploration, not biomarker analysis or statistical processing.
        It deals with retrieving available data, dataset summaries, entity lists, and relationships between drug, trial, and study entities.
        Score as 'edp' if ANY of the following hold true:
        1. The query explicitly mentions EDP or Enterprise Data Platform.
        2. The query asks for data or entities that exist within EDP, such as:
            * drugs
            * studies
            * trials
            * datasets
            * therapeutic areas
            * vaults
            * indications
            * usernames, suppliers or creators
            * results filtered by attributes like phase, created_by, indication, or vault.
        3. The query requests retrieval or exploration of available data, not computational analytics or visualizations.
        4. The query focuses on high-level dataset discovery, entity metadata, or dataset availability — not specific biomarker, statistical, or report-driven analysis.
        Intent cues that signal EDP queries:
        * "Get data for all ..."
        * "List all datasets ..."
        * "Show me the results of data for ..."
        * "Retrieve data from EDP for ..."
        * "Get all drugs/studies/trials/therapeutic areas ..."
        * "Show me results for phase X and indication Y"
        * "Show me data created by username John"
        * "Get all records from vault sb_cb_123"
        Do NOT score high for 'edp' if:
        * The query involves biomarkers, research insights, or biological interpretation -> score as 'biomarker'.
        * The query requests SQL-style structured data retrieval (with schema awareness) or refers to database terms like study table, project table, column, query -> score as 'sql_query'.
        * The query asks to visualize data, generate plots, or mention chart types -> score as 'chart_query'.
        * The query involves analytics, DEA, PCA, correlation summaries, or expression comparisons -> score as 'report' or 'statistical' as per rules.
        * The query asks how to perform EDP actions in the UI (upload, sync, navigate, configure filters) -> score as 'nav_ai'.
        * The query is broad, factual, or conversational (no structured intent) -> score as 'general'.

    - 'Statistical Agent':
        Questions that request statistical calculations, interpretations, or analyses not primarily related to visualizations or DEA reports, but rather to statistical metrics and hypothesis testing. These questions often involve statistical methods such as correlation coefficients, hypothesis tests, or confidence intervals — either requested directly, or indirectly implied.
        Priority Rule: If a query involves statistical concepts or operations (e.g., correlation, p-value, t-test, confidence interval), it must receive a higher score for 'Statistical Agent', even if it also includes terms like biomarkers, genes, or database-related words (e.g., "study," "project," or "SQL"). Statistical intent takes precedence over data retrieval or database context.
    These questions may include requests for formulas, statistical explanations, or generating SQL to compute statistical metrics. Even if the query contains biomarker or database terms, score it higher for 'Statistical Agent' if the user's primary intent is to perform or understand a statistical operation.
    Only score a query high for 'Statistical Agent' if it involves any of the following concepts, whether directly or indirectly through SQL/statistical computation requests:

    Core Statistical Keywords:
        Correlation & Association:
        Pearson correlation, Spearman correlation, Kendall's Tau, Point-Biserial, Phi Coefficient, Cramer's V

        Tests & Hypothesis Testing:
        p-value, hypothesis testing, null/alternative hypothesis
        t-test (one-sample, two-sample, paired), z-test, chi-square test
        ANOVA, MANOVA, F-test

        Descriptive Stats & Inference:
        Confidence interval (CI), mean, median, mode
        standard deviation, variance, range
        power analysis, effect size
        Type I / Type II error, statistical significance

    Example queries that must receive a high score for 'Statistical Agent':
        "Calculate the Pearson correlation between IL6 and CRP."
        "What is the p-value for difference in VAF between treatment groups?"
        "Can I compute the 95% confidence interval for this biomarker?"
        "Perform a paired t-test between baseline and post-treatment expression."
        "Is the correlation between EGFR and STAT3 significant?"
        "Explain Type I and Type II error in the context of gene expression."
        "How to calculate power analysis for a two-sample t-test?"

    - 'VIQ Agent':
        Score as 'VIQ Agent' if it involves:
        - monitoring, analyzing, or forecasting clinical trial quality metrics and protocol compliance signals.
        - Metrics and Signal digest or KPI monitoring
        - Out-of-protocol collections and protocol deviations
        - Missed sample collections
        - Missed EDC (Electronic Data Capture) entries or data discrepancies
        - PK (Pharmacokinetic) sample compliance
        - Trend analysis over time periods (months, quarters, years)
        - Forecasting future metrics, signals, risks, or compliance issues
        - Correlation analysis between metrics (e.g., missed samples vs out-of-protocol collections)
        - Alerts, thresholds, or notification configuration
        - Explanation of alert behavior or triggers

        **Key Metric/Signal Patterns:**
        - Temporal indicators: "trend over X months", "last 12/24/36 months", "in 2024", "next quarter", "forecast", "predict", "projection"
        - Metric terms: "missed EDC entries", "missed sample collections", "out-of-protocol collections", "PK samples", "EDC discrepancies"
        - Actions: "show trend", "forecast", "predict", "list metrics", "filter by", "highest/lowest", "compare with other metrics"
        - Aggregations: Study/site/subject-level metric or signal evaluation, compliance analysis, deviation tracking

        **Examples (MUST score as 'viq'):**
        - "Show me the trend of missed EDC data entries over the last 36 months"
        - "Show me the trend of missed EDC data entries over the last 12 months"
        - "Show me the current data and trends for missed sample collections over the last 24 months and compare it with other related metrics"
        - "Show me all active metrics"
        - "Show me all the issues related to 'Missed Sample Collections' in 2024"
        - "List all metrics in the Sample Metrics category"
        - "Which month had the highest out-of-protocol collections in the last 36 months?"
        - "Forecast missed EDC data entries for the next quarter"
        - "Predict out-of-protocol collections for the next 6 months"
        - "Show trend projection for EDC discrepancies"
        - "Give me my signal digest"
        - "Show all out-of-protocol collections for the last 2 months"

        **Do NOT score 'viq' if:**
        - Raw data retrieval without quality/compliance context -> 'sql_query'
        - Biomarker expression or biological insights -> 'biomarker'
        - Statistical analysis without compliance context -> 'statistical'
        - Platform navigation or UI operations -> 'nav_ai'


    STRICT Scoring Rules:
        If the query contains statistical keywords from the above list, score it high for 'Statistical Agent', regardless of whether it also includes biomarkers, genes, or database terms like "study" or "project".
        If the query requests SQL to compute a statistical metric (e.g., Pearson correlation, CI, t-test), score it high for 'Statistical Agent', even if SQL is involved.
        Do NOT score under 'chart_query' unless the query explicitly requests visualizations (e.g., "plot a histogram of standard deviation values" -> chart_query).
        Do NOT score under 'report' unless the query explicitly requests a DEA report or involves known DEA trigger phrases.

Please follow these key scoring rules strictly:
1. Use the conversation history to determine if the query is a follow-up. Adjust score accordingly.
2. If it's a clarification related to a previous SQL query, assign higher score to 'Data Query Agent'.
3. Avoid assigning score to 'Analytics Agent' unless the query meets all requirements.
4. If the query includes "study", "protocol", or "project", assign score to 'Data Query Agent' even if biomarkers are mentioned.
5. No assumptions. Use only explicit query details and history.

</Scoring Guidelines>

<schema>
Here is the schema of the database tables:
{meta_schema}
</schema>

<Question>{user_query}</Question>

<conversation_history>{conversation_history}</conversation_history>

Now return a list with confidence scores (summing to 1). Only include the list, no explanation or extra text. follow this strictly. Do NOT use ```
Do NOT use ```json or any code fences.
"""
    return PromptResult(
        text=text, model_params=_CLASSIFY_PARAMS, format=PromptFormat.CLAUDE
    )