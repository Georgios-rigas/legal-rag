import boto3
import json
import re
from typing import List, Dict, Optional
from dataclasses import dataclass
from langchain_text_splitters import RecursiveCharacterTextSplitter

# --- CONFIGURATION ---
BUCKET_NAME = "test-bucket-gr7"
PREFIX = "raw_legal_cases/"

@dataclass
class ProcessedChunk:
    chunk_id: str
    parent_id: str
    text: str
    vector: Optional[List[float]] = None
    metadata: Dict = None

class LegalDocProcessor:
    def __init__(self):
        self.s3 = boto3.client('s3')
        
        # 1. PARENT SPLITTER: Large context blocks
        self.parent_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000,
            chunk_overlap=200
        )
        
        # 2. CHILD SPLITTER: Small search blocks
        self.child_splitter = RecursiveCharacterTextSplitter(
            chunk_size=400,
            chunk_overlap=50
        )

    def load_json_from_s3(self, key: str) -> Dict:
        """Downloads and parses a single JSON from S3."""
        response = self.s3.get_object(Bucket=BUCKET_NAME, Key=key)
        content = response['Body'].read().decode('utf-8')
        return json.loads(content)

    def clean_legal_text(self, text: str) -> str:
        """Cleaning Logic:
        1. Remove excessive newlines common in OCR.
        2. Remove generic headers if repetitive.
        """
        # Replace multiple newlines with a single space
        text = re.sub(r'\n+', ' ', text)
        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def process_case(self, s3_key: str):
        """The Main Pipeline Logic"""
        
        # A. Load
        raw_data = self.load_json_from_s3(s3_key)
        
        # B. Metadata Extraction (The "Recruiter Hook")
        # In Law, the Date and Court are as important as the text.
        metadata = {
            "case_id": raw_data.get("id"),
            "case_name": raw_data.get("name_abbreviation"),
            "date": raw_data.get("decision_date"), # ISO format YYYY-MM-DD
            "court": raw_data.get("court", {}).get("name_abbreviation"),
            "jurisdiction": raw_data.get("jurisdiction", {}).get("name"),
            "citation": raw_data.get("citations", [{}])[0].get("cite"),
            "source_link": f"https://s3.amazonaws.com/{BUCKET_NAME}/{s3_key}" # Data Lineage
        }

        # C. Extract the actual Opinion Text
        # Note: Some cases have multiple opinions (concurring/dissenting). 
        # For simplicity, we take the first one (usually majority).
        try:
            raw_text = raw_data['casebody']['opinions'][0]['text']
        except (KeyError, IndexError):
            print(f"Skipping {s3_key}: No opinion text found.")
            return []

        cleaned_text = self.clean_legal_text(raw_text)

        # D. Parent-Child Chunking Strategy
        chunks_to_index = []
        
        # Create Parents
        parent_docs = self.parent_splitter.create_documents([cleaned_text])
        
        for p_idx, parent in enumerate(parent_docs):
            parent_id = f"{metadata['case_id']}_P{p_idx}"
            
            # Create Children from this specific Parent
            child_docs = self.child_splitter.create_documents([parent.page_content])
            
            for c_idx, child in enumerate(child_docs):
                child_id = f"{parent_id}_C{c_idx}"
                
                chunk_obj = ProcessedChunk(
                    chunk_id=child_id,
                    parent_id=parent_id,
                    text=child.page_content, # Child text is what we embed
                    metadata={
                        **metadata,
                        "parent_text": parent.page_content, # STORE PARENT CONTEXT HERE
                        "type": "child"
                    }
                )
                chunks_to_index.append(chunk_obj)
        
        return chunks_to_index

# --- SIMULATION OF PRODUCTION RUN ---
if __name__ == "__main__":
    processor = LegalDocProcessor()
    
    # List a few files to test
    s3 = boto3.client('s3')
    objects = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=PREFIX, MaxKeys=5)
    
    if 'Contents' in objects:
        for obj in objects['Contents']:
            key = obj['Key']
            if not key.endswith('.json'): continue
            
            print(f"Processing: {key}...")
            chunks = processor.process_case(key)
            
            if chunks:
                print(f"  --> Created {len(chunks)} Child Chunks.")
                print(f"  --> Sample Child: {chunks[0].text[:50]}...")
                print(f"  --> Linked Parent: {chunks[0].metadata['parent_text'][:50]}...")
                print(f"  --> Metadata: {chunks[0].metadata['date']} | {chunks[0].metadata['court']}")
                print("-" * 50)