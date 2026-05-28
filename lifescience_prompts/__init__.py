"""lifescience_prompts — LLM-agnostic prompt library for life-science applications."""

from lifescience_prompts._version import __version__
from lifescience_prompts.registry import PromptRegistry
from lifescience_prompts.types import ModelParams, PromptFormat, PromptResult

# Import prompt modules to trigger @PromptRegistry.register decorators
from lifescience_prompts.prompts import (  # noqa: F401
    biomarker,
    classification,
    sql,
    summary,
    support,
)


def get_prompt(name: str):
    """Shortcut to retrieve a prompt factory function by registry name."""
    return PromptRegistry.get(name)


def list_prompts(category: str | None = None):
    """List all registered prompt names, optionally filtered by category."""
    return PromptRegistry.list_prompts(category)


__all__ = [
    "__version__",
    "get_prompt",
    "list_prompts",
    "ModelParams",
    "PromptFormat",
    "PromptRegistry",
    "PromptResult",
]
