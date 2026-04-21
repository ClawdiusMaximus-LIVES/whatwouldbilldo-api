"""
Script 05 — Verify RAG search is working with 10 test queries.
"""

import os
from dotenv import load_dotenv
from openai import OpenAI
from supabase import create_client

load_dotenv()

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

TEST_QUERIES = [
    "How do I deal with resentment?",
    "What is the first step?",
    "How do I stay sober when I feel like drinking?",
    "What is a higher power?",
    "How do I make amends to people I've hurt?",
    "What does it mean to be powerless over alcohol?",
    "How do I help another alcoholic?",
    "What is the spiritual experience?",
    "How do I deal with fear?",
    "What is the purpose of the twelve traditions?",
]


def embed(text: str) -> list[float]:
    result = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return result.data[0].embedding


def search(query: str, k: int = 3) -> list[dict]:
    embedding = embed(query)
    result = supabase.rpc("search_bill_passages", {
        "query_embedding": embedding,
        "match_count": k,
        "match_threshold": 0.5  # lower threshold for testing
    }).execute()
    return result.data or []


def main():
    # Check passage count
    count_result = supabase.table("bill_passages").select("id", count="exact").execute()
    total = count_result.count or 0
    print(f"\n🔍 Verifying search — {total} passages in Supabase\n")

    if total == 0:
        print("ERROR: No passages found. Run scripts 03 and 04 first.")
        return

    passed = 0
    for query in TEST_QUERIES:
        results = search(query)
        if results:
            top = results[0]
            sim = top.get("similarity", 0)
            src = top.get("source", "?")
            preview = top.get("content", "")[:80].replace("\n", " ")
            print(f"✓ '{query[:45]}...' → {src} ({sim:.3f})")
            print(f"    \"{preview}...\"")
            passed += 1
        else:
            print(f"✗ '{query}' — NO RESULTS (threshold may be too high)")
        print()

    print(f"{'='*50}")
    print(f"Results: {passed}/{len(TEST_QUERIES)} queries returned passages")
    if passed == len(TEST_QUERIES):
        print("✅ Search is working! Ready to build the API.")
    elif passed >= 7:
        print("⚠️  Search is mostly working. A few queries returned nothing — check threshold.")
    else:
        print("❌ Search has issues. Check that pgvector extension is enabled in Supabase.")


if __name__ == "__main__":
    main()
