# Legal RAG MLOps Deployment Guide

## Overview

This document describes the complete MLOps CI/CD pipeline for the Legal RAG (Retrieval-Augmented Generation) system, including deployment architecture, automated pipelines, and operational workflows.

## System Architecture

### Components

1. **Frontend**: React/TypeScript application with Tailwind CSS
   - Hosted on Azure Kubernetes Service (AKS)
   - Load Balancer IP: `52.166.46.37`
   - Port: 80

2. **Backend API**: FastAPI Python application
   - Hosted on Azure Kubernetes Service (AKS)
   - Load Balancer IP: `20.50.147.24`
   - Port: 8000
   - Container Registry: Azure Container Registry (ACR) `legalragpersonalacr.azurecr.io`

3. **Vector Database**: Pinecone
   - Index: `legal-cases`
   - Dimensions: 1536 (OpenAI embeddings)
   - Vectors: 9,594 legal case chunks
   - Environment: `us-east-1`

4. **Storage**: AWS S3
   - Stores original legal case PDFs
   - Referenced via `case_id_to_s3_mapping.json`

5. **LLM Services**:
   - **Embeddings**: OpenAI `text-embedding-3-small` (1536 dimensions)
   - **Generation**: Anthropic Claude `claude-sonnet-4-5-20250929`

---

## CI/CD Pipeline Architecture

### Pipeline Files

1. **Backend Pipeline**: `.github/workflows/backend-cicd.yml` or `azure-pipelines-backend.yml`
2. **Frontend Pipeline**: `.github/workflows/frontend-cicd.yml` or `azure-pipelines-frontend.yml`

### Pipeline Triggers

Both pipelines are triggered automatically on:
- Push to `main` or `master` branch
- Changes to specific files (path filters)

#### Backend Triggers
```yaml
paths:
  include:
    - api.py
    - query_rag.py
    - config.py
    - pdf_generator.py
    - requirements.txt
    - Dockerfile
    - chunked_output/**
    - case_id_to_s3_mapping.json
    - azure-pipelines-backend.yml
```

#### Frontend Triggers
```yaml
paths:
  include:
    - frontend/**
    - azure-pipelines-frontend.yml
```

---

## Backend CI/CD Pipeline

### Stage 1: Build and Push Docker Image

#### Step 1: Aggressive Memory Cleanup
- **Purpose**: Free up memory on self-hosted Windows agent
- **Actions**:
  - Stop all running containers
  - Remove stopped containers
  - Remove dangling images
  - Remove old images (keep only last 2 versions)
  - Remove build cache
  - System-wide Docker cleanup

#### Step 2: Login to ACR
```bash
az acr login --name legalragpersonalacr
```

#### Step 3: Build Docker Image
- **Base Image**: `python:3.11-slim`
- **Tags**:
  - `$(Build.BuildId)` (e.g., `20251201.10`)
  - `latest`
- **Size**: ~500MB (after removing sentence-transformers)
- **Previous Size**: 4.46GB (with local embedding model)

**Dockerfile Overview**:
```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y build-essential

# Install Python dependencies (no sentence-transformers!)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY config.py query_rag.py api.py pdf_generator.py .
COPY case_id_to_s3_mapping.json .
COPY chunked_output/ ./chunked_output/

EXPOSE 8000
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Step 4: Push Build ID Tag to ACR
- Push image with build-specific tag (e.g., `20251201.10`)
- Timeout: 2 hours
- Uses PowerShell job with progress reporting

#### Step 5: Push Latest Tag to ACR
- Push image with `latest` tag
- Reuses layers from previous push (faster)
- Timeout: 30 minutes

#### Step 6: Cleanup After Push
- Remove pushed images from local cache
- Free memory immediately
- Quick image prune

### Stage 2: Deploy to AKS

#### Step 1: Get AKS Credentials
```bash
az aks get-credentials \
  --resource-group legal-rag-personal-rg \
  --name legal-rag-personal-aks \
  --overwrite-existing
```

#### Step 2: Update Deployment Image
```bash
kubectl set image deployment/legal-rag-api \
  api=legalragpersonalacr.azurecr.io/legal-rag-api:$(Build.BuildId)
