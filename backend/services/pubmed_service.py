import os
import certifi
from Bio import Entrez

os.environ["SSL_CERT_FILE"] = certifi.where()

Entrez.email = "prabhu01042005@gmail.com"


def search_pubmed(query: str, max_results: int = 3):
    handle = Entrez.esearch(
        db="pubmed",
        term=query,
        retmax=max_results
    )

    record = Entrez.read(handle)
    handle.close()

    return record["IdList"]


def fetch_pubmed_abstracts(pubmed_ids):
    """
    Returns abstract records with PubMed ID metadata.
    """

    if not pubmed_ids:
        return []

    handle = Entrez.efetch(
        db="pubmed",
        id=",".join(pubmed_ids),
        rettype="abstract",
        retmode="xml"
    )

    records = Entrez.read(handle)
    handle.close()

    articles = []

    for article in records["PubmedArticle"]:
        medline = article["MedlineCitation"]

        pubmed_id = str(medline["PMID"])

        article_data = medline.get("Article", {})

        title = article_data.get("ArticleTitle", "No title available")

        abstract_text = ""

        if "Abstract" in article_data:
            abstract_parts = article_data["Abstract"].get("AbstractText", [])

            abstract_text = " ".join(
                str(part) for part in abstract_parts
            )

        if abstract_text.strip():
            articles.append({
                "pubmed_id": pubmed_id,
                "title": str(title),
                "abstract": abstract_text
            })

    return articles