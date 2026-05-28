import inspect
from typing import Callable, Dict, List, Optional


class PromptRegistry:
    """Central registry mapping prompt names to their factory callables."""
    _prompts: Dict[str, dict] = {}

    @classmethod
    def register(cls, name: str, category: str = "") -> Callable:
        """Decorator to register a prompt factory function."""
        def decorator(fn: Callable) -> Callable:
            cls._prompts[name] = {
                "fn": fn,
                "category": category,
                "signature": inspect.signature(fn),
            }
            return fn
        return decorator

    @classmethod
    def get(cls, name: str) -> Callable:
        """Retrieve a prompt factory by name."""
        entry = cls._prompts.get(name)
        if entry is None:
            available = list(cls._prompts.keys())
            raise KeyError(f"Prompt '{name}' not registered. Available: {available}")
        return entry["fn"]

    @classmethod
    def list_prompts(cls, category: Optional[str] = None) -> List[str]:
        """List all registered prompt names, optionally filtered by category."""
        if category:
            return [k for k, v in cls._prompts.items() if v["category"] == category]
        return list(cls._prompts.keys())

    @classmethod
    def info(cls, name: str) -> dict:
        """Return metadata about a registered prompt."""
        entry = cls._prompts[name]
        return {
            "name": name,
            "category": entry["category"],
            "parameters": str(entry["signature"]),
        }
