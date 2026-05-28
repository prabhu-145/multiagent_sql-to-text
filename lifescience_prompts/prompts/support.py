from lifescience_prompts.registry import PromptRegistry
from lifescience_prompts.types import ModelParams, PromptFormat, PromptResult


@PromptRegistry.register("support.non_biomarker", category="support")
def non_biomarker_prompt(user_query: str) -> PromptResult:
    """Handle greetings, direct SQL commands, and out-of-scope queries."""
    text = f"""
   Human: {user_query}

    <Instructions>
    Follow the rules below carefully:

    1. If the user query is a greeting (e.g., "Hello", "Hi", "Good morning", "Good evening", etc.), respond with an appropriate greeting (e.g., "Hello!", "Hi there!", "Good morning!").

    2. If the user enters a direct SQL command (e.g., a query starting with SELECT, INSERT, UPDATE, DELETE), respond with:
    "It looks like you've entered a SQL query. Please rephrase your request in natural language so I can assist you in answering that."

    3. For all other queries, respond with:
    "This request is outside the scope of QuartzBio's Virtual Assistant.\\nTry rephrasing for better results, or contact Product Support via the "Help" button if assistance is needed"

    4.Make all keywords, topics, and headers bold using Markdown syntax (e.g., **bold**) in your response.
    </Instructions>

"""
    return PromptResult(
        text=text,
        model_params=ModelParams(temperature=0.1, max_tokens=512),
        format=PromptFormat.CLAUDE,
    )


@PromptRegistry.register("support.language_detection", category="support")
def language_detection_prompt(text: str) -> PromptResult:
    """Detect the language of user input text."""
    prompt_text = f"""
    <|begin_of_text|>
    <|start_header_id|>user<|end_header_id|>

    Identify the language of the input text.The input can be an abbreviation, a single word, or a sentence.
    If the input is a request, query, or instruction written in English, classify it as English.
    Most of the single word terms are related to biomarker entities, so classify them as English.
    If the input consists of commonly used English words, classify it as **English**.
    Provide only the name of the language as the output.

    Input: {text}
    Output:

    <|eot_id|>
    <|start_header_id|>assistant<|end_header_id|>
    """
    return PromptResult(
        text=prompt_text,
        model_params=ModelParams(temperature=0.2, max_tokens=150),
        format=PromptFormat.LLAMA,
    )
