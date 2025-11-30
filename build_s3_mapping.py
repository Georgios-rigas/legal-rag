"""
Build mapping from case_id to S3 file path
This script reads all JSON files from S3 and creates a mapping file
"""
import boto3
import json
from tqdm import tqdm

BUCKET_NAME = "test-bucket-gr7"
TARGET_FOLDER = "raw_legal_cases"

def build_mapping():
    """Build case_id -> S3 key mapping from all files in S3."""
    s3_client = boto3.client('s3')

    print(f"Scanning S3 bucket: {BUCKET_NAME}/{TARGET_FOLDER}")

    # List all objects
    paginator = s3_client.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=BUCKET_NAME, Prefix=f"{TARGET_FOLDER}/")

    mapping = {}
    total_files = 0

    for page in pages:
        if 'Contents' not in page:
            continue

        for obj in tqdm(page['Contents'], desc="Processing files"):
            s3_key = obj['Key']

            # Only process JSON files
            if not s3_key.endswith('.json'):
                continue

            total_files += 1

            try:
                # Download and parse the JSON file
                response = s3_client.get_object(Bucket=BUCKET_NAME, Key=s3_key)
                case_data = json.loads(response['Body'].read())

                case_id = case_data.get('id')
                if case_id:
                    mapping[str(case_id)] = s3_key

            except Exception as e:
                print(f"\nError processing {s3_key}: {e}")
                continue

    # Save mapping to file
    output_file = "case_id_to_s3_mapping.json"
    with open(output_file, 'w') as f:
        json.dump(mapping, f, indent=2)

    print(f"\n✓ Processed {total_files} files")
    print(f"✓ Created mapping for {len(mapping)} cases")
    print(f"✓ Saved to {output_file}")

    return mapping

if __name__ == "__main__":
    build_mapping()
