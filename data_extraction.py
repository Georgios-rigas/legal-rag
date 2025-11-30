import boto3
import requests
from bs4 import BeautifulSoup
import zipfile
import io
import os

# --- CONFIGURATION ---
BASE_URL = "https://static.case.law/a2d/"  # The URL from your screenshot
BUCKET_NAME = "test-bucket-gr7"            # Your S3 Bucket
TARGET_FOLDER = "raw_legal_cases"          # Folder inside S3 to keep things tidy
DOWNLOAD_LIMIT = 100                      # Limit to first 10 links

def upload_legal_data():
    # 1. Initialize S3 Client
    s3 = boto3.client('s3')
    
    print(f"🔍 Scraping {BASE_URL} for ZIP files...")
    
    # 2. Get the HTML to find the links
    response = requests.get(BASE_URL)
    if response.status_code != 200:
        print("Failed to access website.")
        return

    soup = BeautifulSoup(response.content, 'html.parser')

    # Find all links ending in .zip
    zip_links = [a['href'] for a in soup.find_all('a') if a.get('href', '').endswith('.zip')]

    # Take only the first 10
    target_links = zip_links[:DOWNLOAD_LIMIT]
    print(f"✅ Found {len(zip_links)} volumes. Downloading the first {len(target_links)}...")

    # Debug: show first link format
    if target_links:
        print(f"🔍 Sample link: {target_links[0]}")

    # 3. Process each ZIP
    for zip_filename in target_links:
        # Build full URL - check if it's already a full URL or just a filename
        if zip_filename.startswith('http'):
            full_url = zip_filename
        else:
            full_url = BASE_URL + zip_filename

        print(f"\n⬇️  Downloading: {full_url} ...")
        
        # Stream download the zip (better for memory)
        try:
            zip_resp = requests.get(full_url, timeout=30)
        except Exception as e:
            print(f"   ❌ Failed to download {zip_filename}: {e}")
            continue

        if zip_resp.status_code == 200:
            # Open zip in memory without saving to disk
            with zipfile.ZipFile(io.BytesIO(zip_resp.content)) as z:
                
                # Filter for files inside the 'json/' folder
                json_files = [f for f in z.namelist() if f.endswith('.json') and 'json/' in f]
                
                print(f"   📂 Found {len(json_files)} JSON cases inside. Uploading to S3...")
                
                # 4. Upload each JSON to S3
                for json_file in json_files:
                    # Read the JSON content
                    file_content = z.read(json_file)

                    # Create a nice S3 key (path)
                    # Example: raw_legal_cases/31/0647-01.json
                    # Extract just the filename from the URL (e.g., "31.zip" from full URL)
                    zip_basename = os.path.basename(zip_filename)
                    volume_name = zip_basename.replace('.zip', '')
                    clean_filename = os.path.basename(json_file) # removes 'json/' prefix
                    s3_key = f"{TARGET_FOLDER}/{volume_name}/{clean_filename}"
                    
                    # Upload
                    s3.put_object(
                        Bucket=BUCKET_NAME,
                        Key=s3_key,
                        Body=file_content,
                        ContentType='application/json'
                    )
                
                print(f"   ✅ Uploaded contents of {zip_filename}")
        else:
            print(f"   ❌ Failed to download {zip_filename} - HTTP Status: {zip_resp.status_code}")
            print(f"   Response: {zip_resp.text[:200]}")

if __name__ == "__main__":
    try:
        upload_legal_data()
        print("\n🎉 All Done! Check your S3 Bucket.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Make sure your AWS credentials are configured correctly!")