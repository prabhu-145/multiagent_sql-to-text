from Bio import Entrez

Entrez.email = "prabhu01042005@gmail.com"


def search_pubmed(query: str, max_results: int = 5):
    handle = Entrez.esearch(
        db="pubmed",
        term=query,
        retmax=max_results
    )
    results = Entrez.read(handle)
    return results["IdList"]


def fetch_pubmed_abstracts(pubmed_ids):
    if not pubmed_ids:
        return ""

    ids = ",".join(pubmed_ids)

    handle = Entrez.efetch(
        db="pubmed",
        id=ids,
        rettype="abstract",
        retmode="text"
    )

    return handle.read()