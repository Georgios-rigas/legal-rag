"""
Quality Gates Checker for CI/CD Pipeline

This script checks if evaluation results meet minimum quality thresholds.
If thresholds are not met, the script exits with code 1, failing the pipeline.

Usage:
    python check_quality_gates.py evaluation_results.json
"""

import json
import sys


# Define quality thresholds (minimum requirements for deployment)
THRESHOLDS = {
    'precision@5': 0.70,       # 70% precision minimum
    'citation_accuracy': 0.90,  # 90% citation accuracy minimum
    'avg_latency': 10.0,        # 10 seconds maximum average latency
    'p95_latency': 15.0,        # 15 seconds maximum p95 latency
    'cost_per_query': 0.05      # $0.05 maximum cost per query
}


def check_quality_gates(results_file):
    """
    Check if evaluation results meet quality thresholds.

    Args:
        results_file: Path to evaluation results JSON file

    Returns:
        bool: True if all gates pass, False otherwise
    """
    try:
        with open(results_file) as f:
            results = json.load(f)
    except FileNotFoundError:
        print(f"❌ ERROR: Results file not found: {results_file}")
        return False
    except json.JSONDecodeError:
        print(f"❌ ERROR: Invalid JSON in results file: {results_file}")
        return False

    failures = []

    # Check retrieval quality
    if results.get('retrieval_metrics'):
        precision = results['retrieval_metrics'].get('avg_precision@5', 0)
        if precision < THRESHOLDS['precision@5']:
            failures.append(
                f"Precision@5 ({precision:.3f}) below threshold "
                f"({THRESHOLDS['precision@5']})"
            )

        recall = results['retrieval_metrics'].get('avg_recall@5', 0)
        print(f"  ℹ️  Recall@5: {recall:.3f} (no threshold, informational)")

        mrr = results['retrieval_metrics'].get('avg_mrr', 0)
        print(f"  ℹ️  MRR: {mrr:.3f} (no threshold, informational)")

    # Check answer quality
    if results.get('answer_quality_metrics'):
        citation_acc = results['answer_quality_metrics'].get('avg_citation_accuracy', 0)
        if citation_acc < THRESHOLDS['citation_accuracy']:
            failures.append(
                f"Citation accuracy ({citation_acc:.3f}) below threshold "
                f"({THRESHOLDS['citation_accuracy']})"
            )

    # Check performance
    if results.get('performance_metrics'):
        avg_latency = results['performance_metrics'].get('avg_total_latency', 0)
        p95_latency = results['performance_metrics'].get('p95_total_latency', 0)

        if avg_latency > THRESHOLDS['avg_latency']:
            failures.append(
                f"Average latency ({avg_latency:.2f}s) above threshold "
                f"({THRESHOLDS['avg_latency']}s)"
            )

        if p95_latency and p95_latency > THRESHOLDS['p95_latency']:
            failures.append(
                f"P95 latency ({p95_latency:.2f}s) above threshold "
                f"({THRESHOLDS['p95_latency']}s)"
            )

    # Check cost
    if results.get('cost_metrics'):
        cost = results['cost_metrics'].get('avg_cost_per_query', 0)
        if cost > THRESHOLDS['cost_per_query']:
            failures.append(
                f"Cost per query (${cost:.4f}) above threshold "
                f"(${THRESHOLDS['cost_per_query']})"
            )

    # Print results
    print("=" * 80)
    print("QUALITY GATE RESULTS")
    print("=" * 80)
    print()

    if failures:
        print("❌ FAILED - Quality gates not met:")
        print()
        for failure in failures:
            print(f"  ❌ {failure}")
        print()
        print("=" * 80)
        print("Pipeline BLOCKED. Fix issues above before deploying.")
        print("=" * 80)
        return False
    else:
        print("✅ PASSED - All quality gates met!")
        print()

        # Print passing metrics
        if results.get('retrieval_metrics'):
            precision = results['retrieval_metrics'].get('avg_precision@5', 0)
            print(f"  ✓ Precision@5: {precision:.3f} (>= {THRESHOLDS['precision@5']})")

        if results.get('answer_quality_metrics'):
            citation_acc = results['answer_quality_metrics'].get('avg_citation_accuracy', 0)
            print(f"  ✓ Citation Accuracy: {citation_acc:.3f} (>= {THRESHOLDS['citation_accuracy']})")

        if results.get('performance_metrics'):
            avg_latency = results['performance_metrics'].get('avg_total_latency', 0)
            print(f"  ✓ Avg Latency: {avg_latency:.2f}s (<= {THRESHOLDS['avg_latency']}s)")

        if results.get('cost_metrics'):
            cost = results['cost_metrics'].get('avg_cost_per_query', 0)
            print(f"  ✓ Cost/Query: ${cost:.4f} (<= ${THRESHOLDS['cost_per_query']})")

        print()
        print("=" * 80)
        print("Pipeline APPROVED for deployment.")
        print("=" * 80)
        return True


def main():
    """Main entry point."""
    if len(sys.argv) != 2:
        print("Usage: python check_quality_gates.py <results_file>")
        print()
        print("Example:")
        print("  python check_quality_gates.py evaluation_results.json")
        sys.exit(1)

    results_file = sys.argv[1]

    # Check quality gates
    passed = check_quality_gates(results_file)

    # Exit with appropriate code
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
