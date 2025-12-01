"""
Delete old index and re-index with OpenAI embeddings
"""
from pinecone import Pinecone
import config
import os

# Override to use OpenAI
os.environ['EMBEDDING_PROVIDER'] = 'openai'

# Reload config with new provider
import importlib
importlib.reload(config)

print("=" * 60)
print("Re-indexing with OpenAI Embeddings")
print("=" * 60)

# Connect to Pinecone
pc = Pinecone(api_key=config.PINECONE_API_KEY)

# Check if index exists
existing_indexes = pc.list_indexes()
index_names = [idx['name'] for idx in existing_indexes]

if config.PINECONE_INDEX_NAME in index_names:
    print(f"\nDeleting existing index '{config.PINECONE_INDEX_NAME}'...")
    pc.delete_index(config.PINECONE_INDEX_NAME)
    print(f"Index deleted successfully")
else:
    print(f"\nNo existing index to delete")

print(f"\nNow run: python embed_and_index.py")
print(f"This will create a new index with {config.EMBEDDING_DIMENSION} dimensions for OpenAI")
