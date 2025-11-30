# Quick Setup Guide - Legal RAG with Claude Sonnet 4.5

## What You Need

### 3 API Keys:

1. **Pinecone** (free) - Vector database
   - Sign up: https://www.pinecone.io/
   - Get API key from dashboard
   - Note your region (us-east-1 or eu-west-1)

2. **OpenAI** - For embeddings only
   - Sign up: https://platform.openai.com/
   - Create API key
   - Add payment method (you'll spend ~$2 for initial embeddings)

3. **Anthropic** - For Claude Sonnet 4.5
   - Sign up: https://console.anthropic.com/
   - Create API key
   - Add payment method

## Setup Steps

### 1. Configure .env file

```bash
# Copy the example
copy .env.example .env
```

Then edit `.env` with your real API keys:

```env
PINECONE_API_KEY=your_pinecone_key_here
PINECONE_ENVIRONMENT=us-east-1
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
LLM_PROVIDER=claude
```

### 2. Run the pipeline

```bash
# Activate your venv
venv\Scripts\activate

# Index your chunked data to Pinecone
python embed_and_index.py

# Query the system
python query_rag.py
```

## What Each API Does

| Service | Used For | Cost |
|---------|----------|------|
| **Pinecone** | Store vector embeddings | $0 (free tier) |
| **OpenAI** | Generate embeddings from text | $0.10 per 1M tokens (~$2 one-time) |
| **Anthropic** | Generate answers with Claude | $3 per 1M input tokens, $15 per 1M output tokens |

## Example Query Flow

1. **You ask**: "What is required to prove criminal intent?"
2. **OpenAI**: Converts your question to a vector embedding ($0.0001)
3. **Pinecone**: Finds 5 most relevant legal case chunks (free)
4. **System**: Retrieves full parent opinions for context
5. **Claude 4.5**: Generates answer from legal opinions (~$0.018)
6. **You get**: Detailed answer with case citations

## Switching to OpenAI GPT-4

If you prefer to use GPT-4 instead of Claude, just change in `.env`:

```env
LLM_PROVIDER=openai
```

## Troubleshooting

**"PINECONE_API_KEY not found"**
- Make sure you created `.env` (not `.env.example`)
- Check the file has no typos

**"Rate limit exceeded"**
- Add payment method to OpenAI/Anthropic
- Wait a few minutes and try again

**"Index not found"**
- Run `embed_and_index.py` first

## Cost Example (1000 queries/month)

| Item | Cost |
|------|------|
| Pinecone | $0 |
| OpenAI embeddings | $0.10 |
| Claude responses | ~$18 |
| **Total** | **~$18/month** |

Much cheaper than Claude API alone since we only use it for generation, not retrieval!
