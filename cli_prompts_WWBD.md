# What Would Bill Do? — Claude Code CLI Session Prompts

Paste these into Claude Code CLI one session at a time.
Wait for each session to fully complete before starting the next.

---

## BEFORE YOU START — Manual Setup (5 min)

1. Create a folder: `mkdir whatwouldbilldo && cd whatwouldbilldo`
2. Copy `CLAUDE.md` into that folder
3. Create a Supabase project at supabase.com (free tier)
   - Enable pgvector: go to SQL Editor → run `create extension if not exists vector;`
   - Grab your Project URL and anon key from Settings → API
4. Have ready: OpenAI API key, Anthropic API key, Supabase URL + key
5. Open Claude Code CLI in the `whatwouldbilldo/` folder: `claude`

---

## SESSION 1 — Project Setup + Supabase Schema

```
Read CLAUDE.md fully before doing anything.

Set up the What Would Bill Do? project:

1. Create the full folder structure from CLAUDE.md (corpus/, scripts/, api/, web/, supabase/)

2. Create .gitignore:
   .env
   corpus/raw/
   corpus/audio/
   __pycache__/
   *.pyc
   .DS_Store
   venv/

3. Create .env.example:
   OPENAI_API_KEY=sk-...
   ANTHROPIC_API_KEY=sk-ant-...
   SUPABASE_URL=https://[project].supabase.co
   SUPABASE_KEY=eyJ...

4. Create supabase/schema.sql with the exact schema from CLAUDE.md — the bill_passages table, search_bill_passages function, and ivfflat index.

5. Create api/requirements.txt:
   fastapi
   uvicorn
   openai
   anthropic
   supabase
   python-dotenv
   pdfplumber
   requests
   beautifulsoup4
   tiktoken
   httpx

6. Create a Python venv and install requirements:
   python3 -m venv venv
   source venv/bin/activate
   pip install -r api/requirements.txt

7. Create scripts/requirements.txt with the same packages (corpus scripts need them too)

8. Print a checklist of what the user needs to do manually in Supabase before S2 (run schema.sql in SQL editor)

git init
git add -A && git commit -m "S1: project scaffold, Supabase schema, requirements"
```

---

## SESSION 2 — Corpus Download

```
Read CLAUDE.md fully before doing anything.

Build scripts/01_download_corpus.py that downloads all public domain Bill W. source material.

The script must:

1. Download the 1939 Big Book HTML from https://anonpress.org/bb/
   - Scrape all chapter pages (the site has a chapter index)
   - Save each chapter as a separate .html file in corpus/raw/bigbook_1939/
   - Print progress for each chapter

2. Download the 1939 Big Book PDF as a fallback:
   URL: https://images.recoveryhq.com/wp-content/uploads/2020/07/14123720/1st-Edition-AA-Big-Book.pdf
   Save to: corpus/raw/bigbook_1939_fallback.pdf

3. Download the AA Traditions pamphlet (P-17):
   URL: https://www.aa.org/sites/default/files/literature/assets/p-17_AATraditions.pdf
   Save to: corpus/raw/p17_traditions.pdf

4. Scrape Grapevine articles from silkworth.net:
   URL: https://silkworth.net/aa/writings-of-a-a-members/bill-w/grapevine-articles-of-bill-w/
   - Find all article links on that page
   - For each article link: fetch the HTML, save to corpus/raw/grapevine/[slug].html
   - Rate limit: sleep 1 second between requests (be polite)
   - Skip any that return non-200
   - Print count as it goes

5. Scrape Bill W. talk transcripts from silkworth.net:
   URLs to scrape:
   - https://silkworth.net/alcoholics-anonymous/transcript-of-talk-given-by-bill-w/
   - https://silkworth.net/alcoholics-anonymous/bill-w-s-talk-to-the-manhattan-group/
   - https://silkworth.net/aa/writings-of-a-a-members/bill-w/talks-at-general-service-conferences/
   Save each to corpus/raw/talks/[slug].html

6. Scrape Bill W. letters from silkworth.net:
   URLs to scrape:
   - https://silkworth.net/aa/writings-of-a-a-members/bill-w/letters-to-jim-burwell-from-bill-wilson/
   - https://silkworth.net/alcoholics-anonymous/bill-w-s-letter-to-dr-carl-gustav-jung/
   Save each to corpus/raw/letters/[slug].html

7. Find and download audio files from silkworth.net:
   URL: https://silkworth.net/aa/audio-books/aa-speaker-bill-w/
   - Scrape the page to find all audio links (.mp3, .m4a, .ogg, .wav)
   - Download each audio file to corpus/audio/
   - Print filename + size for each

8. At the end, print a summary:
   - Files downloaded per category
   - Total size
   - Any failures (URLs that returned errors)

Run the script and show output. Fix any errors.

git add -A && git commit -m "S2: corpus download pipeline complete"
```

