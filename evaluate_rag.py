"""
RAG System Evaluation Script

This script evaluates the Legal RAG system using the curated evaluation dataset.
It measures retrieval quality, answer accuracy, performance, and cost metrics.

Usage:
    python evaluate_rag.py --dataset evaluation_dataset.json --output results.json
"""

import json
import time
import os
from typing import List, Dict, Any
from collections import defaultdict
import statistics

from query_rag import LegalRAG
import config

# Optional: Weights & Biases integration
WANDB_ENABLED = os.getenv("WANDB_ENABLED", "false").lower() == "true"
if WANDB_ENABLED:
    try:
        import wandb
        print("✅ Weights & Biases integration enabled")
    except ImportError:
        print("⚠️  wandb not installed. Install with: pip install wandb")
        WANDB_ENABLED = False


class RAGEvaluator:
    """Evaluates RAG system performance on curated test queries."""

    def __init__(self, dataset_path: str = "evaluation_dataset.json"):
        """Load evaluation dataset and initialize RAG system."""
        print("Loading evaluation dataset...")
        with open(dataset_path, 'r') as f:
            self.dataset = json.load(f)

        print(f"Loaded {len(self.dataset['test_queries'])} test queries")

        print("\nInitializing Legal RAG system...")
        self.rag = LegalRAG()

        self.results = {
            "retrieval_metrics": {},
            "answer_quality_metrics": {},
            "performance_metrics": {},
            "cost_metrics": {},
            "per_query_results": []
        }

        # Initialize Weights & Biases if enabled
        self.wandb_run = None
        if WANDB_ENABLED:
            project_name = os.getenv("WANDB_PROJECT", "legal-rag-monitoring")
            self.wandb_run = wandb.init(
                project=project_name,
                name=f"eval_{time.strftime('%Y%m%d_%H%M%S')}",
                config={
                    "embedding_provider": config.EMBEDDING_PROVIDER,
                    "llm_provider": config.LLM_PROVIDER,
                    "dataset_size": len(self.dataset['test_queries'])
                }
            )
            print(f"📊 W&B Run: {self.wandb_run.url}")

    def evaluate_retrieval(self, query: Dict[str, Any], retrieved_cases: List[Dict]) -> Dict[str, float]:
        """
        Evaluate retrieval quality for a single query.

        Metrics:
        - Precision@5: How many of top 5 are relevant?
        - Recall@5: How many relevant cases did we find?
        - MRR: Position of first relevant result
        """
        relevant_case_ids = set(query.get("relevant_case_ids", []))

        if not relevant_case_ids:
            # No ground truth for this query
            return {
                "precision@5": None,
                "recall@5": None,
                "mrr": None,
                "has_ground_truth": False
            }

        # Extract case IDs from retrieved results
        retrieved_ids = [
            int(case.get("metadata", {}).get("case_id", -1))
            for case in retrieved_cases[:5]
        ]

        # Calculate metrics
        relevant_retrieved = [cid for cid in retrieved_ids if cid in relevant_case_ids]

        precision_at_5 = len(relevant_retrieved) / 5 if len(retrieved_cases) >= 5 else 0
        recall_at_5 = len(relevant_retrieved) / len(relevant_case_ids) if relevant_case_ids else 0

        # MRR - position of first relevant result
        mrr = 0
        for i, cid in enumerate(retrieved_ids, 1):
            if cid in relevant_case_ids:
                mrr = 1 / i
                break

        return {
            "precision@5": precision_at_5,
            "recall@5": recall_at_5,
            "mrr": mrr,
            "has_ground_truth": True,
            "retrieved_case_ids": retrieved_ids,
            "relevant_retrieved": relevant_retrieved
        }

    def evaluate_answer_quality(
        self,
        query: Dict[str, Any],
        answer: str,
        sources: List[Dict]
    ) -> Dict[str, Any]:
        """
        Evaluate answer quality (requires manual review or LLM-as-judge).

        For now, we check:
        - Citation accuracy: Are cited cases in retrieved sources?
        - Expected points coverage (manual review needed)
        """
        # Extract case names/IDs mentioned in answer
        cited_cases = self._extract_citations(answer)

        # Check if citations are from retrieved sources
        retrieved_case_ids = {src.get("metadata", {}).get("case_id") for src in sources}
        retrieved_case_names = {src.get("metadata", {}).get("case_name") for src in sources}

        # Verify citations
        verified_citations = 0
        total_citations = len(cited_cases)

        for cite in cited_cases:
            if cite in retrieved_case_names or cite in retrieved_case_ids:
                verified_citations += 1

        citation_accuracy = verified_citations / total_citations if total_citations > 0 else 1.0

        # Check for expected answer points (requires manual review)
        expected_points = query.get("expected_answer_points", [])

        return {
            "citation_accuracy": citation_accuracy,
            "total_citations": total_citations,
            "verified_citations": verified_citations,
            "expected_points": expected_points,
            "expected_points_count": len(expected_points),
            "answer_length": len(answer),
            "has_expected_points": len(expected_points) > 0
        }

    def evaluate_performance(self, timings: Dict[str, float]) -> Dict[str, float]:
        """Evaluate performance metrics."""
        return {
            "total_latency": timings.get("total", 0),
            "embedding_time": timings.get("embedding", 0),
            "search_time": timings.get("search", 0),
            "llm_time": timings.get("llm", 0)
        }

    def evaluate_cost(self, query: str, answer: str) -> Dict[str, float]:
        """
        Estimate API costs for query.

        OpenAI embeddings: ~$0.00002 per 1K tokens
        Anthropic Claude: ~$3 per 1M input tokens, ~$15 per 1M output tokens
        """
        # Estimate tokens (rough: 1 token ≈ 4 chars)
        query_tokens = len(query) / 4
        answer_tokens = len(answer) / 4

        # Estimate context tokens (5 retrieved chunks × ~200 tokens each)
        context_tokens = 1000

        # Costs
        embedding_cost = (query_tokens / 1000) * 0.00002
        llm_input_cost = ((query_tokens + context_tokens) / 1_000_000) * 3
        llm_output_cost = (answer_tokens / 1_000_000) * 15

        total_cost = embedding_cost + llm_input_cost + llm_output_cost

        return {
            "embedding_cost": embedding_cost,
            "llm_input_cost": llm_input_cost,
            "llm_output_cost": llm_output_cost,
            "total_cost": total_cost
        }

    def _extract_citations(self, text: str) -> List[str]:
        """Extract case citations from answer text."""
        # Simple extraction - looks for "v." pattern common in case names
        # In production, use more sophisticated NER or regex
        citations = []
        words = text.split()
        for i, word in enumerate(words):
            if word.lower() == "v." and i > 0 and i < len(words) - 1:
                # Found "v." - extract surrounding words
                citation = f"{words[i-1]} v. {words[i+1]}"
                citations.append(citation)
        return citations

    def run_single_query(self, query_obj: Dict[str, Any]) -> Dict[str, Any]:
        """Run evaluation for a single test query."""
        query_text = query_obj["query"]
        query_id = query_obj["query_id"]

        print(f"\nQuery {query_id}: {query_text[:80]}...")

        # Time the complete query
        start_time = time.time()

        # Step 1: Embed query
        embed_start = time.time()
        query_embedding = self.rag.embed_query(query_text)
        embed_time = time.time() - embed_start

        # Step 2: Search Pinecone
        search_start = time.time()
        search_results = self.rag.index.query(
            vector=query_embedding,
            top_k=5,
            include_metadata=True
        )
        retrieved_cases = search_results.get("matches", [])
        search_time = time.time() - search_start

        # Step 3: Generate answer
        llm_start = time.time()
        answer, sources = self.rag.generate_answer(query_text, retrieved_cases)
        llm_time = time.time() - llm_start

        total_time = time.time() - start_time

        timings = {
            "total": total_time,
            "embedding": embed_time,
            "search": search_time,
            "llm": llm_time
        }

        # Evaluate retrieval
        retrieval_metrics = self.evaluate_retrieval(query_obj, retrieved_cases)

        # Evaluate answer quality
        answer_metrics = self.evaluate_answer_quality(query_obj, answer, sources)

        # Evaluate performance
        performance_metrics = self.evaluate_performance(timings)

        # Estimate cost
        cost_metrics = self.evaluate_cost(query_text, answer)

        result = {
            "query_id": query_id,
            "query": query_text,
            "category": query_obj.get("category"),
            "difficulty": query_obj.get("difficulty"),
            "retrieval_metrics": retrieval_metrics,
            "answer_metrics": answer_metrics,
            "performance_metrics": performance_metrics,
            "cost_metrics": cost_metrics,
            "answer": answer[:500] + "..." if len(answer) > 500 else answer,  # Truncate for storage
            "retrieved_case_ids": retrieval_metrics.get("retrieved_case_ids", [])
        }

        # Print summary
        if retrieval_metrics["has_ground_truth"]:
            print(f"  Precision@5: {retrieval_metrics['precision@5']:.2f}")
            print(f"  Recall@5: {retrieval_metrics['recall@5']:.2f}")
            print(f"  MRR: {retrieval_metrics['mrr']:.3f}")
        print(f"  Latency: {total_time:.2f}s")
        print(f"  Cost: ${cost_metrics['total_cost']:.4f}")

        return result

    def run_evaluation(self, max_queries: int = None) -> Dict[str, Any]:
        """
        Run evaluation on all test queries.

        Args:
            max_queries: Maximum number of queries to evaluate (None = all)
        """
        queries = self.dataset["test_queries"]
        if max_queries:
            queries = queries[:max_queries]

        print(f"\n{'='*80}")
        print(f"Running evaluation on {len(queries)} queries...")
        print(f"{'='*80}")

        per_query_results = []

        for query_obj in queries:
            try:
                result = self.run_single_query(query_obj)
                per_query_results.append(result)
            except Exception as e:
                print(f"  ERROR: {str(e)}")
                per_query_results.append({
                    "query_id": query_obj["query_id"],
                    "error": str(e)
                })

        # Aggregate metrics
        self._aggregate_metrics(per_query_results)

        self.results["per_query_results"] = per_query_results

        return self.results

    def _aggregate_metrics(self, results: List[Dict[str, Any]]):
        """Aggregate metrics across all queries."""
        # Filter out errors
        valid_results = [r for r in results if "error" not in r]

        if not valid_results:
            print("\nNo valid results to aggregate!")
            return

        # Aggregate retrieval metrics
        retrieval_results = [
            r["retrieval_metrics"]
            for r in valid_results
            if r["retrieval_metrics"]["has_ground_truth"]
        ]

        if retrieval_results:
            self.results["retrieval_metrics"] = {
                "avg_precision@5": statistics.mean([r["precision@5"] for r in retrieval_results]),
                "avg_recall@5": statistics.mean([r["recall@5"] for r in retrieval_results]),
                "avg_mrr": statistics.mean([r["mrr"] for r in retrieval_results]),
                "queries_with_ground_truth": len(retrieval_results)
            }

        # Aggregate answer quality metrics
        citation_accuracies = [
            r["answer_metrics"]["citation_accuracy"]
            for r in valid_results
            if r["answer_metrics"]["total_citations"] > 0
        ]

        if citation_accuracies:
            self.results["answer_quality_metrics"] = {
                "avg_citation_accuracy": statistics.mean(citation_accuracies),
                "queries_with_citations": len(citation_accuracies)
            }

        # Aggregate performance metrics
        self.results["performance_metrics"] = {
            "avg_total_latency": statistics.mean([r["performance_metrics"]["total_latency"] for r in valid_results]),
            "avg_embedding_time": statistics.mean([r["performance_metrics"]["embedding_time"] for r in valid_results]),
            "avg_search_time": statistics.mean([r["performance_metrics"]["search_time"] for r in valid_results]),
            "avg_llm_time": statistics.mean([r["performance_metrics"]["llm_time"] for r in valid_results]),
            "p95_total_latency": statistics.quantiles([r["performance_metrics"]["total_latency"] for r in valid_results], n=20)[18],  # 95th percentile
        }

        # Aggregate cost metrics
        self.results["cost_metrics"] = {
            "avg_cost_per_query": statistics.mean([r["cost_metrics"]["total_cost"] for r in valid_results]),
            "total_cost": sum([r["cost_metrics"]["total_cost"] for r in valid_results]),
            "avg_embedding_cost": statistics.mean([r["cost_metrics"]["embedding_cost"] for r in valid_results]),
            "avg_llm_cost": statistics.mean([r["cost_metrics"]["llm_input_cost"] + r["cost_metrics"]["llm_output_cost"] for r in valid_results])
        }

    def print_summary(self):
        """Print evaluation summary."""
        print(f"\n{'='*80}")
        print("EVALUATION SUMMARY")
        print(f"{'='*80}")

        if self.results["retrieval_metrics"]:
            print("\nRetrieval Metrics:")
            print(f"  Average Precision@5: {self.results['retrieval_metrics']['avg_precision@5']:.3f}")
            print(f"  Average Recall@5: {self.results['retrieval_metrics']['avg_recall@5']:.3f}")
            print(f"  Average MRR: {self.results['retrieval_metrics']['avg_mrr']:.3f}")
            print(f"  Queries with ground truth: {self.results['retrieval_metrics']['queries_with_ground_truth']}")

        if self.results["answer_quality_metrics"]:
            print("\nAnswer Quality Metrics:")
            print(f"  Average Citation Accuracy: {self.results['answer_quality_metrics']['avg_citation_accuracy']:.3f}")
            print(f"  Queries with citations: {self.results['answer_quality_metrics']['queries_with_citations']}")

        if self.results["performance_metrics"]:
            print("\nPerformance Metrics:")
            print(f"  Average Total Latency: {self.results['performance_metrics']['avg_total_latency']:.2f}s")
            print(f"  Average Embedding Time: {self.results['performance_metrics']['avg_embedding_time']*1000:.0f}ms")
            print(f"  Average Search Time: {self.results['performance_metrics']['avg_search_time']*1000:.0f}ms")
            print(f"  Average LLM Time: {self.results['performance_metrics']['avg_llm_time']:.2f}s")
            print(f"  95th Percentile Latency: {self.results['performance_metrics']['p95_total_latency']:.2f}s")

        if self.results["cost_metrics"]:
            print("\nCost Metrics:")
            print(f"  Average Cost per Query: ${self.results['cost_metrics']['avg_cost_per_query']:.4f}")
            print(f"  Total Cost (all queries): ${self.results['cost_metrics']['total_cost']:.2f}")
            print(f"  Average Embedding Cost: ${self.results['cost_metrics']['avg_embedding_cost']:.6f}")
            print(f"  Average LLM Cost: ${self.results['cost_metrics']['avg_llm_cost']:.4f}")

        print(f"\n{'='*80}")

        # Log to Weights & Biases
        if self.wandb_run:
            self._log_to_wandb()

    def _log_to_wandb(self):
        """Log metrics to Weights & Biases."""
        if not self.wandb_run:
            return

        # Log summary metrics
        metrics_to_log = {}

        if self.results["retrieval_metrics"]:
            metrics_to_log.update({
                "precision@5": self.results["retrieval_metrics"]["avg_precision@5"],
                "recall@5": self.results["retrieval_metrics"]["avg_recall@5"],
                "mrr": self.results["retrieval_metrics"]["avg_mrr"]
            })

        if self.results["answer_quality_metrics"]:
            metrics_to_log["citation_accuracy"] = self.results["answer_quality_metrics"]["avg_citation_accuracy"]

        if self.results["performance_metrics"]:
            metrics_to_log.update({
                "avg_latency": self.results["performance_metrics"]["avg_total_latency"],
                "p95_latency": self.results["performance_metrics"]["p95_total_latency"],
                "embedding_time": self.results["performance_metrics"]["avg_embedding_time"],
                "search_time": self.results["performance_metrics"]["avg_search_time"],
                "llm_time": self.results["performance_metrics"]["avg_llm_time"]
            })

        if self.results["cost_metrics"]:
            metrics_to_log.update({
                "cost_per_query": self.results["cost_metrics"]["avg_cost_per_query"],
                "total_cost": self.results["cost_metrics"]["total_cost"]
            })

        wandb.log(metrics_to_log)
        print(f"\n✅ Metrics logged to Weights & Biases: {self.wandb_run.url}")

        # Finish the run
        wandb.finish()

    def save_results(self, output_path: str = "evaluation_results.json"):
        """Save evaluation results to JSON file."""
        with open(output_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\nResults saved to {output_path}")


def main():
    """Run evaluation."""
    import argparse

    parser = argparse.ArgumentParser(description="Evaluate Legal RAG system")
    parser.add_argument("--dataset", default="evaluation_dataset.json", help="Path to evaluation dataset")
    parser.add_argument("--output", default="evaluation_results.json", help="Path to save results")
    parser.add_argument("--max-queries", type=int, default=None, help="Maximum number of queries to evaluate")

    args = parser.parse_args()

    evaluator = RAGEvaluator(args.dataset)
    evaluator.run_evaluation(max_queries=args.max_queries)
    evaluator.print_summary()
    evaluator.save_results(args.output)


if __name__ == "__main__":
    main()
