"""
Script 02 — Transcribe audio files with OpenAI Whisper
Handles files >25MB by splitting with pydub
"""

import os, json, math
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

AUDIO_DIR = Path("corpus/audio")
TRANSCRIPT_DIR = Path("corpus/transcripts")
TRANSCRIPT_DIR.mkdir(parents=True, exist_ok=True)

AUDIO_EXTS = {".mp3", ".m4a", ".wav", ".ogg", ".flac"}
MAX_BYTES = 24 * 1024 * 1024  # 24MB safety margin (Whisper limit is 25MB)


def transcribe_file(audio_path: Path) -> str:
    """Transcribe a single audio file, splitting if >24MB."""
    size = audio_path.stat().st_size

    if size <= MAX_BYTES:
        print(f"  Transcribing {audio_path.name} ({size//1024}KB)...")
        with open(audio_path, "rb") as f:
            result = client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                language="en"
            )
        return result.text

    # File too large — split with pydub
    print(f"  {audio_path.name} is {size//1024//1024}MB — splitting...")
    try:
        from pydub import AudioSegment
    except ImportError:
        print("  Installing pydub...")
        os.system("pip install pydub")
        from pydub import AudioSegment

    audio = AudioSegment.from_file(audio_path)
    duration_ms = len(audio)
    # Estimate chunk duration based on file size ratio
    chunk_ms = int(duration_ms * MAX_BYTES / size * 0.9)
    chunks = math.ceil(duration_ms / chunk_ms)
    print(f"  Splitting into {chunks} chunks...")

    full_transcript = []
    for i in range(chunks):
        start = i * chunk_ms
        end = min((i + 1) * chunk_ms, duration_ms)
        chunk = audio[start:end]

        chunk_path = audio_path.parent / f"_chunk_{i}_{audio_path.name}"
        chunk.export(chunk_path, format="mp3")

        try:
            with open(chunk_path, "rb") as f:
                result = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=f,
                    language="en"
                )
            full_transcript.append(result.text)
            print(f"  ✓ chunk {i+1}/{chunks}")
        finally:
            chunk_path.unlink(missing_ok=True)

    return " ".join(full_transcript)


def main():
    audio_files = [f for f in AUDIO_DIR.iterdir() if f.suffix.lower() in AUDIO_EXTS]

    if not audio_files:
        print("No audio files found in corpus/audio/ — skipping transcription")
        return

    print(f"\n🎙️  Transcribing {len(audio_files)} audio files with Whisper...")

    for audio_path in sorted(audio_files):
        transcript_path = TRANSCRIPT_DIR / (audio_path.stem + ".txt")
        meta_path = TRANSCRIPT_DIR / (audio_path.stem + "_meta.json")

        if transcript_path.exists():
            print(f"  ✓ skip {audio_path.name} (already transcribed)")
            continue

        try:
            text = transcribe_file(audio_path)
            transcript_path.write_text(text, encoding="utf-8")

            meta = {
                "source_file": audio_path.name,
                "source": "transcript",
                "title": audio_path.stem.replace("_", " ").replace("-", " "),
                "char_count": len(text),
                "word_count": len(text.split())
            }
            meta_path.write_text(json.dumps(meta, indent=2))

            print(f"  ✓ {audio_path.name} → {len(text.split())} words")

        except Exception as e:
            print(f"  ✗ FAILED {audio_path.name}: {e}")

    print(f"\n✅ Transcription complete. Files in corpus/transcripts/")


if __name__ == "__main__":
    main()
