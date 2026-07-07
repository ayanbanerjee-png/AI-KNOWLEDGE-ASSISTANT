"""
core/embedder.py — Task D + E: Embeddings & Incremental Vector Index

Two modes:
  --full   : rebuild entire index from scratch (default first time)
  --update : only index NEW files not yet in the vector store (incremental)

Usage:
    python core/embedder.py           # full rebuild
    python core/embedder.py --update  # incremental (only new files)
"""

import json
import pickle
import argparse
import numpy as np
from pathlib import Path

from sentence_transformers import SentenceTransformer
import faiss

# ── project root detection ────────────────────────────────────────────────────
def _find_project_root() -> Path:
    here = Path(__file__).resolve()
    for parent in [here.parent, here.parent.parent, Path.cwd()]:
        if (parent / "data").exists():
            return parent
    return Path.cwd()

PROJECT_ROOT   = _find_project_root()
PROCESSED_DIR  = PROJECT_ROOT / "data" / "processed"
VECTOR_DIR     = PROJECT_ROOT / "data" / "vector_store"
REGISTRY_FILE  = VECTOR_DIR / "indexed_files.json"  # tracks what's been indexed

EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
EMBEDDING_DIM   = 384
INDEX_FILE      = "index.faiss"
METADATA_FILE   = "metadata.pkl"


# =============================================================================
# REGISTRY — tracks which files have already been indexed
# =============================================================================

def load_registry() -> set:
    """Load set of already-indexed filenames."""
    if REGISTRY_FILE.exists():
        return set(json.loads(REGISTRY_FILE.read_text()))
    return set()


def save_registry(indexed: set):
    REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY_FILE.write_text(json.dumps(sorted(indexed), indent=2))


# =============================================================================
# LOAD CHUNKS
# =============================================================================

def load_chunks_from_files(files: list[Path]) -> list[dict]:
    """Load chunks from a specific list of .chunks.json files."""
    chunks = []
    for path in files:
        doc      = json.loads(path.read_text(encoding="utf-8"))
        source   = doc.get("source", path.stem)
        metadata = doc.get("metadata", {})
        for chunk in doc.get("chunks", []):
            chunks.append({
                "id":     chunk["id"],
                "index":  chunk["index"],
                "text":   chunk["text"],
                "source": source,
                "title":  metadata.get("title", source),
                "tags":   metadata.get("tags", []),
                "type":   metadata.get("type", ""),
                "date":   metadata.get("date", ""),
            })
    return chunks


# =============================================================================
# EMBED
# =============================================================================

def embed_chunks(chunks: list[dict], model: SentenceTransformer) -> np.ndarray:
    if not chunks:
        return np.empty((0, EMBEDDING_DIM), dtype="float32")

    texts = [c["text"] for c in chunks]
    print(f"  🔢  Embedding {len(texts)} chunks ...")
    embeddings = model.encode(
        texts,
        batch_size=32,
        show_progress_bar=True,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )
    return embeddings.astype("float32")


# =============================================================================
# SAVE / LOAD VECTOR STORE
# =============================================================================

def save_vector_store(index, chunks: list[dict]):
    VECTOR_DIR.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(VECTOR_DIR / INDEX_FILE))
    with open(VECTOR_DIR / METADATA_FILE, "wb") as f:
        pickle.dump(chunks, f)


def load_vector_store():
    """Load existing index and chunks. Returns (None, []) if not found."""
    idx_path  = VECTOR_DIR / INDEX_FILE
    meta_path = VECTOR_DIR / METADATA_FILE
    if not idx_path.exists() or not meta_path.exists():
        return None, []
    index = faiss.read_index(str(idx_path))
    with open(meta_path, "rb") as f:
        chunks = pickle.load(f)
    return index, chunks


# =============================================================================
# FULL REBUILD
# =============================================================================

def build_full(processed_dir: Path = PROCESSED_DIR):
    print(f"\n🔄  Full rebuild — indexing all documents\n")

    all_files = sorted(processed_dir.glob("*.chunks.json"))
    if not all_files:
        print(f"  ⚠️  No .chunks.json files found in {processed_dir}")
        return

    chunks = load_chunks_from_files(all_files)
    if not chunks:
        print("  No chunks found in processed files")
        return
    print(f"  📂  {len(chunks)} chunks from {len(all_files)} documents\n")

    model      = SentenceTransformer(EMBEDDING_MODEL)
    embeddings = embed_chunks(chunks, model)

    index = faiss.IndexFlatIP(EMBEDDING_DIM)
    index.add(embeddings)

    save_vector_store(index, chunks)
    save_registry({f.name for f in all_files})

    print(f"\n  📦  Index built: {index.ntotal} vectors")
    print(f"  💾  Saved to {VECTOR_DIR}/")
    print(f"\n✅  Full rebuild complete\n")


# =============================================================================
# INCREMENTAL UPDATE — only index new files
# =============================================================================

def build_incremental(processed_dir: Path = PROCESSED_DIR):
    print(f"\n🔄  Incremental update — checking for new files\n")

    all_files  = sorted(processed_dir.glob("*.chunks.json"))
    registry   = load_registry()
    new_files  = [f for f in all_files if f.name not in registry]

    if not new_files:
        print("  ✅  No new files to index — everything is up to date!\n")
        return

    print(f"  📂  Found {len(new_files)} new file(s) to index:")
    for f in new_files:
        print(f"      + {f.name}")
    print()

    # Load new chunks
    new_chunks = load_chunks_from_files(new_files)
    if not new_chunks:
        print("  New processed files did not contain any chunks")
        return

    # Load existing index + chunks
    index, existing_chunks = load_vector_store()

    # Embed new chunks
    model      = SentenceTransformer(EMBEDDING_MODEL)
    embeddings = embed_chunks(new_chunks, model)

    if index is None:
        # No existing index — create fresh
        index = faiss.IndexFlatIP(EMBEDDING_DIM)

    # Add new vectors to existing index
    index.add(embeddings)
    all_chunks = existing_chunks + new_chunks

    # Save updated index
    save_vector_store(index, all_chunks)

    # Update registry
    updated_registry = registry | {f.name for f in new_files}
    save_registry(updated_registry)

    print(f"\n  📦  Index updated: {index.ntotal} total vectors")
    print(f"  ➕  Added: {len(new_chunks)} new chunks")
    print(f"  💾  Saved to {VECTOR_DIR}/")
    print(f"\n✅  Incremental update complete\n")


# =============================================================================
# SEARCH (used by retriever)
# =============================================================================

def search(query: str, model: SentenceTransformer, index, chunks: list,
           top_k: int = 5) -> list[dict]:
    prefixed  = f"Represent this sentence for searching relevant passages: {query}"
    query_vec = model.encode(
        [prefixed], normalize_embeddings=True, convert_to_numpy=True
    ).astype("float32")

    scores, indices = index.search(query_vec, top_k)
    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue
        chunk = chunks[int(idx)]
        results.append({
            "score":  float(score),
            "id":     chunk["id"],
            "source": chunk["source"],
            "title":  chunk["title"],
            "text":   chunk["text"],
        })
    return results


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build or update FAISS vector index")
    parser.add_argument("--update", action="store_true",
                        help="Incremental mode — only index new files")
    parser.add_argument("--processed", type=Path, default=PROCESSED_DIR)
    args = parser.parse_args()

    if args.update:
        build_incremental(processed_dir=args.processed)
    else:
        build_full(processed_dir=args.processed)
