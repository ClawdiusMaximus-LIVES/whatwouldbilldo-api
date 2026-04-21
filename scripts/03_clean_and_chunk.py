"""
Script 03 — Clean raw text and chunk into ~250-token pieces with ~30-token overlap.
Outputs JSONL files to corpus/processed/
"""

import os, json, re
from pathlib import Path
import tiktoken
from bs4 import BeautifulSoup

PROCESSED_DIR = Path("corpus/processed")
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

enc = tiktoken.get_encoding("cl100k_base")
TARGET_TOKENS = 250
OVERLAP_TOKENS = 30


# ── Text cleaners ─────────────────────────────────────────────────────────────

def clean_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    # Remove nav, footer, header, scripts, styles
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    return clean_text(text)


def clean_text(text: str) -> str:
    # Normalize whitespace
    text = re.sub(r'\r\n', '\n', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    # Remove page numbers and running headers (common in scanned PDFs)
    text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)
    text = text.strip()
    return text


# ── Chunker ───────────────────────────────────────────────────────────────────

def chunk_text(text: str, source: str, chapter: str = None, title: str = None,
               date_written: str = None) -> list[dict]:
    """Split text into overlapping chunks of ~250 tokens, respecting paragraphs."""
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    chunks = []
    current_tokens = []
    current_text = []
    chunk_index = 0

    def flush(tokens, texts):
        nonlocal chunk_index
        content = ' '.join(texts).strip()
        if len(tokens) < 20:  # skip tiny fragments
            return
        chunks.append({
            "content": content,
            "source": source,
            "chapter": chapter,
            "title": title,
            "date_written": date_written,
            "chunk_index": chunk_index,
            "token_count": len(tokens)
        })
        chunk_index += 1

    for para in paragraphs:
        para_tokens = enc.encode(para)

        # If adding this paragraph exceeds target, flush current and start new
        if len(current_tokens) + len(para_tokens) > TARGET_TOKENS and current_tokens:
            flush(current_tokens, current_text)

            # Overlap: keep last OVERLAP_TOKENS worth of content
            overlap_tokens = current_tokens[-OVERLAP_TOKENS:]
            overlap_text = enc.decode(overlap_tokens)
            current_tokens = overlap_tokens
            current_text = [overlap_text]

        # If a single paragraph exceeds target, split it by sentences
        if len(para_tokens) > TARGET_TOKENS:
            sentences = re.split(r'(?<=[.!?])\s+', para)
            for sent in sentences:
                sent_tokens = enc.encode(sent)
                if len(current_tokens) + len(sent_tokens) > TARGET_TOKENS and current_tokens:
                    flush(current_tokens, current_text)
                    overlap_tokens = current_tokens[-OVERLAP_TOKENS:]
                    current_tokens = overlap_tokens
                    current_text = [enc.decode(overlap_tokens)]
                current_tokens += sent_tokens
                current_text.append(sent)
        else:
            current_tokens += para_tokens
            current_text.append(para)

    if current_tokens:
        flush(current_tokens, current_text)

    return chunks


# ── Process each source type ──────────────────────────────────────────────────

def process_bigbook():
    src_dir = Path("corpus/raw/bigbook_1939")
    if not src_dir.exists():
        return []
    all_chunks = []
    for f in sorted(src_dir.glob("*.html")):
        chapter_name = f.stem.replace("_", " ").title()
        text = clean_html(f.read_text(encoding="utf-8", errors="ignore"))
        chunks = chunk_text(text, source="big_book_1939", chapter=chapter_name,
                            date_written="1939")
        all_chunks.extend(chunks)
        print(f"  big_book_1939/{f.name}: {len(chunks)} chunks")
    return all_chunks


def process_manuscript():
    src_dir = Path("corpus/raw/manuscript_1938")
    if not src_dir.exists():
        return []
    all_chunks = []
    for f in sorted(src_dir.glob("*.html")):
        chapter_name = f.stem.replace("_", " ").title()
        text = clean_html(f.read_text(encoding="utf-8", errors="ignore"))
        chunks = chunk_text(text, source="manuscript_1938", chapter=chapter_name,
                            date_written="1938")
        all_chunks.extend(chunks)
        print(f"  manuscript_1938/{f.name}: {len(chunks)} chunks")
    return all_chunks


