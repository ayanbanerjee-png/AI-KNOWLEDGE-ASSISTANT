"""
tools/evaluate.py — Run evaluation against the question set

Asks all eval questions, checks if the correct source was retrieved,
and prints a summary report.

Usage:
    python tools/evaluate.py
"""

import sys
import os
from pathlib import Path

# Add project root to path
root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))

from core.logger import get_eval_questions, get_stats, init_db
from core.retriever import retrieve


def run_evaluation():
    init_db()
    questions = get_eval_questions()

    if not questions:
        print("⚠️  No eval questions found. Run add_eval_question() first.")
        return

    print("\n📋  Running Evaluation")
    print("=" * 60)

    correct   = 0
    total     = len(questions)

    for q in questions:
        question        = q["question"]
        expected_source = q["expected_source"]

        # Retrieve top chunks
        results = retrieve(question, top_k=5)
        sources = [r["source"] for r in results]

        # Check if expected source is in top results
        hit = any(expected_source.lower() in s.lower() for s in sources)
        if hit:
            correct += 1

        status = "✅" if hit else "❌"
        print(f"\n{status}  Q: {question[:55]}...")
        print(f"    Expected : {expected_source}")
        print(f"    Retrieved: {sources[0] if sources else 'none'}")
        if not hit:
            print(f"    All sources: {sources}")

    accuracy = correct / total * 100
    print("\n" + "=" * 60)
    print(f"📊  Results: {correct}/{total} correct ({accuracy:.0f}% accuracy)")

    # Overall stats
    stats = get_stats()
    if stats["total_queries"]:
        print(f"\n📈  Overall Stats (all {stats['total_queries']} queries):")
        print(f"    Avg Latency    : {stats['avg_latency_ms']:.0f}ms")
        print(f"    Avg Recall@K   : {stats['avg_recall']:.3f}")
        print(f"    Avg Grounding  : {stats['avg_grounding']:.3f}")
        print(f"    Avg Citation   : {stats['avg_citation_coverage']:.3f}")
    print("=" * 60)


if __name__ == "__main__":
    run_evaluation()