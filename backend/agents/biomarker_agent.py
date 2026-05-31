from services.pubmed_service import search_pubmed, fetch_pubmed_abstracts
from services.llm_service import generate_response
from services.embedding_service import create_embedding
from services.vector_service import store_document, search_similar


def handle_biomarker_query(user_query: str):
    pubmed_ids = search_pubmed(user_query, max_results=1)
    abstracts = fetch_pubmed_abstracts(pubmed_ids)

    # Keep context small to avoid Ollama KV cache memory errors
    abstracts = abstracts[:500]

    chunks = [
        abstracts[i:i + 500]
        for i in range(0, len(abstracts), 500)
    ]

    for idx, chunk in enumerate(chunks):
        embedding = create_embedding(chunk)

        store_document(
            doc_id=f"{user_query}_{idx}",
            text=chunk,
            embedding=embedding
        )

    query_embedding = create_embedding(user_query)

    similar_docs = search_similar(
        query_embedding,
        n_results=1
    )

    documents = similar_docs.get("documents", [[]])[0]

    if not documents:
        retrieved_context = abstracts
    else:
        retrieved_context = documents[0]

    prompt = f"""
Answer briefly using this biomedical context.

Question:
{user_query}

Context:
{retrieved_context}

Answer:
"""

    summary = generate_response(prompt)

    return {
        "agent": "biomarker_agent",
        "pubmed_ids": pubmed_ids,
        "retrieved_context_count": len(documents),
        "summary": summary
    }