```

#### Step 3: Wait for Rollout
```bash
kubectl rollout status deployment/legal-rag-api --timeout=10m
```

#### Step 4: Verify Deployment
- Check pod status
- Verify readiness probes
- Check logs for successful startup

---

## Frontend CI/CD Pipeline

### Stage 1: Build and Push Docker Image

#### Step 1: Build React Application
```bash
npm install
npm run build
```
- Output: `dist/` directory with optimized static files

#### Step 2: Build Docker Image
- **Base Image**: `nginx:alpine`
- **Tags**:
  - `$(Build.BuildId)` (incrementing number)
  - `latest`
- **Size**: ~50MB

**Dockerfile Overview**:
```dockerfile
FROM node:18 AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

#### Step 3: Push to ACR
- Push both build ID tag and `latest` tag

### Stage 2: Deploy to AKS

#### Step 1: Update Deployment
```bash
kubectl set image deployment/legal-rag-frontend \
  frontend=legalragpersonalacr.azurecr.io/legal-rag-frontend:$(Build.BuildId)
```

#### Step 2: Wait for Rollout
```bash
kubectl rollout status deployment/legal-rag-frontend --timeout=5m
```

---

## Kubernetes Configuration

### Backend Deployment (`k8s-deployment-personal.yaml`)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: legal-rag-api
spec:
  replicas: 1
  selector:
    matchLabels:
      app: legal-rag-api
  template:
    metadata:
      labels:
        app: legal-rag-api
    spec:
      containers:
      - name: api
        image: legalragpersonalacr.azurecr.io/legal-rag-api:latest
        imagePullPolicy: Always
        ports:
        - containerPort: 8000
        env:
        - name: EMBEDDING_PROVIDER
          value: "openai"
        - name: LLM_PROVIDER
          value: "claude"
        - name: PINECONE_ENVIRONMENT
          value: "us-east-1"
        - name: PINECONE_API_KEY
          valueFrom:
            secretKeyRef:
              name: legal-rag-secrets
              key: PINECONE_API_KEY
        - name: ANTHROPIC_API_KEY
          valueFrom:
            secretKeyRef:
              name: legal-rag-secrets
              key: ANTHROPIC_API_KEY
        - name: AWS_ACCESS_KEY_ID
          valueFrom:
            secretKeyRef:
              name: legal-rag-secrets
              key: AWS_ACCESS_KEY_ID
        - name: AWS_SECRET_ACCESS_KEY
          valueFrom:
            secretKeyRef:
              name: legal-rag-secrets
              key: AWS_SECRET_ACCESS_KEY
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: legal-rag-secrets
              key: OPENAI_API_KEY
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /docs
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /docs
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: legal-rag-api-service
spec:
  type: LoadBalancer
  selector:
    app: legal-rag-api
  ports:
  - port: 80
    targetPort: 8000
```

### Frontend Deployment (`k8s-frontend-deployment.yaml`)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: legal-rag-frontend
spec:
  replicas: 1
  selector:
    matchLabels:
      app: legal-rag-frontend
  template:
    metadata:
      labels:
        app: legal-rag-frontend
    spec:
      containers:
      - name: frontend
        image: legalragpersonalacr.azurecr.io/legal-rag-frontend:latest
        imagePullPolicy: Always
        ports:
        - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: legal-rag-frontend-service
spec:
  type: LoadBalancer
  selector:
    app: legal-rag-frontend
  ports:
  - port: 80
    targetPort: 80
```

### Secrets Management

Secrets are stored in Kubernetes and referenced by deployments:

```bash
kubectl create secret generic legal-rag-secrets \
  --from-literal=ANTHROPIC_API_KEY='sk-ant-...' \
  --from-literal=AWS_ACCESS_KEY_ID='AKIA...' \
  --from-literal=AWS_SECRET_ACCESS_KEY='...' \
  --from-literal=PINECONE_API_KEY='pcsk_...' \
  --from-literal=OPENAI_API_KEY='sk-proj-...'
```

---

## Data Pipeline (Indexing)

### Ingestion Pipeline

The data pipeline runs **locally** (not in CI/CD) to process legal cases and index them to Pinecone.

#### Files
- `ingest_pipeline.py`: Main orchestration script
- `embed_and_index.py`: Embedding generation and Pinecone indexing

