"""
Query interface for Legal RAG System
Searches child chunks, retrieves parent context, generates answers
"""
import json
from typing import List, Dict
from pinecone import Pinecone
from openai import OpenAI
from anthropic import Anthropic
from sentence_transformers import SentenceTransformer
import config


class LegalRAG:
    def __init__(self):
        """Initialize Pinecone, embedding model, and LLM client."""
        self.pc = Pinecone(api_key=config.PINECONE_API_KEY)
        self.index = self.pc.Index(config.PINECONE_INDEX_NAME)

        # Embedding client (OpenAI or local)
        self.embedding_provider = config.EMBEDDING_PROVIDER
        if self.embedding_provider == "openai":
            self.openai_client = OpenAI(api_key=config.OPENAI_API_KEY)
            print(f"Using OpenAI embeddings ({config.OPENAI_EMBEDDING_MODEL})")
        else:
            self.embedding_model = SentenceTransformer(config.LOCAL_EMBEDDING_MODEL)
            print(f"Using local embeddings ({config.LOCAL_EMBEDDING_MODEL})")

        # LLM client (Claude or OpenAI)
        self.llm_provider = config.LLM_PROVIDER
        if self.llm_provider == "claude":
            self.anthropic_client = Anthropic(api_key=config.ANTHROPIC_API_KEY)
            print(f"Using Claude ({config.CLAUDE_MODEL}) for generation")
        else:
            self.openai_client = OpenAI(api_key=config.OPENAI_API_KEY)
            print(f"Using OpenAI ({config.OPENAI_MODEL}) for generation")

        # Load parent chunks for context retrieval
        with open(config.PARENTS_FILE, 'r') as f:
            parents = json.load(f)
        self.parent_lookup = {p['id']: p for p in parents}

        print(f"Legal RAG initialized with {len(self.parent_lookup)} parent cases")


    def embed_query(self, query: str) -> List[float]:
        """Generate embedding for user query."""
        if self.embedding_provider == "openai":
            response = self.openai_client.embeddings.create(
                model=config.OPENAI_EMBEDDING_MODEL,
                input=[query]
            )
            return response.data[0].embedding
        else:
            # Local embeddings
            embedding = self.embedding_model.encode(query, show_progress_bar=False)
            return embedding.tolist()


    def search(self, query: str, top_k: int = None) -> List[Dict]:
        """
        Search for relevant child chunks.
        Returns parent context for each match.
        """
        top_k = top_k or config.TOP_K_CHILDREN

        # Embed query
        query_embedding = self.embed_query(query)

        # Search Pinecone
        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True
        )

        # Retrieve parent context for each match
        enriched_results = []
        seen_parents = set()

        for match in results['matches']:
            parent_id = match['metadata']['parent_id']

            # Get full parent text
            parent = self.parent_lookup.get(parent_id)
            if not parent:
                continue

            # Avoid duplicate parents
            if parent_id in seen_parents:
                continue
            seen_parents.add(parent_id)

            enriched_results.append({
                'score': match['score'],
                'child_text': match['metadata']['text'],
                'parent_text': parent['text'],
                'case_id': parent['metadata']['case_id'],
                'case_name': match['metadata']['case_name'],
                'decision_date': match['metadata']['decision_date'],
                'court': match['metadata']['court'],
                'citation': match['metadata']['citation'],
                'parent_id': parent_id,
                'child_id': match['id']
            })

        return enriched_results


    def generate_answer(self, query: str, contexts: List[Dict]) -> Dict:
        """
        Generate answer using retrieved parent contexts.
        """
        # Build context string from parents
        context_str = "\n\n---\n\n".join([
            f"Case: {ctx['case_name']} ({ctx['citation']})\n"
            f"Date: {ctx['decision_date']}\n"
            f"Court: {ctx['court']}\n\n"
            f"{ctx['parent_text']}"
            for ctx in contexts
        ])

        # Create prompt
        prompt = f"""You are a legal research assistant. Answer the following question based ONLY on the provided legal cases.

Question: {query}

Legal Cases:
{context_str}

Instructions:
- Provide a clear, accurate answer based on the cases above
- Cite specific cases when making legal points (use case name and citation)
- If the cases don't contain enough information to answer, say so
- Be precise and use legal terminology appropriately

Answer:"""

        # Generate response based on LLM provider
        if self.llm_provider == "claude":
            response = self.anthropic_client.messages.create(
                model=config.CLAUDE_MODEL,
                max_tokens=4096,
                temperature=config.TEMPERATURE,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            answer = response.content[0].text
        else:
            response = self.openai_client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a legal research assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=config.TEMPERATURE
            )
            answer = response.choices[0].message.content

        return {
            'query': query,
            'answer': answer,
            'sources': contexts,
            'num_sources': len(contexts)
        }


    def query(self, question: str, top_k: int = None) -> Dict:
        """
        Main query method: search + generate answer.
        """
        print(f"\nQuery: {question}")
        print(f"Searching for relevant cases...")

        # Search for relevant chunks
        results = self.search(question, top_k)

        if not results:
            return {
                'query': question,
                'answer': "I couldn't find any relevant legal cases to answer this question.",
                'sources': [],
                'num_sources': 0
            }

        print(f"Found {len(results)} relevant cases")
        print(f"Generating answer...")

        # Generate answer
        response = self.generate_answer(question, results)

        return response


def format_response(response: Dict):
    """Pretty print the RAG response."""
    print("\n" + "=" * 80)
    print("ANSWER")
    print("=" * 80)
    print(response['answer'])
    print("\n" + "=" * 80)
    print(f"SOURCES ({response['num_sources']} cases)")
    print("=" * 80)

    for i, source in enumerate(response['sources'], 1):
        print(f"\n{i}. {source['case_name']} ({source['citation']})")
        print(f"   Date: {source['decision_date']}")
        print(f"   Court: {source['court']}")
        print(f"   Relevance: {source['score']:.3f}")


def main():
    """Interactive query interface."""
    print("=" * 80)
    print("Legal RAG - Query Interface")
    print("=" * 80)

    # Initialize RAG system
    rag = LegalRAG()

    # Example queries (you can modify or make it interactive)
    example_queries = [
        "What is required to prove criminal intent in indecent exposure cases?",
        "Can a landlord waive a lease covenant by accepting rent?",
        "What are the requirements for a broker to earn commission on a real estate transaction?"
    ]

    print("\nExample queries:")
    for i, q in enumerate(example_queries, 1):
        print(f"   {i}. {q}")

    # Interactive mode
    print("\n" + "=" * 80)
    print("Enter your question (or 'quit' to exit):")
    print("=" * 80)

    while True:
        try:
            user_query = input("\n>>> ").strip()

            if user_query.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break

            if not user_query:
                continue

            # Query the system
            response = rag.query(user_query)

            # Display results
            format_response(response)

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")


if __name__ == "__main__":
    main()
