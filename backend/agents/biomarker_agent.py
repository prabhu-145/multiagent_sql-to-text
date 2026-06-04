import os
import hashlib

from services.pubmed_service import (
    search_pubmed,
    fetch_pubmed_abstracts,
)
from services.llm_service import generate_response
from services.embedding_service import create_embedding
from services.vector_service import store_document, search_similar


def build_pubmed_search_query(user_query: str) -> str:
    """
    Dynamically rewrite the user's question into a concise PubMed search query.
    This avoids biomarker-specific hardcoding.
    """

    prompt = f"""
You are a biomedical literature search assistant.

Convert the user question into a concise PubMed search query.

Rules:
- Return only the search query.
- Do not explain.
- Do not use markdown.
- Keep it under 12 words.
- Include biomedical terms likely to retrieve relevant PubMed abstracts.
- Do not answer the question.

User Question:
{user_query}

PubMed Search Query:
"""

    try:
        response = generate_response(
            prompt=prompt,
            model=os.getenv("BIOMARKER_AGENT_MODEL", "qwen2.5:1.5b"),
            num_ctx=512,
            num_predict=40,
            temperature=0.1,
            timeout=60,
        )

        cleaned = response.strip()
        cleaned = cleaned.replace('"', "")
        cleaned = cleaned.replace("`", "")
        cleaned = cleaned.split("\n")[0].strip()

        if cleaned:
            return cleaned

        return user_query

    except Exception:
        return user_query


def create_query_id(user_query: str, pubmed_query: str, pubmed_ids: list[str]) -> str:
    raw_text = (
        user_query.lower().strip()
        + "_"
        + pubmed_query.lower().strip()
        + "_"
        + "_".join(pubmed_ids)
    )

    return hashlib.md5(
        raw_text.encode("utf-8")
    ).hexdigest()


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

        query_id = metadata.get("query_id", "unknown")
        pubmed_id = metadata.get("pubmed_id", "unknown")
        title = metadata.get("title", "No title available")
        chunk_id = metadata.get("chunk_id", "unknown")

        context_blocks.append(
            f"""
Source {index + 1}
Query ID: {query_id}
PubMed ID: {pubmed_id}
Title: {title}
Chunk ID: {chunk_id}
Relevance Distance: {distance}

Evidence:
{document}
"""
        )

        sources.append({
            "query_id": query_id,
            "pubmed_id": pubmed_id,
            "title": title,
            "chunk_id": chunk_id,
            "distance": distance,
        })

    return "\n\n".join(context_blocks), sources


def handle_biomarker_query(user_query: str):
    try:
        pubmed_query = build_pubmed_search_query(user_query)

        pubmed_ids = search_pubmed(
            pubmed_query,
            max_results=2,
        )

        articles = fetch_pubmed_abstracts(pubmed_ids)

        if not articles:
            return {
                "agent": "biomarker_agent",
                "mode": "source_aware_rag",
                "status": "failed",
                "message": "No PubMed abstracts were found for this query.",
                "pubmed_query": pubmed_query,
                "pubmed_ids": pubmed_ids,
                "suggestion": "Try a more specific biomarker query such as HER2 breast cancer biomarker or EGFR mutation lung cancer.",
            }

        query_id = create_query_id(
            user_query=user_query,
            pubmed_query=pubmed_query,
            pubmed_ids=pubmed_ids,
        )

        stored_chunks = 0

        for article in articles:
            pubmed_id = article["pubmed_id"]
            title = article["title"]
            abstract = article["abstract"][:2500]

            chunks = chunk_text(
                abstract,
                chunk_size=600,
            )

            for chunk_id, chunk in enumerate(chunks):
                embedding = create_embedding(chunk)

                doc_id = f"{query_id}_pubmed_{pubmed_id}_chunk_{chunk_id}"

                metadata = {
                    "query_id": query_id,
                    "pubmed_query": pubmed_query,
                    "pubmed_id": pubmed_id,
                    "title": title,
                    "chunk_id": chunk_id,
                    "source": "PubMed",
                    "agent": "biomarker_agent",
                    "user_query": user_query,
                }

                store_document(
                    doc_id=doc_id,
                    text=chunk,
                    embedding=embedding,
                    metadata=metadata,
                )

                stored_chunks += 1

        query_embedding = create_embedding(user_query)

        similar_docs = search_similar(
            query_embedding,
            n_results=2,
            where_filter={
                "query_id": query_id,
            },
        )

        retrieved_context, sources = build_rag_context(
            similar_docs,
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

PubMed Search Query Used:
{pubmed_query}

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
            timeout=180,
        )

        return {
            "agent": "biomarker_agent",
            "mode": "source_aware_rag",
            "status": "success",
            "query_id": query_id,
            "pubmed_query": pubmed_query,
            "pubmed_ids": pubmed_ids,
            "articles_found": len(articles),
            "chunks_stored": stored_chunks,
            "retrieved_context_count": len(
                similar_docs.get("documents", [[]])[0]
            ),
            "sources": sources,
            "summary": summary,
        }

    except Exception as error:
        return {
            "agent": "biomarker_agent",
            "mode": "source_aware_rag",
            "status": "failed",
            "message": "Biomarker Agent failed during PubMed retrieval, embedding, vector search, or LLM summarization.",
            "error": str(error),
            "suggestion": "Check PubMed SSL, HuggingFace embedding model, ChromaDB path, and Ollama model status.",
        }