#### Process Flow

1. **Load Documents**
   ```python
   # Load chunked legal cases
   children = load('./chunked_output/children.json')  # 9,594 chunks
   parents = load('./chunked_output/parents.json')    # 1,671 cases
   ```

2. **Generate Embeddings** (OpenAI)
   ```python
   client = OpenAI(api_key=config.OPENAI_API_KEY)

   for batch in chunks(texts, batch_size=100):
       response = client.embeddings.create(
           model="text-embedding-3-small",
           input=batch
       )
       embeddings.extend([item.embedding for item in response.data])
   ```
   - Model: `text-embedding-3-small`
   - Dimensions: 1536
   - Batch size: 100 texts per request
   - Retry logic: Exponential backoff for rate limits

3. **Index to Pinecone**
   ```python
   # Create/connect to index
   pc = Pinecone(api_key=config.PINECONE_API_KEY)

   if "legal-cases" not in pc.list_indexes().names():
       pc.create_index(
           name="legal-cases",
           dimension=1536,
           metric="cosine"
       )

   index = pc.Index("legal-cases")

   # Upsert vectors in batches
   for batch in chunks(vectors, batch_size=100):
       index.upsert(vectors=batch)
   ```

4. **Verify Indexing**
   ```bash
   python check_index.py
   # Output: Total vectors: 9594, Dimension: 1536
   ```

### Re-indexing Process

When switching embedding providers or updating the index:

```bash
# Delete old index
python reindex_with_openai.py

# Re-run embedding and indexing
python embed_and_index.py
```

**Important**: Re-indexing is **NOT automated** in CI/CD because:
- It's expensive (API costs)
- It takes time (~10-15 minutes)
- Only needed when:
  - Switching embedding models
  - Adding new legal cases
  - Changing chunking strategy

---

## MLOps Workflow

### Development Workflow

1. **Local Development**
   ```bash
   # Make code changes
   vim api.py

   # Test locally
   python -m uvicorn api:app --reload

   # Run frontend locally
   cd frontend && npm run dev
   ```

2. **Commit Changes**
   ```bash
   git add .
   git commit -m "Description of changes"
   ```

3. **Push to Azure DevOps**
   ```bash
   git push azuredevops main
   ```

4. **Automatic Pipeline Trigger**
   - Backend pipeline triggers if backend files changed
   - Frontend pipeline triggers if frontend files changed
   - Both can run in parallel

5. **Monitor Pipeline**
   - View in Azure DevOps → Pipelines
   - Check build logs for errors
   - Verify Docker image pushed to ACR

6. **Automatic Deployment**
   - Pipeline automatically deploys to AKS
   - Kubernetes performs rolling update
   - Old pods remain until new pods are ready

7. **Verification**
   ```bash
   # Check deployment status
   kubectl get pods -l app=legal-rag-api
   kubectl get pods -l app=legal-rag-frontend

   # Check logs
   kubectl logs -l app=legal-rag-api --tail=50

   # Test endpoints
   curl http://52.166.46.37  # Frontend
   curl http://20.50.147.24/docs  # Backend API docs
   ```

### Production Monitoring

```bash
# Check all deployments
kubectl get deployments

# Check all services
kubectl get services

# Check pod health
kubectl get pods --all-namespaces

# View pod logs
kubectl logs <pod-name> --tail=100 --follow

# Describe pod (for troubleshooting)
kubectl describe pod <pod-name>

# Check resource usage
kubectl top pods
```

### Rollback Procedure

If a deployment fails:

```bash
# Rollback to previous version
kubectl rollout undo deployment/legal-rag-api

# Check rollout status
kubectl rollout status deployment/legal-rag-api

# View rollout history
kubectl rollout history deployment/legal-rag-api
```

---

## Configuration Management

### Environment Variables

Backend requires these environment variables:

