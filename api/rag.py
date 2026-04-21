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


def _looks_like_complete_passage(text: str) -> bool:
    """Reject chunks that start or end mid-sentence.

    The 1939 Big Book was chunked at token boundaries during ingest, so some
    chunks start with a lowercase word or end mid-word. Those read badly as
    standalone reflections.
    """
    s = (text or "").strip()
    if len(s) < 40:
        return False
    first = s[0]
    last = s[-1]
    starts_clean = first.isupper() or first in '"“—'
    ends_clean = last in '.?!"”'
    return starts_clean and ends_clean


def get_random_passage() -> dict | None:
    """Get a random passage for the daily reflection from the 1939 Big Book.

    Retries up to 10 times to find a chunk whose text reads as a complete
    passage. Falls back to whatever we last fetched if no clean chunk was
    found, so the endpoint never returns nothing.
    """
    count_result = get_supabase().table("bill_passages")\
        .select("id", count="exact")\
        .eq("source", "big_book_1939")\
        .limit(1)\
        .execute()
    total = count_result.count or 0
    if total == 0:
        return None

    last_seen: dict | None = None
    for _ in range(10):
        offset = random.randint(0, total - 1)
        result = get_supabase().table("bill_passages")\
            .select("content,source,chapter,title,chunk_index")\
            .eq("source", "big_book_1939")\
            .range(offset, offset)\
            .execute()
        if not result.data:
            continue
        passage = result.data[0]
        last_seen = passage
        if _looks_like_complete_passage(passage.get("content", "")):
            return passage

    return last_seen


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