---

## SESSION 3 — Audio Transcription

```
Read CLAUDE.md fully before doing anything.

Build scripts/02_transcribe_audio.py that transcribes all audio files in corpus/audio/ using the OpenAI Whisper API.

Requirements:
1. Load OPENAI_API_KEY from .env
2. Find all audio files in corpus/audio/ (mp3, m4a, wav, ogg, flac)
3. For each audio file:
   a. Check if transcript already exists in corpus/transcripts/[filename].txt — skip if yes
   b. Check file size — Whisper API limit is 25MB. If larger, split using pydub into 20MB chunks
   c. Call openai.audio.transcriptions.create with model="whisper-1", language="en"
   d. Save the full transcript text to corpus/transcripts/[original_filename].txt
   e. Save metadata as corpus/transcripts/[original_filename]_meta.json:
      { "source_file": "...", "duration_estimate": "...", "word_count": ..., "transcribed_at": "..." }
   f. Print: filename, word count, first 100 chars of transcript

4. After all transcriptions, print summary:
   - Total files transcribed
   - Total word count across all transcripts
   - Any files that failed

5. For any file that fails (API error, format issue), log it to corpus/transcripts/failed.log with the error message — don't crash the whole script.

Use a requests.Session with a reasonable timeout. The 1954 Fort Worth talk may be long — be patient.

Run the script and show output.

git add -A && git commit -m "S3: Whisper audio transcription pipeline"
```

---

## SESSION 4 — Clean, Chunk, Embed, Ingest

```
Read CLAUDE.md fully before doing anything.

This is the core data pipeline. Build two scripts:

--- scripts/03_clean_and_chunk.py ---

Converts all raw source files into clean, chunked JSONL records.

For each source type, implement a cleaner:

BIG BOOK (HTML files in corpus/raw/bigbook_1939/):
- Parse HTML with BeautifulSoup, extract text only
- Remove page numbers (lines that are just a number)
- Remove headers/footers (short repeated lines)
- Identify chapter boundaries from headings

GRAPEVINE ARTICLES (HTML in corpus/raw/grapevine/):
- Parse HTML, extract article title + body text
- Extract date from the page if available (look for month/year patterns)
- Clean: remove nav elements, ads, sidebars — body text only

TALKS (HTML in corpus/raw/talks/):
- Parse HTML, extract talk title + body text
- Note: these may have transcription artifacts — clean [inaudible] markers

LETTERS (HTML in corpus/raw/letters/):
- Parse HTML, extract letter content
- Preserve "Dear [name]" openings and sign-offs — they're part of Bill's voice

TRANSCRIPTS (TXT in corpus/transcripts/):
- Raw Whisper output — clean repeated words, obvious transcription errors
- Add source metadata from the _meta.json sidecar file

CHUNKING (apply to all cleaned text):
- Target 250 tokens per chunk (use tiktoken cl100k_base encoding to count)
- Overlap: last 30 tokens of previous chunk prepended to next chunk
- Never split in the middle of a sentence — find nearest sentence boundary
- Each chunk becomes a JSON record:
  {
    "content": "...",
    "source": "big_book_1939" | "grapevine" | "talk" | "letter" | "transcript",
    "chapter": "Chapter 5: How It Works",   // null if not applicable
    "title": "...",                           // article/talk title
    "date_written": "1939" | "1944-06" | etc,
    "chunk_index": 0,
    "token_count": 247
  }

Save all records to corpus/processed/all_chunks.jsonl (one JSON per line)
Print summary: total chunks, chunks per source type, avg token count

--- scripts/04_embed_and_ingest.py ---

Reads corpus/processed/all_chunks.jsonl, embeds each chunk, upserts to Supabase.

1. Load .env (OPENAI_API_KEY, SUPABASE_URL, SUPABASE_KEY)
2. Connect to Supabase
3. Read all_chunks.jsonl
4. Batch embed using openai.embeddings.create, model="text-embedding-3-small"
   - Batch size: 100 chunks per API call (API limit is 2048, but 100 is safe)
   - Print progress every 100 chunks
5. Upsert each embedded chunk to bill_passages table (use ON CONFLICT DO NOTHING)
6. After ingestion, run a quick sanity check:
   - Query total row count from bill_passages
   - Run one test search: embed "what do I do when I want to drink?" and return top 3 results
   - Print the results so we can visually verify quality

Run both scripts in sequence and show output. Fix any errors until the test search returns sensible Big Book passages.

--- scripts/05_verify_search.py ---

Run 10 sample queries that real users would ask, print the top 3 retrieved passages for each:

Queries:
1. "I'm angry at someone who wronged me and I can't let it go"
2. "What do the 12 steps actually mean"
3. "I relapsed after 6 months sober"
4. "I don't believe in God, can AA still work for me"
5. "How do I make amends to someone I really hurt"
6. "I feel hopeless and nothing is getting better"
7. "What is the fourth step"
8. "I'm scared of what I'll find if I look at myself honestly"
9. "My sponsor isn't available and I need help right now"
10. "Why does selfishness matter in recovery"

For each query print: query → top passage (first 150 chars) → source.

The output of this script is the quality gate. If the passages are relevant and from the right sources, S4 is done.

git add -A && git commit -m "S4: clean, chunk, embed, ingest corpus — RAG verified"
```

