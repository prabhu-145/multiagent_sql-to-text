import os

from services.pubmed_service import (
    search_pubmed,
    fetch_pubmed_abstracts
)
from services.llm_service import generate_response
from services.embedding_service import create_embedding
from services.vector_service import store_document, search_similar


def chunk_text(text: str, chunk_size: int = 600):
    chunks = []

    for i in range(0, len(text), chunk_size):
        chunk = text[i:i + chunk_size].strip()

        if chunk:
            chunks.append(chunk)

    return chunks


def build_rag_context(similar_docs):
    documents = similar_docs.get("documents", [[]])[0]
    metadatas = similar_docs.get("metadatas", [[]])[0]
    distances = similar_docs.get("distances", [[]])[0]

    context_blocks = []
    sources = []

    for index, document in enumerate(documents):
        metadata = metadatas[index] if index < len(metadatas) else {}
        distance = distances[index] if index < len(distances) else None

        pubmed_id = metadata.get("pubmed_id", "unknown")
        title = metadata.get("title", "No title available")
        chunk_id = metadata.get("chunk_id", "unknown")

        context_blocks.append(
            f"""
Source {index + 1}
PubMed ID: {pubmed_id}
Title: {title}
Chunk ID: {chunk_id}
Relevance Distance: {distance}

Evidence:
{document}
"""
        )

        sources.append({
            "pubmed_id": pubmed_id,
            "title": title,
            "chunk_id": chunk_id,
            "distance": distance
        })

    return "\n\n".join(context_blocks), sources


def handle_biomarker_query(user_query: str):
    try:
        pubmed_ids = search_pubmed(
            user_query,
            max_results=2
        )

        articles = fetch_pubmed_abstracts(pubmed_ids)

        if not articles:
            return {
                "agent": "biomarker_agent",
                "mode": "source_aware_rag",
                "status": "failed",
                "message": "No PubMed abstracts were found for this query.",
                "pubmed_ids": pubmed_ids,
                "suggestion": "Try a more specific biomarker query such as HER2 breast cancer biomarker or EGFR mutation lung cancer."
            }

        stored_chunks = 0

        for article in articles:
            pubmed_id = article["pubmed_id"]
            title = article["title"]
            abstract = article["abstract"][:2500]

            chunks = chunk_text(
                abstract,
                chunk_size=600
            )

            for chunk_id, chunk in enumerate(chunks):
                embedding = create_embedding(chunk)

                doc_id = f"pubmed_{pubmed_id}_chunk_{chunk_id}"

                metadata = {
                    "pubmed_id": pubmed_id,
                    "title": title,
                    "chunk_id": chunk_id,
                    "source": "PubMed",
                    "agent": "biomarker_agent"
                }

                store_document(
                    doc_id=doc_id,
                    text=chunk,
                    embedding=embedding,
                    metadata=metadata
                )

                stored_chunks += 1

        query_embedding = create_embedding(user_query)

        similar_docs = search_similar(
            query_embedding,
            n_results=2
        )

        retrieved_context, sources = build_rag_context(
            similar_docs
        )

        prompt = f"""
You are a biomedical research assistant.

Use only the retrieved PubMed evidence below to answer the user's question.

Rules:
- Give a concise scientific explanation.
- Do not invent facts outside the retrieved evidence.
- If evidence is limited, mention that clearly.
- Mention the PubMed IDs used as evidence.
- Keep the answer within 4 sentences.

User Question:
{user_query}

Retrieved PubMed Evidence:
{retrieved_context}

Answer:
"""

        summary = generate_response(
            prompt=prompt,
            model=os.getenv("BIOMARKER_AGENT_MODEL", "qwen2.5:1.5b"),
            num_ctx=2048,
            num_predict=180,
            temperature=0.2,
            timeout=180
        )

        return {
            "agent": "biomarker_agent",
            "mode": "source_aware_rag",
            "status": "success",
            "pubmed_ids": pubmed_ids,
            "articles_found": len(articles),
            "chunks_stored": stored_chunks,
            "retrieved_context_count": len(
                similar_docs.get("documents", [[]])[0]
            ),
            "sources": sources,
            "summary": summary
        }

    except Exception as error:
        return {
            "agent": "biomarker_agent",
            "mode": "source_aware_rag",
            "status": "failed",
            "message": "Biomarker Agent failed during PubMed retrieval, embedding, vector search, or LLM summarization.",
            "error": str(error),
            "suggestion": "Check PubMed SSL, HuggingFace embedding model, ChromaDB path, and Ollama model status."
        }