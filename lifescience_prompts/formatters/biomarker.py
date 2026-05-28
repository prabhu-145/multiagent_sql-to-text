from dataclasses import dataclass
from typing import Any, Dict, List, Union


@dataclass
class BiomarkerContext:
    """Pre-formatted biomarker data ready for prompt injection."""
    pubmed_texts: List[str]
    clinical_texts: List[str]
    sources_info: List[str]


def prepare_biomarker_context(
    pubmed_results: List[Union[str, Dict[str, Any]]],
    clinical_results: List[Union[str, Dict[str, Any]]],
) -> BiomarkerContext:
    """Extract and format texts/URLs from raw API result dicts."""
    pubmed_texts = [
        item["abstract"] if isinstance(item, dict) else str(item)
        for item in pubmed_results
    ]
    clinical_texts = [
        item["text"] if isinstance(item, dict) else str(item)
        for item in clinical_results
    ]
    sources_info = []
    for item in pubmed_results:
        if isinstance(item, dict) and "url" in item and item["url"]:
            sources_info.append(item["url"])
    for item in clinical_results:
        if isinstance(item, dict) and "url" in item and item["url"]:
            sources_info.append(item["url"])
    return BiomarkerContext(pubmed_texts, clinical_texts, sources_info)
