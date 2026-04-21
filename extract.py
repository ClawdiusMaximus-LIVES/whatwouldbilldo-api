import json
import pathlib
import re

import pdfplumber

HERE = pathlib.Path(__file__).parent
OUT = HERE / "extracted"
OUT.mkdir(exist_ok=True)


def clean(text: str) -> str:
    text = text.replace("\u00ad", "")
    text = re.sub(r"(\w+)-\n(\w+)", r"\1\2", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


for pdf_path in sorted(HERE.glob("*.pdf")):
    print(f"→ {pdf_path.name}")
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            raw = page.extract_text(x_tolerance=2, y_tolerance=3) or ""
            pages.append({"page": i, "text": clean(raw)})

    stem = pdf_path.stem
    (OUT / f"{stem}.txt").write_text(
        "\n\n".join(f"[page {p['page']}]\n{p['text']}" for p in pages)
    )
    (OUT / f"{stem}.jsonl").write_text(
        "\n".join(
            json.dumps({"source": pdf_path.name, **p}, ensure_ascii=False)
            for p in pages
        )
    )
    print(f"  {len(pages)} pages → {stem}.txt, {stem}.jsonl")
