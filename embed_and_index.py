"""
Embed child chunks and index them in Pinecone
Stores parent_id in metadata for retrieval
"""
import json
from typing import List, Dict
from tqdm import tqdm
from pinecone import Pinecone, ServerlessSpec
import config

# Import embedding provider
if config.EMBEDDING_PROVIDER == "openai":
    from openai import OpenAI
else:
    from sentence_transformers import SentenceTransformer

def load_chunks():
    """Load parent and child chunks from JSON files."""
    print(f"📂 Loading chunks from {config.CHUNKED_DATA_PATH}...")

    with open(config.CHILDREN_FILE, 'r') as f:
        children = json.load(f)

    with open(config.PARENTS_FILE, 'r') as f:
        parents = json.load(f)

    # Create parent lookup
    parent_lookup = {p['id']: p for p in parents}

    print(f"✅ Loaded {len(children)} child chunks and {len(parents)} parent chunks")
    return children, parent_lookup


def generate_embeddings(texts: List[str], batch_size: int = 100) -> List[List[float]]:
    """Generate embeddings using configured provider."""
    print(f"🔮 Generating embeddings for {len(texts)} texts using {config.EMBEDDING_PROVIDER}...")

    if config.EMBEDDING_PROVIDER == "openai":
        client = OpenAI(api_key=config.OPENAI_API_KEY)
        all_embeddings = []

        for i in tqdm(range(0, len(texts), batch_size)):
            batch = texts[i:i + batch_size]
            response = client.embeddings.create(
                model=config.OPENAI_EMBEDDING_MODEL,
                input=batch
            )
            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)

        return all_embeddings
    else:
        # Local embeddings with sentence-transformers
        model = SentenceTransformer(config.LOCAL_EMBEDDING_MODEL)
        print(f"📥 Using local model: {config.LOCAL_EMBEDDING_MODEL}")

        embeddings = []
        for i in tqdm(range(0, len(texts), batch_size)):
            batch = texts[i:i + batch_size]
            batch_embeddings = model.encode(batch, show_progress_bar=False)
            embeddings.extend(batch_embeddings.tolist())

        return embeddings


def init_pinecone_index():
    """Initialize Pinecone index (creates if doesn't exist)."""
    print(f"🔌 Connecting to Pinecone...")

    pc = Pinecone(api_key=config.PINECONE_API_KEY)

    # Check if index exists
    existing_indexes = pc.list_indexes()
    index_names = [idx['name'] for idx in existing_indexes]

    if config.PINECONE_INDEX_NAME not in index_names:
        print(f"📊 Creating index '{config.PINECONE_INDEX_NAME}'...")
        pc.create_index(
            name=config.PINECONE_INDEX_NAME,
            dimension=config.EMBEDDING_DIMENSION,
            metric='cosine',
            spec=ServerlessSpec(
                cloud='aws',
                region=config.PINECONE_ENVIRONMENT
            )
        )
        print(f"✅ Index created successfully")
    else:
        print(f"✅ Index '{config.PINECONE_INDEX_NAME}' already exists")

    return pc.Index(config.PINECONE_INDEX_NAME)


def index_chunks(children: List[Dict], parent_lookup: Dict, index):
    """Generate embeddings and index children with metadata."""
    print(f"\n📥 Indexing {len(children)} child chunks...")

    # Extract texts for embedding
    texts = [child['text'] for child in children]

    # Generate embeddings
    embeddings = generate_embeddings(texts)

    # Prepare vectors for upsert
    vectors = []
    for i, child in enumerate(children):
        parent = parent_lookup.get(child['metadata']['parent_id'])

        # Prepare metadata (Pinecone has size limits, so be selective)
        metadata = {
            'child_id': child['id'],
            'parent_id': child['metadata']['parent_id'],
            'case_id': str(child['metadata']['case_id']),
            'case_name': child['metadata']['case_name'],
            'decision_date': child['metadata']['decision_date'],
            'court': child['metadata']['court'],
            'citation': child['metadata']['citation'],
            'chunk_index': child['metadata']['chunk_index'],
            'text': child['text'][:1000],  # Truncate for metadata storage
        }

        vectors.append({
            'id': child['id'],
            'values': embeddings[i],
            'metadata': metadata
        })

    # Upsert in batches
    batch_size = 100
    print(f"⬆️  Upserting vectors to Pinecone...")

    for i in tqdm(range(0, len(vectors), batch_size)):
        batch = vectors[i:i + batch_size]
        index.upsert(vectors=batch)

    print(f"✅ Successfully indexed {len(vectors)} vectors!")


def main():
    """Main pipeline: load chunks, generate embeddings, index to Pinecone."""
    print("=" * 60)
    print("Legal RAG - Embedding & Indexing Pipeline")
    print("=" * 60)

    # Validate config
    if not config.PINECONE_API_KEY:
        print("❌ Error: PINECONE_API_KEY not found in .env file")
        print("Please copy .env.example to .env and add your API keys")
        return

    if not config.OPENAI_API_KEY:
        print("❌ Error: OPENAI_API_KEY not found in .env file")
        return

    try:
        # Load data
        children, parent_lookup = load_chunks()

        # Initialize Pinecone
        index = init_pinecone_index()

        # Index chunks
        index_chunks(children, parent_lookup, index)

        # Get index stats
        stats = index.describe_index_stats()
        print(f"\n📊 Index Stats:")
        print(f"   Total vectors: {stats['total_vector_count']}")
        print(f"   Dimension: {stats['dimension']}")

        print("\n🎉 Indexing complete! Ready for queries.")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise


if __name__ == "__main__":
    main()