| Variable | Source | Purpose |
|----------|--------|---------|
| `EMBEDDING_PROVIDER` | Deployment | Set to "openai" for cloud embeddings |
| `LLM_PROVIDER` | Deployment | Set to "claude" for Anthropic |
| `PINECONE_API_KEY` | Secret | Pinecone vector database access |
| `PINECONE_ENVIRONMENT` | Deployment | Pinecone region (us-east-1) |
| `ANTHROPIC_API_KEY` | Secret | Claude API access |
| `OPENAI_API_KEY` | Secret | OpenAI embeddings API access |
| `AWS_ACCESS_KEY_ID` | Secret | AWS S3 access for PDFs |
| `AWS_SECRET_ACCESS_KEY` | Secret | AWS S3 secret key |

### Updating Secrets

```bash
# Delete old secret
kubectl delete secret legal-rag-secrets

# Create new secret
kubectl create secret generic legal-rag-secrets \
  --from-literal=PINECONE_API_KEY='new-key' \
  --from-literal=ANTHROPIC_API_KEY='new-key' \
  --from-literal=AWS_ACCESS_KEY_ID='new-key' \
  --from-literal=AWS_SECRET_ACCESS_KEY='new-key' \
  --from-literal=OPENAI_API_KEY='new-key'

# Restart deployment to pick up new secrets
kubectl rollout restart deployment/legal-rag-api
```

### Updating Environment Variables

```bash
# Update single environment variable
kubectl set env deployment/legal-rag-api EMBEDDING_PROVIDER=openai

# Update via patch (for complex changes)
kubectl patch deployment legal-rag-api --type='json' -p='[{
  "op": "add",
  "path": "/spec/template/spec/containers/0/env/-",
  "value": {
    "name": "NEW_VAR",
    "value": "new-value"
  }
}]'
```

---

## Troubleshooting Guide

### Common Issues

#### 1. Pod CrashLoopBackOff

**Symptoms**: Pod keeps restarting
```bash
kubectl get pods
# NAME                            READY   STATUS             RESTARTS
# legal-rag-api-xxx-yyy           0/1     CrashLoopBackOff   5
```

**Diagnosis**:
```bash
# Check logs
kubectl logs legal-rag-api-xxx-yyy

# Check events
kubectl describe pod legal-rag-api-xxx-yyy
```

**Common Causes**:
- Missing environment variable
- Missing secret
- Code error on startup
- Port already in use
- Resource limits too low

#### 2. ImagePullBackOff

**Symptoms**: Cannot pull Docker image
```bash
kubectl get pods
# NAME                            READY   STATUS              RESTARTS
# legal-rag-api-xxx-yyy           0/1     ImagePullBackOff    0
```

**Diagnosis**:
```bash
kubectl describe pod legal-rag-api-xxx-yyy | grep -A 5 "Failed"
```

**Common Causes**:
- Image tag doesn't exist in ACR
- ACR authentication issue
- Image name typo

**Solution**:
```bash
# Check available images in ACR
az acr repository show-tags --name legalragpersonalacr --repository legal-rag-api

# Use correct tag
kubectl set image deployment/legal-rag-api api=legalragpersonalacr.azurecr.io/legal-rag-api:latest
```

#### 3. Dimension Mismatch Error

**Symptoms**: Query fails with dimension error

**Cause**: Embedding dimensions don't match Pinecone index
- Old: Local embeddings (384 dimensions)
- New: OpenAI embeddings (1536 dimensions)

**Solution**: Re-index Pinecone with correct dimensions
```bash
python reindex_with_openai.py
python embed_and_index.py
```

#### 4. ModuleNotFoundError: sentence_transformers

**Symptoms**: Pod crashes on startup with import error

**Cause**: Code still imports sentence_transformers but it's not in requirements.txt

**Solution**: Make import conditional
```python
# query_rag.py
if self.embedding_provider == "openai":
    self.openai_client = OpenAI(api_key=config.OPENAI_API_KEY)
else:
    from sentence_transformers import SentenceTransformer
    self.embedding_model = SentenceTransformer(config.LOCAL_EMBEDDING_MODEL)
```

#### 5. Frontend Shows "Failed to get response"

**Symptoms**: Frontend loads but queries fail

**Diagnosis**:
```bash
# Check if frontend has correct backend URL
kubectl logs -l app=legal-rag-frontend

# Check backend logs
kubectl logs -l app=legal-rag-api --tail=50
```

**Common Causes**:
- Frontend pointing to wrong backend IP
- Backend pod not running
- Backend returning 500 error

