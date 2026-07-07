"""
core/retriever.py — Task E: Retrieval

Loads the FAISS vector store and retrieves the most relevant
chunks for a given user query.

Auto-reloads the vector store when it detects changes on disk
so Terminal 1 never needs to be restarted after indexing.

Usage:
    python core/retriever.py "How do I report a security vulnerability?"
"""

import pickle
import argparse
from pathlib import Path

import faiss
from sentence_transformers import SentenceTransformer

# ── project root detection ────────────────────────────────────────────────────
def _find_project_root() -> Path:
    here = Path(__file__).resolve()
    for parent in [here.parent, here.parent.parent, Path.cwd()]:
        if (parent / "data").exists():
            return parent
    return Path.cwd()

PROJECT_ROOT    = _find_project_root()
VECTOR_DIR      = PROJECT_ROOT / "data" / "vector_store"
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
TOP_K_DEFAULT   = 5
MIN_SCORE       = 0.63   # minimum similarity score to include a chunk

# ── singleton cache ───────────────────────────────────────────────────────────
_model            = None
_index            = None
_chunks           = None
_index_last_mtime = 0.0


def _get_index_mtime() -> float:
    idx_path = VECTOR_DIR / "index.faiss"
    try:
        return idx_path.stat().st_mtime
    except FileNotFoundError:
        return 0.0


def _load_resources():
    global _model, _index, _chunks, _index_last_mtime

    if _model is None:
        print("  🤖  Loading embedding model ...")
        _model = SentenceTransformer(EMBEDDING_MODEL)

    current_mtime = _get_index_mtime()
    index_changed = current_mtime > _index_last_mtime

    if _index is None or _chunks is None or index_changed:
        idx_path  = VECTOR_DIR / "index.faiss"
        meta_path = VECTOR_DIR / "metadata.pkl"

        if not idx_path.exists() or not meta_path.exists():
            raise FileNotFoundError(
                f"Vector store not found at {VECTOR_DIR}. "
                "Run core/embedder.py first."
            )

        if index_changed and _index is not None:
            print("  🔄  Vector store updated — reloading ...")
        else:
            print("  📦  Loading vector store ...")

        _index = faiss.read_index(str(idx_path))
        with open(meta_path, "rb") as f:
            _chunks = pickle.load(f)

        _index_last_mtime = current_mtime
        print(f"  ✅  {_index.ntotal} vectors loaded")

    return _model, _index, _chunks


def reload_vector_store():
    """Force reload the vector store from disk after reindexing."""
    global _index, _chunks, _index_last_mtime
    _index            = None
    _chunks           = None
    _index_last_mtime = 0.0
    print("  🔄  Vector store cache cleared — will reload on next query")


# =============================================================================
# RETRIEVAL
# =============================================================================

def retrieve(query: str,
             top_k: int     = TOP_K_DEFAULT,
             min_score: float = MIN_SCORE) -> list[dict]:
    """
    Retrieve the top_k most relevant chunks for a query.
    Filters out chunks below min_score threshold to avoid
    irrelevant citations from unrelated documents.

    Returns a list of dicts:
      { rank, score, id, source, title, text }
    """
    model, index, chunks = _load_resources()

    prefixed  = f"Represent this sentence for searching relevant passages: {query}"
    query_vec = model.encode(
        [prefixed],
        normalize_embeddings=True,
        convert_to_numpy=True,
    ).astype("float32")

    scores, indices = index.search(query_vec, top_k)

    results = []
    rank    = 1
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue
        # Filter out low relevance chunks
        if float(score) < min_score:
            continue
        chunk = chunks[int(idx)]
        results.append({
            "rank":   rank,
            "score":  round(float(score), 4),
            "id":     chunk["id"],
            "source": chunk["source"],
            "title":  chunk.get("title", chunk["source"]),
            "text":   chunk["text"],
        })
        rank += 1

    return results


def format_context(results: list[dict]) -> str:
    parts = []
    for r in results:
        parts.append(
            f"[Source {r['rank']}: {r['title']} ({r['source']})]\n{r['text']}"
        )
    return "\n\n---\n\n".join(parts)


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Retrieve relevant chunks for a query")
    parser.add_argument("query",   type=str, help="Question to search for")
    parser.add_argument("--top-k", type=int, default=TOP_K_DEFAULT)
    parser.add_argument("--min-score", type=float, default=MIN_SCORE)
    args = parser.parse_args()

    print(f"\n🔍  Query: '{args.query}'\n")
    results = retrieve(args.query, top_k=args.top_k, min_score=args.min_score)

    if not results:
        print(f"  ⚠️  No chunks found above min_score={args.min_score}")
    else:
        for r in results:
            print(f"  {r['rank']}. [{r['score']}] {r['title']}  ({r['source']})")
            print(f"     {r['text'][:150].strip()}...")
            print()
