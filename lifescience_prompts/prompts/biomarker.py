from typing import Any, Dict, List, Union

from lifescience_prompts.formatters.biomarker import prepare_biomarker_context
from lifescience_prompts.registry import PromptRegistry
from lifescience_prompts.types import ModelParams, PromptFormat, PromptResult

_BIOMARKER_PARAMS = ModelParams(temperature=0.4, max_tokens=2000)


@PromptRegistry.register("biomarker.summarize", category="biomarker")
def biomarker_summarize(
    user_query: str,
    conversation_history: Union[str, List[Dict[str, str]]],
    pubmed_results: List[Union[str, Dict[str, Any]]],
    clinical_results: List[Union[str, Dict[str, Any]]],
    model_explanation: str,
) -> PromptResult:
    """Summarize PubMed + ClinicalTrials data for a biomarker query."""
    ctx = prepare_biomarker_context(pubmed_results, clinical_results)

    text = f"""
You are a senior Life Science expert.

Below are extracted summaries from PubMed and ClinicalTrials.gov related to a life science query.

--- PUBMED ABSTRACTS ---
{chr(10).join(ctx.pubmed_texts)}

--- CLINICALTRIALS.GOV SUMMARIES ---
{chr(10).join(ctx.clinical_texts)}

--- SOURCE LINKS ---
{chr(10).join(ctx.sources_info)}

<user_question>{user_query}</user_question>
<conversation_history>{conversation_history}</conversation_history>

Instructions:
1. Start with a short introductory section:

   These are the Key Insights:
   <basice_explanation>{model_explanation}<basic_explanation>

2. After the introductory explanation, structure the summary into the following sections:

   PubMed Insights:
   • Provide 2 to 4 **key findings** derived only from PubMed abstracts.
   • Each bullet should be **under 25 words**.
   • Keep the language simple and avoid redundancy.

   ClinicalTrials Insights:
   • Provide 2 to 4 **key findings** derived only from ClinicalTrials.gov summaries.
   • Each bullet should be **under 25 words**.
   • Keep the language concise and non-repetitive.

3. Finally, include a **Sources** section:
   - List all relevant sources from PubMed and ClinicalTrials.
   - Use this format:
       • PubMed - <link> - <title of the abstract>
       • ClinicalTrials.gov - <link> - <title of the abstract>

4. General rules:
   - Summarize **only** what is directly supported by the provided abstracts and summaries.
   - Do **not** use any external knowledge.
   - Do **not** add commentary or assumptions.
   - If there are no findings for a section, write:
     "No relevant insights found."
   - Make all keywords, topics, and headers bold using Markdown syntax (e.g., **bold**) in your response.
   - Include Markdown structural elements such as headings (using # symbols), unordered and ordered lists, blockquotes, horizontal rules, and definition lists in the response where applicable, formatted using Markdown syntax.

Strictly follow this structure:

These are the Key Insights:
<Model explanation goes here>

PubMed Insights:
• Bullet 1
• Bullet 2
• Bullet 3

ClinicalTrials Insights:
• Bullet 1
• Bullet 2
• Bullet 3

Sources:
• PubMed - <link> - <title>
• PubMed - <link> - <title>
• ClinicalTrials.gov - <link> - <title>
"""
    return PromptResult(text=text, model_params=_BIOMARKER_PARAMS)


@PromptRegistry.register("biomarker.definition", category="biomarker")
def biomarker_definition(user_query: str) -> PromptResult:
    """Generate a concise 2-3 line biomarker definition."""
    text = f"""
You are a life sciences and biomarker domain expert.
Provide a **concise and accurate** 2-3 line explanation or definition for the following query:
"{user_query}"

Focus only on relevant biomarker or life sciences context. Do not add extra details or examples.
"""
    return PromptResult(text=text, model_params=_BIOMARKER_PARAMS)


@PromptRegistry.register("biomarker.keyword_extraction", category="biomarker")
def biomarker_keyword_extraction(user_query: str) -> PromptResult:
    """Extract PubMed/ClinicalTrials search keywords and year range as JSON."""
    text = f"""
You are a life sciences expert.
Your job is to extract:
1. **Precise scientific search keywords** for PubMed and ClinicalTrials APIs.
2. **Start year** and **end year** for the search if the query specifies a timeframe.
3. If no year or timeframe is given, return `null` for both years.

### Rules:
- Do NOT include filler phrases like "latest studies" or "based on PubMed".
- Extract only **biomarkers, genes, proteins, molecular pathways, diseases, conditions, therapeutic areas**.
- For relative timeframes:
    - "latest" or "recent" → last 3 years
    - "past 5 years" → calculate dynamically
    - "since COVID" → 2020 onwards
- Return a valid JSON object only.

### Example 1
Input:
"Find the latest publications about PD-L1 expression in bladder cancer since 2018"
Output:
{{
  "keywords": "PD-L1 expression in bladder cancer",
  "start_year": 2018,
  "end_year": 2025
}}

### Example 2
Input:
"List clinical trials on EGFR mutations in lung cancer"
Output:
{{
  "keywords": "EGFR mutations in lung cancer",
  "start_year": null,
  "end_year": null
}}

User Query: "{user_query}"

Final Output (valid JSON only):
"""
    return PromptResult(text=text, model_params=_BIOMARKER_PARAMS)


@PromptRegistry.register("biomarker.general_info", category="biomarker")
def biomarker_general_info(user_query: str) -> PromptResult:
    """Provide general life science factual insights about a biomarker."""
    text = f"""
    Human:
    <user_question>{user_query}</user_question>

    Instructions:
    You are a life science expert.
    When given a {user_query}, provide clear, concise factual insights based on general life science knowledge, using your expertise to interpret and explain what the term likely refers to, its relevance, and its biological or clinical context.
    Guidelines:
    Begin with "These are the key insights:" before listing bullet points.
    Present the answer in bullet points, focusing only on the main interpretation and facts relevant to the term.
    Each bullet should contain only one clear fact without subpoints or nested lists.
    Use single newlines between bullets for clarity.
    Do not add disclaimers about database lookups or unknown status; instead, provide the best general interpretation based on life science expertise.
    Avoid unnecessary verbosity or disclaimers while ensuring the interpretation remains factual.
    Assistant:"""
    return PromptResult(
        text=text,
        model_params=_BIOMARKER_PARAMS,
        format=PromptFormat.CLAUDE,
    )