**Solution**:
```bash
# Get current backend IP
kubectl get svc legal-rag-api-service
# EXTERNAL-IP: 20.50.147.24

# Update frontend App.tsx
const API_BASE_URL = 'http://20.50.147.24'

# Rebuild and redeploy frontend
git add frontend/src/App.tsx
git commit -m "Update backend URL"
git push azuredevops main
```

---

## Cost Optimization

### Docker Image Size Reduction

**Before**: 4.46 GB (with sentence-transformers)
**After**: ~500 MB (OpenAI embeddings only)

**Savings**:
- Faster build times (~10 minutes → ~3 minutes)
- Faster push to ACR (~8 minutes → ~2 minutes)
- Less memory during build (95% → 30%)
- Faster pod startup (~60s → ~15s)

### API Cost Management

#### OpenAI Embeddings
- Model: `text-embedding-3-small`
- Cost: ~$0.00002 per 1K tokens
- 9,594 chunks × ~200 tokens = ~2M tokens
- Total indexing cost: ~$0.04 (one-time)
- Query cost: ~$0.00004 per query

#### Anthropic Claude
- Model: `claude-sonnet-4-5-20250929`
- Input: ~$3 per 1M tokens
- Output: ~$15 per 1M tokens
- Average query: ~2K input + ~500 output tokens
- Cost per query: ~$0.013

**Monthly estimate** (100 queries/day):
- OpenAI embeddings: $0.12
- Claude generation: $39
- **Total: ~$40/month**

---

## Performance Metrics

### Build Times
- Backend build: 3-5 minutes
- Backend push: 2-3 minutes
- Frontend build: 1-2 minutes
- Frontend push: 1 minute
- **Total pipeline: ~7-11 minutes**

### Query Performance
- Embedding generation: ~200ms
- Pinecone search: ~300ms
- LLM generation: ~3-5s
- **Total query time: ~4-6 seconds**

### System Capacity
- Backend pods: 1 replica (can scale to 10+)
- Frontend pods: 1 replica (can scale to 10+)
- Concurrent users: ~50 (with current setup)
- Max queries/second: ~10

### Resource Usage
- Backend CPU: 250m request, 1000m limit
- Backend Memory: 512Mi request, 2Gi limit
- Frontend CPU: minimal
- Frontend Memory: ~100Mi

---

## Security Best Practices

### Secrets Management
✅ **DO**:
- Store API keys in Kubernetes secrets
- Reference secrets via `valueFrom.secretKeyRef`
- Never commit secrets to Git
- Use `.env` for local development only (in `.gitignore`)

❌ **DON'T**:
- Hardcode API keys in code
- Commit `.env` file
- Use plaintext secrets in deployment YAML

### GitHub Push Protection
- GitHub automatically scans for exposed secrets
- Blocks pushes containing API keys
- Example: `error: GH013: Repository rule violations found`

**Solution**: Remove hardcoded secrets, use environment variables

### Network Security
- AKS cluster has network policies
- Load balancers expose only necessary ports (80, 8000)
- Backend not directly accessible from internet (only via service)

---

## Disaster Recovery

### Backup Strategy

1. **Code**: Stored in Git (Azure DevOps + GitHub)
2. **Docker Images**: Stored in ACR (retention: last 10 builds)
3. **Vector Database**: Pinecone (managed service, automatic backups)
4. **Original Data**: AWS S3 (versioning enabled)
5. **Processed Data**: `chunked_output/` in Git

### Recovery Procedures

#### Complete System Failure

1. **Recreate AKS Cluster**
   ```bash
   az aks create --resource-group legal-rag-personal-rg \
     --name legal-rag-personal-aks \
     --node-count 1 \
     --enable-addons monitoring
   ```

2. **Recreate Secrets**
   ```bash
   kubectl create secret generic legal-rag-secrets \
     --from-literal=... (from secure backup)
   ```

3. **Deploy Applications**
   ```bash
   kubectl apply -f k8s-deployment-personal.yaml
   kubectl apply -f k8s-frontend-deployment.yaml
   ```

4. **Re-index Pinecone** (if index lost)
   ```bash
   python embed_and_index.py
   ```

#### ACR Deletion