def process_grapevine():
    src_dir = Path("corpus/raw/grapevine")
    if not src_dir.exists():
        return []
    all_chunks = []
    for f in sorted(src_dir.glob("*.html")):
        text = clean_html(f.read_text(encoding="utf-8", errors="ignore"))
        title = f.stem.replace("-", " ").replace("_", " ").title()
        chunks = chunk_text(text, source="grapevine", title=title,
                            date_written="1944-1970")
        all_chunks.extend(chunks)
        print(f"  grapevine/{f.name}: {len(chunks)} chunks")
    return all_chunks


def process_talks():
    src_dir = Path("corpus/raw/talks")
    if not src_dir.exists():
        return []
    all_chunks = []
    for f in sorted(src_dir.glob("*.html")):
        text = clean_html(f.read_text(encoding="utf-8", errors="ignore"))
        title = f.stem.replace("_", " ").title()
        chunks = chunk_text(text, source="talk", title=title)
        all_chunks.extend(chunks)
        print(f"  talks/{f.name}: {len(chunks)} chunks")
    return all_chunks


def process_letters():
    src_dir = Path("corpus/raw/letters")
    if not src_dir.exists():
        return []
    all_chunks = []
    for f in sorted(src_dir.glob("*.html")):
        text = clean_html(f.read_text(encoding="utf-8", errors="ignore"))
        title = f.stem.replace("_", " ").title()
        chunks = chunk_text(text, source="letter", title=title)
        all_chunks.extend(chunks)
        print(f"  letters/{f.name}: {len(chunks)} chunks")
    return all_chunks


def process_transcripts():
    src_dir = Path("corpus/transcripts")
    if not src_dir.exists():
        return []
    all_chunks = []
    for f in sorted(src_dir.glob("*.txt")):
        text = clean_text(f.read_text(encoding="utf-8", errors="ignore"))
        title = f.stem.replace("_", " ").replace("-", " ").title()
        chunks = chunk_text(text, source="transcript", title=title)
        all_chunks.extend(chunks)
        print(f"  transcripts/{f.name}: {len(chunks)} chunks")
    return all_chunks


def process_pdfs():
    """Extract text from PDFs (traditions pamphlet, etc.)"""
    try:
        import pdfplumber
    except ImportError:
        print("  pdfplumber not found, skipping PDFs")
        return []

    all_chunks = []
    for f in Path("corpus/raw").glob("*.pdf"):
        print(f"  PDF: {f.name}...")
        try:
            with pdfplumber.open(f) as pdf:
                pages = [p.extract_text() or "" for p in pdf.pages]
                text = clean_text("\n\n".join(pages))
            source = "traditions" if "p17" in f.name else "other"
            chunks = chunk_text(text, source=source, title=f.stem)
            all_chunks.extend(chunks)
            print(f"    {len(chunks)} chunks")
        except Exception as e:
            print(f"  ✗ {f.name}: {e}")
    return all_chunks


def main():
    print("\n🔪 Cleaning and chunking corpus...")

    all_chunks = []
    all_chunks.extend(process_bigbook())
    all_chunks.extend(process_manuscript())
    all_chunks.extend(process_grapevine())
    all_chunks.extend(process_talks())
    all_chunks.extend(process_letters())
    all_chunks.extend(process_transcripts())
    all_chunks.extend(process_pdfs())

    # Write to JSONL
    output_path = PROCESSED_DIR / "all_chunks.jsonl"
    with open(output_path, "w", encoding="utf-8") as f:
        for chunk in all_chunks:
            f.write(json.dumps(chunk) + "\n")

    # Summary
    by_source = {}
    for c in all_chunks:
        by_source[c["source"]] = by_source.get(c["source"], 0) + 1

    print(f"\n✅ Total chunks: {len(all_chunks)}")
    print(f"   Saved to: {output_path}")
    for src, count in sorted(by_source.items()):
        print(f"   {src}: {count} chunks")

    token_total = sum(c["token_count"] for c in all_chunks)
    print(f"   Total tokens: {token_total:,} (~${token_total/1_000_000*0.02:.4f} to embed)")


if __name__ == "__main__":
    main()
