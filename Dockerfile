FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY config.py .
COPY query_rag.py .
COPY api.py .
COPY pdf_generator.py .
COPY case_id_to_s3_mapping.json .

# Copy chunked data files (preserve directory structure)
COPY chunked_output/parents.json ./chunked_output/parents.json
COPY chunked_output/children.json ./chunked_output/children.json

# Expose port
EXPOSE 8000

# Run the FastAPI server
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
