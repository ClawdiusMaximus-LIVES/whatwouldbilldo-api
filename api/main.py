"""
What Would Bill Do? — FastAPI backend
"""

import os
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from api.models import AskRequest, AskResponse, HealthResponse, DailyReflectionResponse
from api.guard_rails import is_crisis, get_crisis_response
from api.rag import search_passages, format_passages_for_prompt, get_passage_count, get_random_passage
from api.bill_persona import generate_response, generate_daily_reflection

# Rate limiter: 20 requests/minute per IP
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="What Would Bill Do?", version="1.0.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Lock this down to your domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/ask", response_model=AskResponse)
@limiter.limit("20/minute")
async def ask_bill(request: Request, body: AskRequest):
    """Main endpoint — runs crisis check first, then RAG + Bill persona."""

    message = body.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # Step 1: Crisis check (always runs first)
    if is_crisis(message):
        crisis_data = get_crisis_response()
        return AskResponse(
            crisis=True,
            crisis_message=crisis_data["crisis_message"],
            crisis_resources=crisis_data["crisis_resources"]
        )

    # Step 2: Retrieve relevant passages
    passages = search_passages(message, k=5)
    passages_text = format_passages_for_prompt(passages)

    # Step 3: Generate Bill's response
    history = [{"role": m.role, "content": m.content} for m in body.conversation_history]
    user_name = (body.user_name or "").strip() or None
    monthly_count = int(request.headers.get("X-Monthly-Count", "0"))
    response_text = generate_response(message, passages, history, passages_text, user_name, monthly_count)

    # Step 4: Build citations
    from api.models import Citation
    citations = []
    seen = set()
    for p in passages:
        key = (p.get("source"), p.get("chapter") or p.get("title"))
        if key not in seen:
            seen.add(key)
            citations.append(Citation(
                source=p.get("source", "unknown"),
                chapter=p.get("chapter"),
                title=p.get("title"),
                similarity=round(p.get("similarity", 0), 3)
            ))

    return AskResponse(
        response=response_text,
        citations=citations,
        crisis=False
    )


@app.get("/health", response_model=HealthResponse)
async def health():
    count = get_passage_count()
    return HealthResponse(status="ok", passages_count=count)


@app.get("/daily-reflection", response_model=DailyReflectionResponse)
async def daily_reflection():
    """Return today's shared reflection.

    Reads from the Supabase `daily_reflections` cache; on miss (first request of
    the day), generates via Anthropic, upserts, and returns. Every subsequent
    caller that day gets the cached row — one Anthropic call / day regardless of
    user count, same content on iOS and the marketing site.
    """
    from api.daily_reflection_store import get_or_generate_today

    try:
        row = get_or_generate_today()
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    return DailyReflectionResponse(
        passage=row["passage"],
        source=row["source"],
        reflection=row["reflection"],
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