---

## SESSION 5 — FastAPI Backend

```
Read CLAUDE.md fully before doing anything.

Build the FastAPI backend in api/. This is the core service the web UI and iOS app will call.

--- api/models.py ---
Pydantic models:
- ChatMessage: role (str), content (str)
- AskRequest: message (str), conversation_history (list[ChatMessage], max 10)
- Citation: content (str), source (str), chapter (str | None), title (str | None), similarity (float)
- AskResponse: response (str), citations (list[Citation]), crisis (bool)
- CrisisResponse: crisis (bool = True), message (str), resources (list[dict])
- HealthResponse: status (str), passages_count (int)
- ReflectionResponse: passage (str), source (str), reflection (str)

--- api/guard_rails.py ---
crisis_check(message: str) -> bool

Uses OpenAI GPT-4o-mini with this exact prompt:
"Classify this message. Reply with ONLY one word: CRISIS or SAFE.

CRISIS if the message contains: suicidal ideation, active self-harm intent, overdose situation, immediate danger to self or others.

SAFE for everything else including: general distress, cravings, relationship problems, step questions, resentment, grief, past-tense relapse discussion.

Message: {message}"

Temperature 0, max_tokens 5. Parse response, return True if CRISIS.
If the API call fails for any reason, return False (fail open — don't block users on API errors).

--- api/rag.py ---
retrieve_passages(query: str, match_count: int = 5) -> list[dict]

1. Embed query with text-embedding-3-small
2. Call Supabase search_bill_passages RPC function
3. Return list of passage dicts with content, source, chapter, title, similarity

--- api/bill_persona.py ---
ask_bill(message: str, passages: list[dict], conversation_history: list[ChatMessage]) -> str

Build the Claude API call:
- System prompt: use the FULL Bill W. system prompt from CLAUDE.md, inserting the retrieved passages into [RETRIEVED_PASSAGES]
- Format retrieved passages as:
  "PASSAGE 1 (from {source}, {chapter or title}):
  {content}
  ---"
- Messages: conversation_history (last 6 exchanges max) + current user message
- Model: claude-sonnet-4-6
- Max tokens: 600
- Temperature: 0.7

Also build:
get_daily_reflection() -> dict
- Pick a random passage from bill_passages where source = 'big_book_1939'
- Ask Claude (shorter prompt, 200 tokens) to write a 2-sentence reflection in Bill's voice on that passage
- Return {passage, source, reflection}

--- api/main.py ---
FastAPI app with these routes:

GET /health
- Query Supabase for count of bill_passages
- Return {status: "ok", passages_count: N}

POST /ask
- Validate request
- Run crisis_check first — if crisis, return CrisisResponse immediately (do NOT call Bill)
- retrieve_passages(message)
- ask_bill(message, passages, conversation_history)
- Parse citations from retrieved passages
- Return AskResponse

GET /daily-reflection
- Return get_daily_reflection()

CORS: allow all origins for now (prototype, will restrict for production)
Add rate limiting: 30 requests per minute per IP (use slowapi)

Start the server with: uvicorn api.main:app --reload --port 8000

Run it and verify:
- GET /health returns ok + passage count
- POST /ask with {"message": "I keep thinking about drinking", "conversation_history": []} returns a Bill W. response with citations
- POST /ask with {"message": "I want to kill myself", "conversation_history": []} returns crisis response, NO Bill response

git add -A && git commit -m "S5: FastAPI backend — RAG + Bill persona + guard rails"
```

---

## SESSION 6 — Web Chat Interface

