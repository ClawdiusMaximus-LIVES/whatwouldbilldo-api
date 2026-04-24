"""
RAG pipeline — embed query → search Supabase pgvector → return top passages.
"""

import os
import re
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


_PAGE_PREFIX = re.compile(
    r'^(?:Page\s+\d+\s+)*'
    r'(?:Alcoholics Anonymous\s+)?'
    r'(?:Page\s+\d+\s+)?'
    r'(?:Chapter\s+\d+\s+)?'
    r'(?:[A-Z][A-Z\s]+\n)?'
)

_MID_WORD_BREAK = re.compile(r'(\w)-?\n(\w)')


def _clean_passage(text: str) -> str:
    # Strip PDF page-number artifacts and fix mid-word line breaks.
    s = (text or '').strip()
    s = _PAGE_PREFIX.sub('', s).strip()
    s = _MID_WORD_BREAK.sub(r'\1\2', s)
    return s


def _looks_like_complete_passage(text: str) -> bool:
    # Reject chunks that start or end mid-sentence after cleaning artifacts.
    s = _clean_passage(text)
    if len(s) < 60:
        return False
    first = s[0]
    last = s[-1]
    starts_clean = first.isupper() or first in ('”', '\u201c', '\u2014')
    ends_clean = last in ('.', '?', '!', '”', '\u201d')
    return starts_clean and ends_clean


_DAILY_ALLOWED_SOURCES = [
    "big_book_1939",
    "manuscript_1938",
    "grapevine",
    "letter",
    "talk",
]


def get_random_passage() -> dict | None:
    """Get a random passage for the daily reflection from Bill's public-domain corpus.

    Draws from the Big Book (1939), the 1938 Original Manuscript, early
    Grapevine articles, personal letters, and talk transcripts. Excludes
    the `traditions` source (ambiguous copyright). Retries up to 30 times
    to find a chunk whose text reads as a complete passage.
    """
    count_result = get_supabase().table("bill_passages")\
        .select("id", count="exact")\
        .in_("source", _DAILY_ALLOWED_SOURCES)\
        .limit(1)\
        .execute()
    total = count_result.count or 0
    if total == 0:
        return None

    last_seen: dict | None = None
    for _ in range(30):
        offset = random.randint(0, total - 1)
        result = get_supabase().table("bill_passages")\
            .select("content,source,chapter,title,chunk_index")\
            .in_("source", _DAILY_ALLOWED_SOURCES)\
            .range(offset, offset)\
            .execute()
        if not result.data:
            continue
        passage = result.data[0]
        last_seen = passage
        content = passage.get("content", "")
        if _looks_like_complete_passage(content):
            # Return cleaned version so UI never sees PDF artifacts
            cleaned = dict(passage)
            cleaned["content"] = _clean_passage(content)
            return cleaned

    # Fallback: return last seen with at least artifact-stripped content
    if last_seen:
        cleaned = dict(last_seen)
        cleaned["content"] = _clean_passage(last_seen.get("content", ""))
        return cleaned
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
        "big_book_1939": "the Big Book (1939)",
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
