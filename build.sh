#!/bin/bash
# ============================================================
# What Would Bill Do? — Overnight Build Script
# Run this before you go to bed. Check build.log in the morning.
# ============================================================

LOG="build.log"
exec > >(tee -a "$LOG") 2>&1

echo ""
echo "============================================================"
echo "  What Would Bill Do? — Overnight Build"
echo "  Started: $(date)"
echo "============================================================"
echo ""

# ── Check .env is configured ────────────────────────────────
if grep -q "PASTE_YOUR" .env 2>/dev/null; then
  echo "❌ ERROR: You haven't filled in your API keys in .env"
  echo "   Open .env and replace the PASTE_YOUR_* placeholders"
  exit 1
fi

if [ ! -f .env ]; then
  echo "❌ ERROR: .env file not found"
  exit 1
fi

echo "✓ .env looks configured"

# ── Check venv ───────────────────────────────────────────────
if [ ! -d "venv" ]; then
  echo ""
  echo "📦 Creating virtual environment..."
  python3 -m venv venv
fi

source venv/bin/activate
echo "✓ venv activated"

# ── Install dependencies ─────────────────────────────────────
echo ""
echo "📦 Installing Python dependencies..."
pip install -q -r requirements.txt
if [ $? -ne 0 ]; then
  echo "❌ pip install failed. Check requirements.txt"
  exit 1
fi
echo "✓ Dependencies installed"

# ── Remind about Supabase schema ─────────────────────────────
echo ""
echo "⚠️  MANUAL STEP REMINDER:"
echo "   If you haven't already, paste supabase/schema.sql"
echo "   into the Supabase SQL Editor and run it."
echo "   (Waiting 10 seconds — press Ctrl+C if you need to do this now)"
sleep 10

# ── Step 1: Download corpus ──────────────────────────────────
echo ""
echo "============================================================"
echo "  STEP 1: Downloading corpus"
echo "  $(date)"
echo "============================================================"
python3 scripts/01_download_corpus.py
if [ $? -ne 0 ]; then
  echo "❌ Corpus download failed. Check error above."
  exit 1
fi
echo "✓ Corpus download complete"

# ── Step 2: Transcribe audio ─────────────────────────────────
echo ""
echo "============================================================"
echo "  STEP 2: Transcribing audio with Whisper"
echo "  $(date)"
echo "============================================================"
python3 scripts/02_transcribe_audio.py
if [ $? -ne 0 ]; then
  echo "⚠️  Audio transcription had errors (non-fatal, continuing)"
fi
echo "✓ Audio transcription done"

# ── Step 3: Clean and chunk ──────────────────────────────────
echo ""
echo "============================================================"
echo "  STEP 3: Cleaning and chunking text"
echo "  $(date)"
echo "============================================================"
python3 scripts/03_clean_and_chunk.py
if [ $? -ne 0 ]; then
  echo "❌ Chunking failed."
  exit 1
fi
echo "✓ Chunking complete"

# ── Step 4: Embed and ingest ─────────────────────────────────
echo ""
echo "============================================================"
echo "  STEP 4: Embedding and ingesting to Supabase"
echo "  $(date)"
echo "============================================================"
# Auto-answer "N" to the re-ingest prompt if data already exists
echo "N" | python3 scripts/04_embed_and_ingest.py
if [ $? -ne 0 ]; then
  echo "❌ Embedding/ingest failed."
  exit 1
fi
echo "✓ Ingest complete"

# ── Step 5: Verify search ────────────────────────────────────
echo ""
echo "============================================================"
echo "  STEP 5: Verifying search"
echo "  $(date)"
echo "============================================================"
python3 scripts/05_verify_search.py
echo "✓ Verification done"

# ── Done ─────────────────────────────────────────────────────
echo ""
echo "============================================================"
echo "  ✅ BUILD COMPLETE"
echo "  Finished: $(date)"
echo "============================================================"
echo ""
echo "To start the API server:"
echo "  source venv/bin/activate"
echo "  uvicorn api.main:app --host 0.0.0.0 --port 8000"
echo ""
echo "Then open web/index.html in your browser to chat with Bill."
echo ""
echo "Check build.log for the full build output."
