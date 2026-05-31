import chromadb

client = chromadb.PersistentClient(path="../chroma_db")

collection = client.get_or_create_collection(name="biomarker_research")


def store_document(doc_id: str, text: str, embedding):
    collection.upsert(
        ids=[doc_id],
        documents=[text],
        embeddings=[embedding]
    )


def search_similar(query_embedding, n_results: int = 3):
    return collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results
    )