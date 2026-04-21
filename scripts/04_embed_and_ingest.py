"""
Script 04 — Embed chunks with OpenAI and upsert to Supabase pgvector.
Batches 100 chunks at a time. Skips if already ingested.
"""

import os, json, time
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from supabase import create_client

load_dotenv()

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

CHUNKS_PATH = Path("corpus/processed/all_chunks.jsonl")
BATCH_SIZE = 100
EMBED_MODEL = "text-embedding-3-small"


def get_embeddings(texts: list[str]) -> list[list[float]]:
    """Get embeddings for a batch of texts."""
    response = openai_client.embeddings.create(
        model=EMBED_MODEL,
        input=texts
    )
    return [item.embedding for item in response.data]


def check_existing_count() -> int:
    result = supabase.table("bill_passages").select("id", count="exact").execute()
    return result.count or 0


def main():
    if not CHUNKS_PATH.exists():
        print("ERROR: corpus/processed/all_chunks.jsonl not found. Run script 03 first.")
        return

    chunks = []
    with open(CHUNKS_PATH, encoding="utf-8") as f:
        for line in f:
            chunks.append(json.loads(line.strip()))

    print(f"\n🧠 Embedding and ingesting {len(chunks)} chunks...")

    # Check how many are already in Supabase
    existing = check_existing_count()
    if existing > 0:
        print(f"  ⚠️  Supabase already has {existing} passages.")
        response = input("  Clear and re-ingest? (y/N): ").strip().lower()
        if response == "y":
            supabase.table("bill_passages").delete().neq("id", 0).execute()
            print("  Cleared existing passages.")
        else:
            print("  Skipping ingest — use existing data.")
            return

    total_batches = (len(chunks) + BATCH_SIZE - 1) // BATCH_SIZE
    ingested = 0

    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i:i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1

        texts = [c["content"] for c in batch]

        try:
            embeddings = get_embeddings(texts)
        except Exception as e:
            print(f"  ✗ Embedding batch {batch_num} failed: {e}")
            time.sleep(5)
            continue

        records = []
        for chunk, embedding in zip(batch, embeddings):
            records.append({
                "content": chunk["content"],
                "embedding": embedding,
                "source": chunk["source"],
                "chapter": chunk.get("chapter"),
                "title": chunk.get("title"),
                "date_written": chunk.get("date_written"),
                "chunk_index": chunk.get("chunk_index"),
                "token_count": chunk.get("token_count")
            })

        try:
            supabase.table("bill_passages").insert(records).execute()
            ingested += len(records)
            print(f"  ✓ Batch {batch_num}/{total_batches} ({ingested}/{len(chunks)} total)")
        except Exception as e:
            print(f"  ✗ Insert batch {batch_num} failed: {e}")
            time.sleep(2)

        # Rate limit: ~3000 RPM for embeddings, be conservative
        time.sleep(0.3)

    final_count = check_existing_count()
    print(f"\n✅ Ingest complete! {final_count} passages now in Supabase.")
    print("   Run script 05 to verify search is working.")


if __name__ == "__main__":
    main()
