import os
import chromadb

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
CHROMA_PATH = os.path.join(BASE_DIR, "chroma_db")

client = chromadb.PersistentClient(path=CHROMA_PATH)

collection = client.get_or_create_collection(
    name="biomarker_research"
)


def store_document(
    doc_id: str,
    text: str,
    embedding,
    metadata: dict
):
    """
    Upsert prevents duplicate records for the same doc_id.
    Metadata stores PubMed ID, title, chunk ID, and query ID.
    """
    collection.upsert(
        ids=[doc_id],
        documents=[text],
        embeddings=[embedding],
        metadatas=[metadata]
    )


def search_similar(
    query_embedding,
    n_results: int = 3,
    where_filter: dict | None = None
):
    """
    Search similar documents.

    where_filter example:
    {"query_id": "abc123"}
    """
    query_args = {
        "query_embeddings": [query_embedding],
        "n_results": n_results,
        "include": [
            "documents",
            "metadatas",
            "distances"
        ]
    }

    if where_filter:
        query_args["where"] = where_filter

    return collection.query(**query_args)


def get_collection_count():
    return collection.count()