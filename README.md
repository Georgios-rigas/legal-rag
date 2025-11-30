# Legal RAG System

A production-ready Retrieval-Augmented Generation (RAG) system for legal case law, using hierarchical parent-child chunking.

## Architecture

- **Data Source**: Case.law legal database
- **Chunking**: Parent (2000 chars) + Child (400 chars) strategy
- **Vector DB**: Pinecone (free tier)
- **Embeddings**: OpenAI text-embedding-3-small
- **LLM**: Claude Sonnet 4.5 (or GPT-4 Turbo)

## Project Structure

```
legal_rag/
├── data_extraction.py      # Download legal cases from Case.law → S3
├── hier_chunking.py         # Chunk cases into parent-child structure
├── embed_and_index.py       # Generate embeddings and index to Pinecone
├── query_rag.py             # Query interface for RAG system
├── config.py                # Configuration management
├── .env                     # API keys (create from .env.example)
└── chunked_output/
    ├── parents.json         # Full opinion contexts
    └── children.json        # Searchable chunks
```

## Setup Instructions

### 1. Get API Keys

**Pinecone (Free Tier):**
1. Go to https://www.pinecone.io/
2. Sign up for free account
3. Create API key in dashboard
4. Note your environment (e.g., `us-east-1`)

**OpenAI (for embeddings only):**
1. Go to https://platform.openai.com/
2. Create API key
3. Add billing (pay-as-you-go)

**Anthropic (for Claude LLM):**
1. Go to https://console.anthropic.com/
2. Create API key
3. Add billing (pay-as-you-go)

### 2. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env with your API keys
PINECONE_API_KEY=your_key_here
PINECONE_ENVIRONMENT=us-east-1
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
LLM_PROVIDER=claude  # or "openai"
```

### 3. Install Dependencies

Already installed:
```bash
pip install pinecone-client openai anthropic python-dotenv boto3 beautifulsoup4 langchain-text-splitters
```

## Usage

### Step 1: Download Legal Cases

```bash
python data_extraction.py
```

This downloads legal cases from Case.law and uploads to S3.

### Step 2: Chunk Cases

```bash
# Process all cases from S3
python hier_chunking.py --bucket test-bucket-gr7 --prefix raw_legal_cases/ --limit 100

# Or run demo with sample
python hier_chunking.py
```

Outputs:
- `chunked_output/parents.json` - Full opinions
- `chunked_output/children.json` - Searchable chunks
- `chunked_output/stats.json` - Processing stats

### Step 3: Index to Pinecone

```bash
python embed_and_index.py
```

This will:
1. Load chunked data
2. Generate embeddings for child chunks
3. Create/connect to Pinecone index
4. Upload vectors with metadata

**Cost:** ~$0.002 per 1,000 chunks (OpenAI embedding cost)

### Step 4: Query the System

```bash
python query_rag.py
```

Example queries:
- "What is required to prove criminal intent in indecent exposure cases?"
- "Can a landlord waive a lease covenant by accepting rent?"
- "What are the requirements for a broker to earn commission?"

## How It Works

### Hierarchical Chunking

**Why parent-child?**
- **Children (400 tokens)**: Small, precise chunks for vector search
- **Parents (2000+ tokens)**: Full legal context for LLM generation
- **Benefit**: Find specific legal points, retrieve complete reasoning

**Example:**
```
Parent (2000 chars): Full opinion with complete legal reasoning
├── Child 1: "Criminal intent requires..."
├── Child 2: "The defendant's exposure was..."
└── Child 3: "Prior convictions may be..."
```

### Query Flow

1. **User asks question** → "What proves criminal intent?"
2. **Embed query** → OpenAI embedding
3. **Search children** → Pinecone finds top 5 relevant 400-char chunks
4. **Retrieve parents** → Get full opinions for those chunks
5. **Generate answer** → GPT-4 synthesizes answer from parent contexts
6. **Return with citations** → Answer + source cases

## Cost Estimates

### One-time Setup (10,000 cases)
- Embeddings: ~$2 (OpenAI)
- Total: **~$2**

### Monthly Costs
- Pinecone: **$0** (free tier up to 100K vectors)
- Embeddings: ~$0.0001 per query (OpenAI)
- Claude Sonnet 4.5: ~$0.003 per query (input) + ~$0.015 per response (output)
- 1000 queries/month: **~$18/month** (mostly Claude generation)

### Scaling
- Up to 25,000 cases: Free tier OK
- Beyond 25,000 cases: Upgrade to Pinecone paid ($70/month)

## Troubleshooting

**"PINECONE_API_KEY not found"**
- Make sure you created `.env` file (not `.env.example`)
- Verify API key is correct

**"Index not found"**
- Run `embed_and_index.py` first to create index

**"Rate limit exceeded"**
- OpenAI: Add payment method
- Pinecone: Upgrade plan

## Next Steps

- [ ] Add metadata filtering (date ranges, courts)
- [ ] Implement hybrid search (keyword + vector)
- [ ] Add citation graph visualization
- [ ] Create web UI with Streamlit
- [ ] Deploy to AWS Lambda

## License

MIT
