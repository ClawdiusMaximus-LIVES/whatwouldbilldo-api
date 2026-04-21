"""
What Would Bill Do? — Corpus Downloader
Run: python download_corpus.py
Requires: pip install requests beautifulsoup4
"""

import os, time, requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# ── Folders ──────────────────────────────────────────────────────────────────
os.makedirs("corpus/raw/bigbook_1939", exist_ok=True)
os.makedirs("corpus/raw/manuscript_1938", exist_ok=True)
os.makedirs("corpus/raw/grapevine", exist_ok=True)
os.makedirs("corpus/raw/talks", exist_ok=True)
os.makedirs("corpus/raw/letters", exist_ok=True)
os.makedirs("corpus/audio", exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0 (research/corpus-builder)"}
session = requests.Session()
session.headers.update(HEADERS)

def fetch(url):
    try:
        r = session.get(url, timeout=20)
        r.raise_for_status()
        return r
    except Exception as e:
        print(f"  ✗ FAILED {url}: {e}")
        return None

def save_html(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def save_bytes(path, content):
    with open(path, "wb") as f:
        f.write(content)

# ── 1. Big Book 1939 — anonpress.org/bb/ ─────────────────────────────────────
print("\n📖 Big Book 1939 (anonpress.org/bb/)")
BB_BASE = "https://anonpress.org/bb/"
BB_CHAPTERS = {
    "foreword":     "Page_xiii.htm",   # foreword
    "doctors_opinion": "Page_xxiii.htm",
    "ch01_bills_story":         "Page_1.htm",
    "ch02_there_is_a_solution": "Page_17.htm",
    "ch03_more_about_alcoholism": "Page_30.htm",
    "ch04_we_agnostics":        "Page_44.htm",
    "ch05_how_it_works":        "Page_58.htm",
    "ch06_into_action":         "Page_72.htm",
    "ch07_working_with_others": "Page_89.htm",
    "ch08_to_wives":            "Page_104.htm",
    "ch09_the_family_afterward":"Page_122.htm",
    "ch10_to_employers":        "Page_136.htm",
    "ch11_a_vision_for_you":    "Page_151.htm",
    "spiritual_experience":     "Page_569.htm",
    "doctors_nightmare":        "Page_171.htm",
}

# Also try to auto-discover any chapters we might have missed
index = fetch(BB_BASE)
if index:
    soup = BeautifulSoup(index.text, "html.parser")
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("Page_") and href not in BB_CHAPTERS.values():
            slug = href.replace(".htm", "").lower()
            BB_CHAPTERS[slug] = href

for name, page in BB_CHAPTERS.items():
    path = f"corpus/raw/bigbook_1939/{name}.html"
    if os.path.exists(path):
        print(f"  ✓ skip {name} (exists)")
        continue
    r = fetch(BB_BASE + page)
    if r:
        save_html(path, r.text)
        print(f"  ✓ {name}")
    time.sleep(0.5)

# ── 2. Original Manuscript 1938 — anonpress.org/manu/ ────────────────────────
print("\n📜 Original Manuscript 1938 (anonpress.org/manu/)")
MANU_BASE = "https://anonpress.org/manu/"
MANU_CHAPTERS = {
    "foreword":          "foreword.htm",
    "doctors_opinion":   "docsopin.htm",
    "ch01_bills_story":  "01.htm",
    "ch02_solution":     "02.htm",
    "ch03_more_about":   "03.htm",
    "ch04_agnostics":    "04.htm",
    "ch05_how_it_works": "05.htm",
    "ch06_into_action":  "06.htm",
    "ch07_working_with": "07.htm",
    "ch08_to_wives":     "08.htm",
    "ch09_family":       "09.htm",
    "ch10_employers":    "10.htm",
    "ch11_vision":       "11.htm",
    "doctors_nightmare": "drbob.htm",
    "ace_full_seven_eleven": "ace.htm",    # manuscript-only story
    "alcoholic_foundation":  "alcfound.htm",
}

for name, page in MANU_CHAPTERS.items():
    path = f"corpus/raw/manuscript_1938/{name}.html"
    if os.path.exists(path):
        print(f"  ✓ skip {name} (exists)")
        continue
    r = fetch(MANU_BASE + page)
    if r:
        save_html(path, r.text)
        print(f"  ✓ {name}")
    time.sleep(0.5)

# ── 3. AA Traditions Pamphlet (P-17) PDF ─────────────────────────────────────
print("\n📄 AA Traditions Pamphlet (P-17)")
p17_path = "corpus/raw/p17_traditions.pdf"
if not os.path.exists(p17_path):
    r = fetch("https://www.aa.org/sites/default/files/literature/assets/p-17_AATraditions.pdf")
    if r:
        save_bytes(p17_path, r.content)
        print(f"  ✓ p17_traditions.pdf ({len(r.content)//1024}KB)")
else:
    print("  ✓ skip (exists)")

# ── 4. Grapevine Articles ─────────────────────────────────────────────────────
print("\n📰 Grapevine Articles (silkworth.net)")
GV_INDEX = "https://silkworth.net/aa/writings-of-a-a-members/bill-w/grapevine-articles-of-bill-w/"
r = fetch(GV_INDEX)
gv_count = 0
if r:
    soup = BeautifulSoup(r.text, "html.parser")
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "silkworth.net" in href and href not in [GV_INDEX]:
            links.append(href)
        elif href.startswith("/") and "grapevine" in href.lower():
            links.append("https://silkworth.net" + href)

    # deduplicate
    links = list(dict.fromkeys(links))
    print(f"  Found {len(links)} article links")

    for url in links:
        slug = url.rstrip("/").split("/")[-1][:60]
        path = f"corpus/raw/grapevine/{slug}.html"
        if os.path.exists(path):
            continue
        art = fetch(url)
        if art:
            save_html(path, art.text)
            gv_count += 1
            print(f"  ✓ {slug}")
        time.sleep(1)

# ── 5. Talk Transcripts ───────────────────────────────────────────────────────
print("\n🎙️ Talk Transcripts (silkworth.net)")
TALKS = [
    ("transcript_general",  "https://silkworth.net/alcoholics-anonymous/transcript-of-talk-given-by-bill-w/"),
    ("talk_manhattan",      "https://silkworth.net/alcoholics-anonymous/bill-w-s-talk-to-the-manhattan-group/"),
    ("talks_gsc",           "https://silkworth.net/aa/writings-of-a-a-members/bill-w/talks-at-general-service-conferences/"),
]
for name, url in TALKS:
    path = f"corpus/raw/talks/{name}.html"
    if os.path.exists(path):
        print(f"  ✓ skip {name}")
        continue
    r = fetch(url)
    if r:
        save_html(path, r.text)
        print(f"  ✓ {name}")
    time.sleep(1)

# ── 6. Letters ────────────────────────────────────────────────────────────────
print("\n✉️  Letters (silkworth.net)")
LETTERS = [
    ("letters_jim_burwell", "https://silkworth.net/aa/writings-of-a-a-members/bill-w/letters-to-jim-burwell-from-bill-wilson/"),
    ("letter_carl_jung",    "https://silkworth.net/alcoholics-anonymous/bill-w-s-letter-to-dr-carl-gustav-jung/"),
]
for name, url in LETTERS:
    path = f"corpus/raw/letters/{name}.html"
    if os.path.exists(path):
        print(f"  ✓ skip {name}")
        continue
    r = fetch(url)
    if r:
        save_html(path, r.text)
        print(f"  ✓ {name}")
    time.sleep(1)

# ── 7. Audio Files ────────────────────────────────────────────────────────────
print("\n🔊 Audio Files (silkworth.net)")
AUDIO_INDEX = "https://silkworth.net/aa/audio-books/aa-speaker-bill-w/"
r = fetch(AUDIO_INDEX)
audio_count = 0
if r:
    soup = BeautifulSoup(r.text, "html.parser")
    audio_exts = (".mp3", ".m4a", ".ogg", ".wav", ".flac")
    audio_links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if any(href.lower().endswith(ext) for ext in audio_exts):
            full = urljoin(AUDIO_INDEX, href)
            audio_links.append(full)

    print(f"  Found {len(audio_links)} audio files")
    for url in audio_links:
        filename = url.split("/")[-1]
        path = f"corpus/audio/{filename}"
        if os.path.exists(path):
            print(f"  ✓ skip {filename} (exists)")
            continue
        print(f"  ↓ {filename}...", end="", flush=True)
        r2 = fetch(url)
        if r2:
            save_bytes(path, r2.content)
            print(f" {len(r2.content)//1024}KB ✓")
            audio_count += 1
        time.sleep(1)

# ── Summary ───────────────────────────────────────────────────────────────────
print("\n" + "="*50)
print("DOWNLOAD COMPLETE")
print("="*50)

for folder, label in [
    ("corpus/raw/bigbook_1939", "Big Book chapters"),
    ("corpus/raw/manuscript_1938", "Manuscript chapters"),
    ("corpus/raw/grapevine", "Grapevine articles"),
    ("corpus/raw/talks", "Talk transcripts"),
    ("corpus/raw/letters", "Letters"),
    ("corpus/audio", "Audio files"),
]:
    if os.path.exists(folder):
        files = os.listdir(folder)
        size = sum(os.path.getsize(f"{folder}/{f}") for f in files) // 1024
        print(f"  {label}: {len(files)} files ({size}KB)")

print("\nNext step: run the clean+chunk+embed script (S4)")
