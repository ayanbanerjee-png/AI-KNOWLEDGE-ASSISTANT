"""
core/ingestor.py — Task C: Ingestion & Normalization Pipeline

Reads documents from data/raw/, cleans and chunks them,
then saves processed chunks + metadata to data/processed/.

Supported formats: .md, .pdf, .docx, .csv

Usage (from your project root):
    python core/ingestor.py
    python core/ingestor.py --raw data/raw --out data/processed
"""

import re
import csv
import json
import hashlib
import argparse
from pathlib import Path
from datetime import datetime

# ── optional parsers (graceful fallback if not installed) ────────────────────
try:
    import fitz          # PyMuPDF  →  pip install pymupdf
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

try:
    import docx          # python-docx  →  pip install python-docx
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False


# ── project root detection ────────────────────────────────────────────────────
def _find_project_root() -> Path:
    """Walk up from this file until we find a directory containing data/."""
    here = Path(__file__).resolve()
    for parent in [here.parent, here.parent.parent, Path.cwd()]:
        if (parent / "data").exists():
            return parent
    return Path.cwd()

PROJECT_ROOT  = _find_project_root()
RAW_DIR       = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

# ── chunking config ───────────────────────────────────────────────────────────
CHUNK_SIZE    = 800    # target tokens per chunk  (approx 4 chars = 1 token)
CHUNK_OVERLAP = 100    # overlap between consecutive chunks in tokens
CHARS_PER_TOK = 4


# =============================================================================
# 1. PARSERS
# =============================================================================

def parse_markdown(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def parse_pdf(path: Path) -> str:
    if not HAS_PYMUPDF:
        print(f"  ⚠️  PyMuPDF not installed — skipping {path.name}")
        return ""
    doc   = fitz.open(str(path))
    pages = [page.get_text() for page in doc]
    doc.close()
    return "\n".join(pages)


def parse_docx(path: Path) -> str:
    if not HAS_DOCX:
        print(f"  ⚠️  python-docx not installed — skipping {path.name}")
        return ""
    document = docx.Document(str(path))
    return "\n".join(p.text for p in document.paragraphs if p.text.strip())


def parse_csv(path: Path) -> str:
    lines = []
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            parts = ", ".join(f"{k}: {v}" for k, v in row.items() if str(v).strip())
            if parts:
                lines.append(parts)
    return "\n".join(lines)


PARSERS = {
    ".md":   parse_markdown,
    ".pdf":  parse_pdf,
    ".docx": parse_docx,
    ".csv":  parse_csv,
}


# =============================================================================
# 2. CLEANING
# =============================================================================

def clean_text(text: str) -> str:
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^[-*_]{3,}\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"\*{1,3}(.+?)\*{1,3}", r"\1", text)
    text = re.sub(r"_{1,2}(.+?)_{1,2}",   r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"```[a-zA-Z]*\n?", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"^\|[-| :]+\|$", "", text, flags=re.MULTILINE)
    text = re.sub(r"\n{3,}", "\n\n", text)
    lines = [l.strip() for l in text.splitlines()]
    lines = [l for l in lines if len(l) > 2]
    return "\n".join(lines).strip()


# =============================================================================
# 3. CHUNKING
# =============================================================================

def chunk_text(text: str,
               chunk_size: int = CHUNK_SIZE,
               overlap: int    = CHUNK_OVERLAP) -> list:
    char_size    = chunk_size * CHARS_PER_TOK
    char_overlap = overlap    * CHARS_PER_TOK

    paragraphs = [p.strip() for p in re.split(r"\n\n+", text) if p.strip()]
    chunks  = []
    current = ""

    for para in paragraphs:
        if len(current) + len(para) + 2 <= char_size:
            current = (current + "\n\n" + para).strip()
        else:
            if current:
                chunks.append(current)
            if char_overlap > 0 and current:
                current = (current[-char_overlap:] + "\n\n" + para).strip()
            else:
                current = para

    if current:
        chunks.append(current)

    final = []
    for chunk in chunks:
        if len(chunk) <= char_size * 1.5:
            final.append(chunk)
        else:
            start = 0
            while start < len(chunk):
                final.append(chunk[start: start + char_size].strip())
                start += char_size - char_overlap

    return [c for c in final if len(c) > 50]


# =============================================================================
# 4. METADATA
# =============================================================================

def load_metadata(doc_path: Path) -> dict:
    meta_path = doc_path.with_suffix(".meta.json")
    if meta_path.exists():
        with open(meta_path, encoding="utf-8") as f:
            return json.load(f)
    return {
        "title": doc_path.stem.replace("_", " ").title(),
        "tags":  [],
        "type":  doc_path.suffix.lstrip("."),
        "date":  datetime.today().strftime("%Y-%m-%d"),
    }


# =============================================================================
# 5. STORAGE
# =============================================================================

def make_chunk_id(source_name: str, index: int) -> str:
    return hashlib.md5(f"{source_name}::{index}".encode()).hexdigest()[:12]


def save_chunks(source_name: str, chunks: list, meta: dict, out_dir: Path) -> Path:
    out_name = source_name.rsplit(".", 1)[0] + ".chunks.json"
    out_path = out_dir / out_name

    payload = {
        "source":   source_name,
        "metadata": meta,
        "chunks": [
            {"id": make_chunk_id(source_name, i), "index": i, "text": chunk}
            for i, chunk in enumerate(chunks)
        ],
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    return out_path


# =============================================================================
# 6. PIPELINE
# =============================================================================

def ingest_file(path: Path, out_dir: Path):
    suffix = path.suffix.lower()
    if suffix not in PARSERS:
        return None

    print(f"  📄  {path.name}")

    raw_text = PARSERS[suffix](path)
    if not raw_text.strip():
        print(f"       ⚠️  empty after parsing — skipped")
        return None

    cleaned  = clean_text(raw_text)
    chunks   = chunk_text(cleaned)
    meta     = load_metadata(path)
    out_path = save_chunks(path.name, chunks, meta, out_dir)

    return {"file": path.name, "chunks": len(chunks), "output": out_path.name}


def run_ingestion(raw_dir: Path = RAW_DIR, out_dir: Path = PROCESSED_DIR):
    raw_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n🔄  Ingestion pipeline starting")
    print(f"    Source : {raw_dir}")
    print(f"    Output : {out_dir}\n")

    doc_files = sorted([
        f for f in raw_dir.iterdir()
        if f.is_file()
        and f.suffix.lower() in PARSERS
        and not f.name.endswith(".meta.json")
    ])

    if not doc_files:
        print(f"  ⚠️  No supported documents found in {raw_dir}")
        return []

    results = []
    for path in doc_files:
        result = ingest_file(path, out_dir)
        if result:
            results.append(result)

    total_chunks = sum(r["chunks"] for r in results)
    print(f"\n✅  Ingestion complete")
    print(f"    Documents : {len(results)}")
    print(f"    Chunks    : {total_chunks}\n")
    print(f"  {'File':<40} {'Chunks':>6}  Output")
    print(f"  {'-'*68}")
    for r in results:
        print(f"  {r['file']:<40} {r['chunks']:>6}  {r['output']}")
    print()

    return results


# =============================================================================
# 7. CLI
# =============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest and chunk documents")
    parser.add_argument("--raw", type=Path, default=RAW_DIR,
                        help="Folder containing raw documents")
    parser.add_argument("--out", type=Path, default=PROCESSED_DIR,
                        help="Folder to write processed chunks")
    args = parser.parse_args()
    run_ingestion(raw_dir=args.raw, out_dir=args.out)
