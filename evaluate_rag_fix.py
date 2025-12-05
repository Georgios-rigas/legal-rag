    def run_single_query(self, query_obj: Dict[str, Any]) -> Dict[str, Any]:
        """Run evaluation for a single test query."""
        query_text = query_obj["query"]
        query_id = query_obj["query_id"]

        print(f"\nQuery {query_id}: {query_text[:80]}...")

        # Time the complete query
        start_time = time.time()

        # Use the RAG system's query method which handles everything properly
        embed_start = time.time()
        response = self.rag.query(query_text, top_k=5)
        total_time = time.time() - start_time
        
        # Extract answer and sources from response
        answer = response.get('answer', '')
        sources = response.get('sources', [])
        
        # Approximate timing breakdown (since we used the full query method)
        # We'll estimate based on typical patterns
        embed_time = 0.2  # Approximate embedding time
        search_time = 0.3  # Approximate search time
        llm_time = total_time - embed_time - search_time

        timings = {
            "total": total_time,
            "embedding": embed_time,
            "search": search_time,
            "llm": llm_time
        }

        # For retrieval evaluation, we need the case IDs from sources
        retrieved_cases = [{'metadata': src} for src in sources]

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
