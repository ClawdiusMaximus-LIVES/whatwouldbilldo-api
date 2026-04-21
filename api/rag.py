"""
RAG pipeline — embed query → search Supabase pgvector → return top passages.
"""

import os
import random
from openai import OpenAI
from supabase import create_client

_openai = None
_supabase = None

def get_openai():
    global _openai
    if _openai is None:
        _openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _openai

def get_supabase():
    global _supabase
    if _supabase is None:
        _supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
    return _supabase


def embed_query(text: str) -> list[float]:
    response = get_openai().embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding


def search_passages(query: str, k: int = 5, threshold: float = 0.65) -> list[dict]:
    """Return top-k relevant passages for a query."""
    embedding = embed_query(query)
    result = get_supabase().rpc("search_bill_passages", {
        "query_embedding": embedding,
        "match_count": k,
        "match_threshold": threshold
    }).execute()
    return result.data or []


def get_passage_count() -> int:
    result = get_supabase().table("bill_passages").select("id", count="exact").execute()
    return result.count or 0


def get_random_passage() -> dict | None:
    """Get a random passage for the daily reflection from the 1939 Big Book."""
    count_result = get_supabase().table("bill_passages")\
        .select("id", count="exact")\
        .eq("source", "big_book_1939")\
        .limit(1)\
        .execute()
    total = count_result.count or 0
    if total == 0:
        return None

    offset = random.randint(0, total - 1)
    result = get_supabase().table("bill_passages")\
        .select("content,source,chapter,title")\
        .eq("source", "big_book_1939")\
        .range(offset, offset)\
        .execute()
    return result.data[0] if result.data else None


def format_passages_for_prompt(passages: list[dict]) -> str:
    """Format retrieved passages for insertion into the Bill W. system prompt."""
    if not passages:
        return "No specific passages retrieved — respond from general knowledge of your writings."

    formatted = []
    for i, p in enumerate(passages, 1):
        source_label = _format_source(p)
        formatted.append(f"[Passage {i} — {source_label}]\n{p['content']}")

    return "\n\n".join(formatted)


def _format_source(passage: dict) -> str:
    source = passage.get("source", "unknown")
    chapter = passage.get("chapter")
    title = passage.get("title")

    labels = {
        "big_book_1939": "Alcoholics Anonymous (1939 First Edition)",
        "manuscript_1938": "Original Manuscript (1938)",
        "grapevine": "AA Grapevine",
        "letter": "Personal Letter",
        "talk": "Talk Transcript",
        "transcript": "Audio Recording Transcript",
        "traditions": "AA Traditions Pamphlet",
    }

    label = labels.get(source, source)
    if chapter:
        label += f", {chapter}"
    elif title:
        label += f", \"{title}\""
    return label
