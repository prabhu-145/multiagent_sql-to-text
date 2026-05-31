SUPPORTED_KEYWORDS = [
    "biomarker", "ctdna", "her2", "egfr", "jak2", "pd-l1", "pdl1",
    "kras", "nsclc", "mutation", "cancer", "genomics", "genome",
    "sequencing",

    "show", "list", "count", "records", "data", "samples", "patients",
    "shipped", "assay", "nanostring", "flow",

    "average", "mean", "median", "standard deviation", "std",
    "correlation", "t-test", "anova", "regression", "chi-square",
    "kaplan", "survival", "pfs", "os"
]

AMBIGUOUS_PHRASES = [
    "search in genomics",
    "search genomics",
    "find in genomics",
    "do genomics",
    "genomics search"
]


def is_supported_query(query: str) -> bool:
    q = query.lower()
    return any(keyword in q for keyword in SUPPORTED_KEYWORDS)


def is_ambiguous_query(query: str) -> bool:
    q = query.lower()
    return any(phrase in q for phrase in AMBIGUOUS_PHRASES)


def suggest_queries(query: str):
    q = query.lower()

    if "genomics" in q or "genome" in q:
        return [
            "What is genomics?",
            "Explain genomic sequencing in cancer research",
            "What biomarkers are used in genomics?"
        ]

    if "ctdna" in q:
        return [
            "What is ctDNA?",
            "Show ctDNA records",
            "Summarize latest papers on ctDNA"
        ]

    if "survival" in q:
        return [
            "Kaplan Meier survival analysis by treatment group",
            "Average OS by treatment group",
            "Compare treatment groups by OS"
        ]

    return [
        "What is HER2 biomarker?",
        "Show ctDNA records",
        "Average OS by treatment group"
    ]


def validate_user_query(query: str):
    if not query or not query.strip():
        return {
            "valid": False,
            "reason": "empty_query",
            "message": "Query cannot be empty.",
            "suggestions": suggest_queries(query)
        }

    if is_ambiguous_query(query):
        return {
            "valid": False,
            "reason": "ambiguous_query",
            "message": "Your query is unclear. Did you mean one of these?",
            "suggestions": suggest_queries(query)
        }

    if not is_supported_query(query):
        return {
            "valid": False,
            "reason": "unsupported_query",
            "message": "This query is outside the supported project scope.",
            "suggestions": suggest_queries(query)
        }

    return {"valid": True}