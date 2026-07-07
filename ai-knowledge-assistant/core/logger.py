"""
core/logger.py — Task G: Evaluation & Logging

Logs every query to SQLite and provides evaluation metrics:
  - Recall@k
  - Citation coverage
  - Answer grounding (overlap with retrieved context)
  - Latency tracking
  - Visualization with Matplotlib

Usage:
    from core.logger import log_query, evaluate, visualize
"""

import os
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional

def _find_project_root() -> Path:
    here = Path(__file__).resolve()
    for parent in [here.parent, here.parent.parent, Path.cwd()]:
        if (parent / "data").exists():
            return parent
    return Path.cwd()

PROJECT_ROOT = _find_project_root()
DB_PATH      = Path(os.getenv("SQLITE_PATH", str(PROJECT_ROOT / "data" / "logs.db")))


# =============================================================================
# DATABASE SETUP
# =============================================================================

def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they don't exist."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS query_logs (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp       TEXT    NOT NULL,
                question        TEXT    NOT NULL,
                answer          TEXT    NOT NULL,
                model           TEXT    NOT NULL,
                latency_ms      INTEGER NOT NULL,
                top_k           INTEGER NOT NULL,
                chunk_ids       TEXT    NOT NULL,
                sources         TEXT    NOT NULL,
                recall_at_k     REAL,
                citation_coverage REAL,
                grounding_score REAL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS eval_questions (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                question        TEXT    NOT NULL,
                expected_source TEXT    NOT NULL,
                added_at        TEXT    NOT NULL
            )
        """)
        conn.commit()


# =============================================================================
# LOGGING
# =============================================================================

def log_query(
    question:    str,
    answer:      str,
    citations:   list[dict],
    model:       str,
    latency_ms:  int,
    top_k:       int,
    context:     str = "",
) -> int:
    """
    Log a query and compute evaluation metrics.
    Returns the row ID of the inserted log.
    """
    init_db()

    chunk_ids = json.dumps([c.get("source", "") + "_" + str(c.get("rank", "")) for c in citations])
    sources   = json.dumps([c.get("source", "") for c in citations])

    # Compute metrics
    recall          = compute_recall_at_k(citations, top_k)
    citation_cov    = compute_citation_coverage(answer, citations)
    grounding       = compute_grounding_score(answer, context)

    with get_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO query_logs
              (timestamp, question, answer, model, latency_ms, top_k,
               chunk_ids, sources, recall_at_k, citation_coverage, grounding_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.utcnow().isoformat(),
            question, answer, model, latency_ms, top_k,
            chunk_ids, sources,
            recall, citation_cov, grounding,
        ))
        conn.commit()
        return cursor.lastrowid


# =============================================================================
# EVALUATION METRICS
# =============================================================================

def compute_recall_at_k(citations: list[dict], top_k: int) -> float:
    """
    Recall@k — ratio of retrieved chunks that have High/Medium confidence.
    Proxy for retrieval quality without needing ground truth labels.
    """
    if not citations:
        return 0.0
    relevant = sum(
        1 for c in citations
        if c.get("confidence") in ("High", "Medium") or c.get("score", 0) >= 0.55
    )
    return round(relevant / min(top_k, len(citations)), 4)


def compute_citation_coverage(answer: str, citations: list[dict]) -> float:
    """
    Citation coverage — fraction of citations that are actually
    referenced in the answer text (e.g. [Source 1]).
    """
    if not citations:
        return 0.0
    referenced = sum(
        1 for c in citations
        if f"[Source {c.get('rank')}]" in answer or c.get("title", "").lower() in answer.lower()
    )
    return round(referenced / len(citations), 4)


def compute_grounding_score(answer: str, context: str) -> float:
    """
    Grounding score — word overlap between answer and retrieved context.
    Higher = answer is more grounded in the retrieved documents.
    """
    if not context or not answer:
        return 0.0

    answer_words  = set(answer.lower().split())
    context_words = set(context.lower().split())

    if not answer_words:
        return 0.0

    overlap = answer_words & context_words
    return round(len(overlap) / len(answer_words), 4)


# =============================================================================
# QUERY HISTORY
# =============================================================================

def get_recent_logs(limit: int = 20) -> list[dict]:
    """Return the most recent query logs."""
    init_db()
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT * FROM query_logs
            ORDER BY id DESC
            LIMIT ?
        """, (limit,)).fetchall()
    return [dict(row) for row in rows]


def get_stats() -> dict:
    """Return aggregate stats across all logged queries."""
    init_db()
    with get_connection() as conn:
        row = conn.execute("""
            SELECT
                COUNT(*)           as total_queries,
                AVG(latency_ms)    as avg_latency_ms,
                MIN(latency_ms)    as min_latency_ms,
                MAX(latency_ms)    as max_latency_ms,
                AVG(recall_at_k)   as avg_recall,
                AVG(citation_coverage) as avg_citation_coverage,
                AVG(grounding_score)   as avg_grounding
            FROM query_logs
        """).fetchone()
    return dict(row)


# =============================================================================
# EVAL QUESTION SET
# =============================================================================