```
Read CLAUDE.md fully before doing anything.

Build the web chat interface in web/. This is the "quick and dirty" prototype to prove the product works. Keep it simple but make it feel right.

--- web/index.html + web/style.css + web/app.js ---

Design spec:
- Dark background: #080a0f
- Bill's message bubbles: #0f1219 background, 1px border #222b3a, warm amber left border #C8860A
- User message bubbles: #1c2330, right-aligned
- Citation text: small, #5a6478, italic, below Bill's bubble
- Font: system-ui or Georgia for Bill's text (slightly serif feels right)
- Input bar: fixed bottom, dark, send button in amber

Features:
1. Chat interface — messages scroll, input at bottom
2. Bill's messages have a subtle typewriter animation (characters appear one by one from the API stream — or just fade in if streaming is too complex)
3. Citations shown below each Bill response:
   — From [source], [chapter or title]
4. CRISIS response: full-width amber card that replaces the normal message:
   "It sounds like you're in a really hard place right now. Please reach out:"
   Then list the hotlines with click-to-call links
5. Sobriety counter in the top-right corner:
   - Small widget, user can click to set their sobriety date
   - Shows "X days sober" using localStorage
   - Not connected to API — just local
6. "Ask Bill anything..." placeholder text in the input
7. Suggested opening questions shown before first message:
   - "What do I do when I want to drink?"
   - "How do I work the steps?"
   - "I relapsed. What now?"
   Click to pre-fill the input.
8. Mobile responsive — works on phone

API connection:
- Call http://localhost:8000/ask for local dev
- Make the API URL a const at the top of app.js so it's easy to change for production

Loading state: show a "Bill is thinking..." indicator with three dots animation while waiting for response.

Error state: if the API is down, show a friendly message: "Bill isn't available right now. Please try again in a moment."

After building, open index.html in a browser (it can call localhost:8000 directly).
Test the full flow manually:
1. Type a real recovery question → verify Bill responds with citations
2. Click a suggested question → verify it works
3. Type "I want to hurt myself" → verify crisis card appears, no Bill response
4. Set a sobriety date → verify counter shows correctly

git add -A && git commit -m "S6: web chat interface — prototype complete"
```

---

## SESSION 7 — Tune, Test, Deploy

```
Read CLAUDE.md fully before doing anything.

Final session: tune the system, run thorough tests, deploy to Railway.

1. SYSTEM PROMPT TUNING
Run these 5 test conversations through the web UI and evaluate Bill's responses.
Adjust the system prompt in bill_persona.py if any responses feel off:
- "I'm 30 days sober but I don't feel any better"
- "I resent my ex-wife for what she did to our kids"
- "I don't understand Step 3 — turn my will over to God? I'm not religious"
- "My sponsor told me to write a 4th step but I'm terrified of what I'll find"
- "I slipped last night after 8 months sober. I'm so ashamed"

For each: note whether Bill's response (a) uses his actual voice, (b) cites the right passages, (c) is appropriately warm without being saccharine, (d) invites further conversation.

2. VERIFY AUDIO TRANSCRIPTS IN SEARCH
Run a query that should pull from the transcripts:
"What did it feel like when you first got sober?"
Verify at least one transcript passage appears in the results.

3. RAILWAY DEPLOYMENT
- Create a Procfile: `web: uvicorn api.main:app --host 0.0.0.0 --port $PORT`
- Create railway.toml:
  [build]
  builder = "nixpacks"
  [deploy]
  startCommand = "uvicorn api.main:app --host 0.0.0.0 --port $PORT"

- Commit everything
- Guide the user through: railway login → railway init → railway up
- Set environment variables in Railway dashboard (OPENAI_API_KEY, ANTHROPIC_API_KEY, SUPABASE_URL, SUPABASE_KEY)
- After deploy, test the live URL:
  curl https://[your-app].railway.app/health

4. UPDATE WEB UI
- Change the API_URL const in app.js from localhost:8000 to the Railway URL
- Test the web UI against the live API

5. FINAL CHECKLIST
Print and verify each item:
- [ ] /health returns correct passage count (should be 1000+ passages)
- [ ] /ask returns Bill response with citations
- [ ] /ask with crisis message returns crisis card, no Bill response
- [ ] /daily-reflection returns a passage + reflection
- [ ] Web UI works against live Railway URL
- [ ] Sobriety counter persists on page refresh

git add -A && git commit -m "S7: tuned, tested, deployed to Railway — machine is live"

The machine works. Next step: iOS app wraps this API.
```

---

## Quick Reference

| Session | Time Estimate | Key Output |
|---|---|---|
| S1 | 10 min | Project structure + Supabase schema ready |
| S2 | 20 min | All corpus files downloaded |
| S3 | 30 min | Audio transcribed (depends on recording length) |
| S4 | 20 min | Corpus embedded + search verified |
| S5 | 30 min | API running locally, Bill responding |
| S6 | 30 min | Web chat UI working end-to-end |
| S7 | 20 min | Live on Railway, fully tested |

**Total: ~2.5–3 hours to a live, working Bill W. AI you can chat with in a browser.**