- Images can be rebuilt from Git using CI/CD pipeline
- Trigger manual pipeline run
- All images rebuilt from source in ~15 minutes

#### Data Loss (S3 or Pinecone)

- S3: Restore from versioning or re-scrape legal cases
- Pinecone: Re-run `embed_and_index.py` from `chunked_output/`

---

## Future Improvements

### Scalability
- [ ] Add horizontal pod autoscaling (HPA)
- [ ] Implement caching layer (Redis) for frequent queries
- [ ] Use CDN for frontend static assets

### Monitoring
- [ ] Add Prometheus for metrics collection
- [ ] Add Grafana for visualization
- [ ] Implement alerting for pod failures
- [ ] Add request tracing (OpenTelemetry)

### CI/CD
- [ ] Add automated testing (pytest, jest)
- [ ] Add security scanning (Snyk, Trivy)
- [ ] Implement blue-green deployments
- [ ] Add canary deployments for gradual rollout

### Data Pipeline
- [ ] Automate indexing pipeline in CI/CD
- [ ] Add incremental indexing (only new cases)
- [ ] Implement data versioning
- [ ] Add data quality checks

---

## Reference Commands

### Kubernetes
```bash
# Get cluster info
kubectl cluster-info

# Get all resources
kubectl get all

# Get deployments
kubectl get deployments

# Get pods
kubectl get pods -l app=legal-rag-api
kubectl get pods -l app=legal-rag-frontend

# Get services
kubectl get services

# Get secrets
kubectl get secrets

# Describe resource
kubectl describe deployment legal-rag-api
kubectl describe pod <pod-name>
kubectl describe service legal-rag-api-service

# Logs
kubectl logs <pod-name>
kubectl logs -l app=legal-rag-api --tail=100 --follow

# Execute command in pod
kubectl exec -it <pod-name> -- /bin/bash

# Port forward (for local testing)
kubectl port-forward service/legal-rag-api-service 8000:80

# Apply configuration
kubectl apply -f k8s-deployment-personal.yaml

# Delete resource
kubectl delete deployment legal-rag-api
kubectl delete service legal-rag-api-service

# Rollout management
kubectl rollout status deployment/legal-rag-api
kubectl rollout history deployment/legal-rag-api
kubectl rollout undo deployment/legal-rag-api
kubectl rollout restart deployment/legal-rag-api

# Resource usage
kubectl top nodes
kubectl top pods

# Update image
kubectl set image deployment/legal-rag-api api=legalragpersonalacr.azurecr.io/legal-rag-api:latest

# Update environment variable
kubectl set env deployment/legal-rag-api EMBEDDING_PROVIDER=openai

# Scale deployment
kubectl scale deployment/legal-rag-api --replicas=3
```

### Azure CLI
```bash
# Login
az login

# Set subscription
az account set --subscription "Azure subscription 1"

# Get AKS credentials
az aks get-credentials --resource-group legal-rag-personal-rg --name legal-rag-personal-aks

# ACR login
az acr login --name legalragpersonalacr

# List images in ACR
az acr repository list --name legalragpersonalacr
az acr repository show-tags --name legalragpersonalacr --repository legal-rag-api

# Delete image from ACR
az acr repository delete --name legalragpersonalacr --image legal-rag-api:old-tag
```

### Docker
```bash
# Build image
docker build -t legalragpersonalacr.azurecr.io/legal-rag-api:latest .

# Push image
docker push legalragpersonalacr.azurecr.io/legal-rag-api:latest

# Run locally
docker run -p 8000:8000 --env-file .env legalragpersonalacr.azurecr.io/legal-rag-api:latest

# Clean up
docker system prune -af
```

### Git
```bash
# Commit and push
git add .
git commit -m "Description"
git push azuredevops main
git push origin main  # Also push to GitHub

# View recent commits
git log --oneline -10

# View changes
git diff
git status
```

---

## Support and Contact

For issues or questions:
- Check Azure DevOps pipeline logs
- Review Kubernetes pod logs
- Check this documentation
- Contact: georgios.rigas@example.com (update with actual contact)

---

**Document Version**: 1.0
**Last Updated**: December 1, 2025
**Author**: MLOps Team
**Status**: Production
