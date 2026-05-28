from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Tuple


class PromptFormat(Enum):
    """Indicates the LLM format tags used in a prompt."""
    PLAIN = "plain"
    CLAUDE = "claude"    # Uses \n\nHuman: / \n\nAssistant:
    LLAMA = "llama"      # Uses <|begin_of_text|> etc.


@dataclass(frozen=True)
class ModelParams:
    """Suggested model invocation parameters."""
    temperature: float = 0.1
    max_tokens: int = 4000
    stop_sequences: Tuple[str, ...] = ()


@dataclass(frozen=True)
class PromptResult:
    """Return value from every prompt factory function."""
    text: str
    model_params: ModelParams
    format: PromptFormat = PromptFormat.PLAIN
    metadata: Dict[str, Any] = field(default_factory=dict)
