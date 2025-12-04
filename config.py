"""
Configuration for Legal RAG System
"""
import os
from dotenv import load_dotenv

# Load environment variables (override system env vars)
load_dotenv(override=True)

# Pinecone Settings
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT", "us-east-1")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "legal-cases")

# Embedding Settings
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "openai")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
LOCAL_EMBEDDING_MODEL = os.getenv("LOCAL_EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# Dimension depends on provider
if EMBEDDING_PROVIDER == "local":
    EMBEDDING_DIMENSION = 384  # all-MiniLM-L6-v2 dimension
else:
    EMBEDDING_DIMENSION = 1536  # OpenAI dimension

# Anthropic Settings (for LLM generation)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# LLM Provider
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "claude")  # "claude" or "openai"
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5-20250929")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")

# Local Paths
CHUNKED_DATA_PATH = "./chunked_output"
PARENTS_FILE = f"{CHUNKED_DATA_PATH}/parents.json"
CHILDREN_FILE = f"{CHUNKED_DATA_PATH}/children.json"

# RAG Settings
TOP_K_CHILDREN = 5  # Number of child chunks to retrieve
TEMPERATURE = 0.1   # LLM temperature for generation

# AWS S3 Settings
BUCKET_NAME = os.getenv("BUCKET_NAME", "legal-opinions-dataset")
TARGET_FOLDER = os.getenv("TARGET_FOLDER", "court-opinions")