def add_eval_question(question: str, expected_source: str):
    """Add a question to the evaluation set."""
    init_db()
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO eval_questions (question, expected_source, added_at)
            VALUES (?, ?, ?)
        """, (question, expected_source, datetime.utcnow().isoformat()))
        conn.commit()


def get_eval_questions() -> list[dict]:
    init_db()
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM eval_questions").fetchall()
    return [dict(row) for row in rows]


# =============================================================================
# VISUALIZATION
# =============================================================================

def visualize(output_path: Optional[str] = None):
    """
    Generate evaluation charts and save to file or display inline.
    Charts:
      1. Latency over time
      2. Recall@k over time
      3. Grounding score distribution
      4. Citation coverage distribution
    """
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
    except ImportError:
        print("⚠️  matplotlib not installed. Run: pip install matplotlib")
        return

    logs = get_recent_logs(limit=100)
    if not logs:
        print("⚠️  No query logs found. Ask some questions first!")
        return

    # Parse data
    timestamps     = [datetime.fromisoformat(l["timestamp"]) for l in logs]
    latencies      = [l["latency_ms"] for l in logs]
    recalls        = [l["recall_at_k"] or 0 for l in logs]
    groundings     = [l["grounding_score"] or 0 for l in logs]
    citation_covs  = [l["citation_coverage"] or 0 for l in logs]

    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    fig.suptitle("AI Knowledge Assistant — Evaluation Dashboard", fontsize=14, fontweight="bold")
    fig.patch.set_facecolor("#0a0a0f")

    for ax in axes.flat:
        ax.set_facecolor("#111118")
        ax.tick_params(colors="#6b6b8a")
        ax.xaxis.label.set_color("#6b6b8a")
        ax.yaxis.label.set_color("#6b6b8a")
        ax.title.set_color("#e2e2f0")
        for spine in ax.spines.values():
            spine.set_edgecolor("#1e1e2e")

    # 1. Latency over time
    axes[0, 0].plot(timestamps, latencies, color="#7c6af7", linewidth=1.5, marker="o", markersize=3)
    axes[0, 0].set_title("Response Latency (ms)")
    axes[0, 0].set_ylabel("ms")
    axes[0, 0].xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    axes[0, 0].axhline(y=sum(latencies)/len(latencies), color="#56cfb2", linestyle="--",
                       linewidth=1, label=f"avg: {sum(latencies)/len(latencies):.0f}ms")
    axes[0, 0].legend(fontsize=8, labelcolor="#56cfb2")

    # 2. Recall@k over time
    axes[0, 1].plot(timestamps, recalls, color="#56cfb2", linewidth=1.5, marker="o", markersize=3)
    axes[0, 1].set_title("Recall@K Over Time")
    axes[0, 1].set_ylabel("Recall@K")
    axes[0, 1].set_ylim(0, 1.1)
    axes[0, 1].xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))

    # 3. Grounding score distribution
    axes[1, 0].hist(groundings, bins=10, color="#7c6af7", edgecolor="#1e1e2e", alpha=0.8)
    axes[1, 0].set_title("Grounding Score Distribution")
    axes[1, 0].set_xlabel("Score (word overlap with context)")
    axes[1, 0].set_ylabel("Count")
    axes[1, 0].axvline(x=sum(groundings)/len(groundings), color="#56cfb2",
                       linestyle="--", linewidth=1,
                       label=f"avg: {sum(groundings)/len(groundings):.2f}")
    axes[1, 0].legend(fontsize=8, labelcolor="#56cfb2")

    # 4. Citation coverage distribution
    axes[1, 1].hist(citation_covs, bins=10, color="#56cfb2", edgecolor="#1e1e2e", alpha=0.8)
    axes[1, 1].set_title("Citation Coverage Distribution")
    axes[1, 1].set_xlabel("Coverage (fraction cited in answer)")
    axes[1, 1].set_ylabel("Count")
    axes[1, 1].axvline(x=sum(citation_covs)/len(citation_covs), color="#7c6af7",
                       linestyle="--", linewidth=1,
                       label=f"avg: {sum(citation_covs)/len(citation_covs):.2f}")
    axes[1, 1].legend(fontsize=8, labelcolor="#7c6af7")

    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches="tight",
                    facecolor=fig.get_facecolor())
        print(f"✅  Chart saved to {output_path}")
    else:
        out = PROJECT_ROOT / "data" / "eval_dashboard.png"
        plt.savefig(str(out), dpi=150, bbox_inches="tight",
                    facecolor=fig.get_facecolor())
        print(f"✅  Chart saved to {out}")

    plt.close()


# =============================================================================
# CLI — run evaluation report
# =============================================================================

if __name__ == "__main__":
    init_db()
    stats = get_stats()

    print("\n📊  Evaluation Report")
    print("=" * 50)
    print(f"  Total queries      : {stats['total_queries']}")
    print(f"  Avg latency        : {stats['avg_latency_ms']:.0f}ms" if stats['avg_latency_ms'] else "  Avg latency        : N/A")
    print(f"  Min / Max latency  : {stats['min_latency_ms']}ms / {stats['max_latency_ms']}ms" if stats['min_latency_ms'] else "  Min / Max latency  : N/A")
    print(f"  Avg Recall@K       : {stats['avg_recall']:.3f}" if stats['avg_recall'] else "  Avg Recall@K       : N/A")
    print(f"  Avg Citation Cov.  : {stats['avg_citation_coverage']:.3f}" if stats['avg_citation_coverage'] else "  Avg Citation Cov.  : N/A")
    print(f"  Avg Grounding      : {stats['avg_grounding']:.3f}" if stats['avg_grounding'] else "  Avg Grounding      : N/A")
    print("=" * 50)

    if stats['total_queries']:
        print("\n📈  Generating visualization ...")
        visualize()

    print("\n🕒  Recent queries:")
    for log in get_recent_logs(limit=5):
        print(f"  [{log['timestamp'][:19]}] {log['question'][:60]}...")
        print(f"    Latency: {log['latency_ms']}ms | Recall: {log['recall_at_k']} | Grounding: {log['grounding_score']}")
