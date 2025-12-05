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
import sys
from typing import List, Dict, Any
from collections import defaultdict
import statistics

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

from query_rag import LegalRAG
import config

# Optional: Weights & Biases integration
WANDB_ENABLED = os.getenv("WANDB_ENABLED", "false").lower() == "true"
if WANDB_ENABLED:
    try:
        import wandb
        print("[OK] Weights & Biases integration enabled")
    except ImportError:
        print("[WARNING] wandb not installed. Install with: pip install wandb")
        WANDB_ENABLED = False
