"""Pre-generate today's (or a given date's) reflection into Supabase.

Not called automatically. Run manually when you want the row seeded before any
user requests it — or wire into a Railway cron service later. Idempotent:
upsert on `date` primary key.

Usage:
    python -m api.cron_daily_reflection              # today UTC
    python -m api.cron_daily_reflection 2026-05-01   # specific date
"""

import sys
from datetime import date as _date

from api.daily_reflection_store import generate_and_store


def main(argv: list[str]) -> int:
    date_arg: str | None = argv[1] if len(argv) > 1 else None
    if date_arg is not None:
        # Validate YYYY-MM-DD format up front so a bad arg doesn't waste an Anthropic call.
        try:
            _date.fromisoformat(date_arg)
        except ValueError:
            print(f"Invalid date '{date_arg}'. Use YYYY-MM-DD.", file=sys.stderr)
            return 2

    try:
        row = generate_and_store(date_key=date_arg)
        print(
            f"✓ Stored daily_reflections[{row['date']}] · "
            f"source={row['source']!r} · "
            f"passage={row['passage'][:60]!r}..."
        )
        return 0
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
