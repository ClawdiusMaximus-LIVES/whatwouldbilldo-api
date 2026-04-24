"""Supabase-backed cache for the daily reflection.

One row per UTC date. Both iOS and the marketing site read from this
(via the API) so all clients see the same reflection on a given day and we
only pay Anthropic once per day.
"""

from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

from api.rag import get_supabase, get_random_passage
from api.bill_persona import generate_daily_reflection


TABLE = "daily_reflections"
# App is US-only; rolling the daily reflection on US Eastern midnight keeps
# morning users in NYC/Chicago/LA/etc. on the same cadence as the author's
# intent. ZoneInfo handles EDT/EST transitions automatically.
DAILY_TZ = ZoneInfo("America/New_York")


def today_key() -> str:
    """Today's date in US Eastern as YYYY-MM-DD — the primary key format."""
    return datetime.now(DAILY_TZ).date().isoformat()


def fetch_for_date(date_key: str) -> Optional[dict]:
    result = (
        get_supabase()
        .table(TABLE)
        .select("*")
        .eq("date", date_key)
        .limit(1)
        .execute()
    )
    rows = result.data or []
    return rows[0] if rows else None


def fetch_today() -> Optional[dict]:
    return fetch_for_date(today_key())


def generate_and_store(date_key: Optional[str] = None) -> dict:
    """Pull a random passage, generate Bill's reflection on it, upsert into Supabase.

    Race note: if two requests land on the same empty date simultaneously, both
    will generate and the second upsert wins. Cheap enough we accept it for v1.
    """
    target = date_key or today_key()
    passage = get_random_passage()
    if not passage:
        raise RuntimeError("No passages available for daily reflection")

    reflection_text = generate_daily_reflection(passage)
    source_label = (
        passage.get("chapter")
        or passage.get("title")
        or passage.get("source", "Bill's writings")
    )

    row = {
        "date": target,
        "passage": passage["content"],
        "source": source_label,
        "reflection": reflection_text,
        "passage_id": passage.get("id"),
    }
    get_supabase().table(TABLE).upsert(row, on_conflict="date").execute()
    return row


def get_or_generate_today() -> dict:
    """Read today's row, or generate + store if missing. The endpoint entrypoint."""
    existing = fetch_today()
    if existing is not None:
        return existing
    return generate_and_store()
