"""Check current Pinecone index stats"""
from pinecone import Pinecone
import config

pc = Pinecone(api_key=config.PINECONE_API_KEY)
index = pc.Index(config.PINECONE_INDEX_NAME)
stats = index.describe_index_stats()

print(f"Index name: {config.PINECONE_INDEX_NAME}")
print(f"Current dimension: {stats['dimension']}")
print(f"Total vectors: {stats['total_vector_count']}")
print(f"\nConfigured embedding provider: {config.EMBEDDING_PROVIDER}")
print(f"Required dimension for {config.EMBEDDING_PROVIDER}: {config.EMBEDDING_DIMENSION}")

if stats['dimension'] != config.EMBEDDING_DIMENSION:
    print(f"\n⚠️  WARNING: Dimension mismatch!")
    print(f"   Index has {stats['dimension']} dimensions")
    print(f"   Provider needs {config.EMBEDDING_DIMENSION} dimensions")
    print(f"\n   You need to delete and recreate the index or create a new one.")
