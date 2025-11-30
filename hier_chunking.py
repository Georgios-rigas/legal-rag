"""
Legal RAG Parent-Child Chunking System (Simplified)

Creates parent chunks (full opinions) and child chunks (paragraphs) 
for efficient retrieval + contextual generation.
"""

import json
import re
import hashlib
from dataclasses import dataclass, asdict


@dataclass
class ChunkingConfig:
    """Chunking parameters tuned for legal text."""
    target_child_tokens: int = 400
    max_child_tokens: int = 600
    min_child_tokens: int = 100
    overlap_tokens: int = 50


def estimate_tokens(text: str) -> int:
    """Rough estimate: ~4 chars per token for legal text."""
    return len(text) // 4


def clean_text(text: str) -> str:
    """Clean OCR artifacts and normalize whitespace."""
    text = re.sub(r'[\u2019\u2018]', "'", text)
    text = re.sub(r'[\u201c\u201d]', '"', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def split_into_paragraphs(text: str) -> list[str]:
    """Split on double newlines, single newlines after sentences, or by sentence groups."""
    # Try double newlines first
    paragraphs = re.split(r'\n\s*\n', text)
    
    # If that doesn't work, try single newlines
    if len(paragraphs) <= 1:
        paragraphs = re.split(r'\n', text)
    
    # If still no splits, split every ~3 sentences
    if len(paragraphs) <= 1:
        sentences = re.split(r'(?<=[.!?])\s+', text)
        paragraphs = []
        for i in range(0, len(sentences), 3):
            paragraphs.append(' '.join(sentences[i:i+3]))
    
    return [p.strip() for p in paragraphs if p.strip()]


def generate_id(case_id: int, chunk_type: str, index: int) -> str:
    """Generate deterministic chunk ID."""
    return hashlib.md5(f"{case_id}-{chunk_type}-{index}".encode()).hexdigest()[:16]


def extract_metadata(case: dict) -> dict:
    """Pull key metadata from case JSON."""
    citations = case.get('citations', [])
    official_cite = next((c['cite'] for c in citations if c.get('type') == 'official'), 
                         citations[0]['cite'] if citations else '')
    
    opinions = case.get('casebody', {}).get('opinions', [])
    first_opinion = opinions[0] if opinions else {}
    
    return {
        'case_id': case.get('id', 0),
        'case_name': case.get('name_abbreviation', case.get('name', '')),
        'decision_date': case.get('decision_date', ''),
        'court': case.get('court', {}).get('name_abbreviation', ''),
        'jurisdiction': case.get('jurisdiction', {}).get('name', ''),
        'citation': official_cite,
        'opinion_type': first_opinion.get('type', 'unknown'),
        'opinion_author': first_opinion.get('author', ''),
    }


def create_children(text: str, case_id: int, parent_id: str, metadata: dict, 
                    config: ChunkingConfig) -> list[dict]:
    """
    Create child chunks from text.
    Strategy: Combine paragraphs until target size, then start new chunk.
    """
    paragraphs = split_into_paragraphs(text)
    children = []
    
    current_text = ""
    current_tokens = 0
    
    for para in paragraphs:
        para_tokens = estimate_tokens(para)
        
        # If adding this paragraph exceeds target, save current and start new
        if current_tokens + para_tokens > config.target_child_tokens and current_tokens >= config.min_child_tokens:
            children.append({
                'chunk_id': generate_id(case_id, f"child-{parent_id}", len(children)),
                'parent_id': parent_id,
                'text': clean_text(current_text),
                'token_estimate': current_tokens,
                'chunk_index': len(children),
                'metadata': metadata
            })
            
            # Start new chunk with overlap (last ~50 tokens)
            overlap_chars = config.overlap_tokens * 4
            current_text = current_text[-overlap_chars:].strip() + "\n\n" + para
            current_tokens = estimate_tokens(current_text)
        else:
            current_text = (current_text + "\n\n" + para).strip()
            current_tokens += para_tokens
    
    # Don't forget the last chunk
    if current_tokens >= config.min_child_tokens:
        children.append({
            'chunk_id': generate_id(case_id, f"child-{parent_id}", len(children)),
            'parent_id': parent_id,
            'text': clean_text(current_text),
            'token_estimate': current_tokens,
            'chunk_index': len(children),
            'metadata': metadata
        })
    
    # Update total count
    for child in children:
        child['total_chunks'] = len(children)
    
    return children


def chunk_case(case: dict, config: ChunkingConfig = None) -> dict:
    """
    Main entry: chunk a legal case into parent-child structure.
    
    Returns:
        {
            'case_id': int,
            'case_name': str,
            'parents': [{'chunk_id', 'text', 'token_estimate', 'child_ids', 'metadata'}],
            'children': [{'chunk_id', 'parent_id', 'text', 'token_estimate', 'chunk_index', 'metadata'}]
        }
    """
    config = config or ChunkingConfig()
    case_id = case.get('id', 0)
    metadata = extract_metadata(case)
    
    parents = []
    children = []
    
    # Process each opinion
    for idx, opinion in enumerate(case.get('casebody', {}).get('opinions', [])):
        opinion_text = opinion.get('text', '')
        if not opinion_text:
            continue
        
        parent_id = generate_id(case_id, "parent", idx)
        opinion_text = clean_text(opinion_text)
        
        # Create parent
        parent = {
            'chunk_id': parent_id,
            'text': opinion_text,
            'token_estimate': estimate_tokens(opinion_text),
            'section_type': f"opinion_{opinion.get('type', 'unknown')}",
            'metadata': metadata
        }
        
        # Create children for this parent
        opinion_children = create_children(opinion_text, case_id, parent_id, metadata, config)
        parent['child_ids'] = [c['chunk_id'] for c in opinion_children]
        
        parents.append(parent)
        children.extend(opinion_children)
    
    return {
        'case_id': case_id,
        'case_name': case.get('name', ''),
        'parents': parents,
        'children': children,
        'stats': {
            'parent_count': len(parents),
            'child_count': len(children),
            'total_tokens': sum(p['token_estimate'] for p in parents)
        }
    }


def format_for_vector_db(chunked: dict) -> tuple[list[dict], list[dict]]:
    """
    Format for vector DB insertion.
    Returns (parent_records, child_records) ready for embedding.
    """
    parent_records = [{
        'id': p['chunk_id'],
        'text': p['text'],
        'metadata': {**p['metadata'], 'type': 'parent', 'child_count': len(p['child_ids'])}
    } for p in chunked['parents']]
    
    child_records = [{
        'id': c['chunk_id'],
        'text': c['text'],
        'metadata': {**c['metadata'], 'type': 'child', 'parent_id': c['parent_id'], 
                     'chunk_index': c['chunk_index']}
    } for c in chunked['children']]
    
    return parent_records, child_records


# =============================================================================
# S3 BATCH PROCESSING
# =============================================================================

def process_s3_bucket(
    bucket: str = "test-bucket-gr7",
    prefix: str = "raw_legal_cases/",
    output_path: str = "./chunked_output",
    limit: int = None
) -> dict:
    """
    Process all legal case JSONs from S3.
    
    Args:
        bucket: S3 bucket name
        prefix: S3 prefix (folder path)
        output_path: Local path to save results
        limit: Optional limit on files to process (for testing)
    
    Returns:
        Stats dict with counts
    """
    import boto3
    from pathlib import Path
    
    s3 = boto3.client('s3')
    config = ChunkingConfig()
    
    all_parents = []
    all_children = []
    processed = 0
    failed = 0
    
    # List all JSON files
    paginator = s3.get_paginator('list_objects_v2')
    json_keys = []
    
    print(f"Scanning s3://{bucket}/{prefix}...")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get('Contents', []):
            if obj['Key'].endswith('.json'):
                json_keys.append(obj['Key'])
    
    if limit:
        json_keys = json_keys[:limit]
    
    print(f"Found {len(json_keys)} JSON files")
    
    # Process each file
    for i, key in enumerate(json_keys):
        try:
            # Read from S3
            response = s3.get_object(Bucket=bucket, Key=key)
            case_data = json.loads(response['Body'].read().decode('utf-8'))
            
            # Chunk it
            chunked = chunk_case(case_data, config)
            
            # Format for vector DB
            parents, children = format_for_vector_db(chunked)
            all_parents.extend(parents)
            all_children.extend(children)
            
            processed += 1
            if processed % 100 == 0:
                print(f"Processed {processed}/{len(json_keys)}")
                
        except Exception as e:
            print(f"Failed {key}: {e}")
            failed += 1
    
    # Save outputs
    Path(output_path).mkdir(parents=True, exist_ok=True)
    
    with open(f"{output_path}/parents.json", 'w') as f:
        json.dump(all_parents, f, indent=2)
    
    with open(f"{output_path}/children.json", 'w') as f:
        json.dump(all_children, f, indent=2)
    
    stats = {
        'files_processed': processed,
        'files_failed': failed,
        'total_parents': len(all_parents),
        'total_children': len(all_children),
    }
    
    with open(f"{output_path}/stats.json", 'w') as f:
        json.dump(stats, f, indent=2)
    
    print(f"\nDone! Saved to {output_path}/")
    print(f"  Parents: {len(all_parents)}")
    print(f"  Children: {len(all_children)}")
    
    return stats


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    import sys
    
    # If command line args provided, run S3 processing
    if len(sys.argv) > 1:
        import argparse
        parser = argparse.ArgumentParser(description='Chunk legal cases from S3')
        parser.add_argument('--bucket', default='test-bucket-gr7')
        parser.add_argument('--prefix', default='raw_legal_cases/')
        parser.add_argument('--output', default='./chunked_output')
        parser.add_argument('--limit', type=int, default=None)
        args = parser.parse_args()
        
        process_s3_bucket(args.bucket, args.prefix, args.output, args.limit)
    
    # Otherwise run demo
    else:
        sample = {
            "id": 8137646,
            "name": "PENN v. WHIDDEN",
            "name_abbreviation": "Penn v. Whidden",
            "decision_date": "1945-04-16",
            "citations": [{"type": "official", "cite": "42 A.2d 136"}],
            "court": {"name_abbreviation": "D.C."},
            "jurisdiction": {"name": "D.C."},
            "casebody": {
                "opinions": [{
                    "type": "majority",
                    "author": "RICHARDSON, Chief Judge.",
                    "text": "RICHARDSON, Chief Judge.\nAction was brought by appellee as administrator for an accounting...\n\nThe intestate died November 8, 1942.\n\nAffirmed."
                }]
            }
        }
        
        result = chunk_case(sample)
        print(f"Demo - Parents: {result['stats']['parent_count']}, Children: {result['stats']['child_count']}")