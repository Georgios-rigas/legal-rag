# Legal RAG Chatbot - End-to-End System Overview

## 🎯 Project Summary
AI-powered legal research assistant that provides accurate answers based on 1,671+ real court cases using Retrieval-Augmented Generation (RAG) architecture.

---

## 🏗️ System Architecture

### **Frontend**
- **Framework**: React 18 with TypeScript
- **Styling**: Tailwind CSS with custom navy/teal gradient theme
- **UI Components**:
  - Framer Motion for animations
  - Custom Aceternity sparkles effects
  - React Router for case viewer navigation
  - Lucide React icons
- **Key Features**:
  - Real-time chat interface with message history
  - Clickable citations opening in-page case viewer
  - Professional slate gray message bubbles
  - Responsive design with Inter font family
  - Example questions for quick start

### **Backend API**
- **Framework**: FastAPI (Python)
- **Server**: Uvicorn ASGI server
- **Endpoints**:
  - `POST /api/query` - RAG query processing
  - `GET /api/case/{case_id}` - Case content retrieval
  - `GET /api/download/{case_id}` - PDF generation
  - `GET /api/stats` - System statistics
  - `GET /health` - Health check
- **Features**:
  - CORS enabled for cross-origin requests
  - Async request handling
  - PDF generation with ReportLab

### **RAG Pipeline**
- **Vector Database**: Pinecone (serverless)
- **Embeddings**: OpenAI text-embedding-3-small (1536 dimensions)
- **LLM**: Claude Sonnet 4.5 (Anthropic)
- **Chunking Strategy**:
  - Parent-child hierarchical chunking
  - Parent chunks: 3000 chars
  - Child chunks: 500 chars with 100 char overlap
- **Retrieval**:
  - Semantic search via embeddings
  - Top-K retrieval with relevance scoring
  - Context window optimization

### **Data Storage**
- **Cloud Storage**: AWS S3
  - Bucket: `test-bucket-gr7`
  - Raw legal cases in JSON format
  - Case ID to S3 key mapping
- **Local Processing**:
  - Chunked data stored in `/chunked_data/`
  - Parent and child chunk JSON files
  - Metadata preservation

---

## ☁️ Cloud Infrastructure

### **Kubernetes (AKS - Azure Kubernetes Service)**
- **Cluster Configuration**:
  - Resource group: `legal-rag-personal-rg`
  - Location: East US
  - Node pools with auto-scaling
- **Deployments**:
  - Backend deployment (FastAPI)
  - Frontend deployment (Nginx serving React build)
- **Services**:
  - Backend ClusterIP service
  - Frontend LoadBalancer service
- **ConfigMaps & Secrets**:
  - API keys (Pinecone, OpenAI, Anthropic, AWS)
  - Environment variables
  - S3 bucket configuration

### **Azure DevOps CI/CD**
- **Pipelines**:
  - **Backend Pipeline** (`backend-cicd.yml`):
    - Build Docker image
    - Push to Azure Container Registry (ACR)
    - Deploy to AKS
    - Health checks
  - **Frontend Pipeline** (`frontend-cicd.yml`):
    - npm install & build
    - Docker image creation
    - Push to ACR
    - Kubernetes deployment
- **Triggers**:
  - Automated on push to main branch
  - Path filters for frontend/backend changes
- **Stages**:
  - Build → Test → Deploy → Verify

### **Container Registry**
- **Azure Container Registry (ACR)**
  - Backend image: `legal-rag-backend`
  - Frontend image: `legal-rag-frontend`
  - Versioned with build IDs

---

## 🔧 Technology Stack

### **Languages & Frameworks**
- Python 3.11+ (Backend)
- TypeScript (Frontend)
- React 18
- FastAPI
- Node.js 20+

### **AI/ML Services**
- **Anthropic Claude**: Sonnet 4.5 for response generation
- **OpenAI**: text-embedding-3-small for embeddings
- **Pinecone**: Vector database for semantic search

### **Cloud Providers**
- **Azure**: Kubernetes (AKS), Container Registry, DevOps
- **AWS**: S3 for data storage

### **Key Libraries**
- **Backend**:
  - `langchain` - RAG orchestration
  - `pinecone-client` - Vector DB client
  - `boto3` - AWS SDK
  - `reportlab` - PDF generation
  - `anthropic` - Claude API
  - `openai` - Embeddings API
- **Frontend**:
  - `axios` - HTTP client
  - `framer-motion` - Animations
  - `react-router-dom` - Routing
  - `react-markdown` - Markdown rendering

### **DevOps Tools**
- Docker & Docker Compose
- Kubernetes (kubectl)
- Azure CLI
- GitHub Actions (alternative to Azure DevOps)
- Helm (optional for package management)

---

## 📊 Data Pipeline

### **Ingestion**
1. Legal cases downloaded from Caselaw Access Project API
2. JSON files stored in AWS S3
3. Metadata extraction (case name, citation, court, date)

### **Processing**
1. **Chunking**: Hierarchical parent-child strategy
2. **Embedding**: OpenAI embeddings for all child chunks
3. **Indexing**: Upload to Pinecone with metadata
4. **Mapping**: Case ID → S3 key lookup table

### **Query Flow**
1. User question → Embedding generation
2. Semantic search in Pinecone → Top-K child chunks
3. Parent chunk retrieval for context
4. Claude Sonnet 4.5 generates answer
5. Sources returned with relevance scores
6. Frontend displays answer + clickable citations

---

## 🚀 Deployment Architecture

```
User Browser
    ↓
Azure Load Balancer
    ↓
AKS Cluster (East US)
    ├── Frontend Pods (Nginx + React)
    │   └── Service: LoadBalancer
    └── Backend Pods (FastAPI)
        ├── Service: ClusterIP
        ├── → Pinecone (Vector Search)
        ├── → AWS S3 (Case Data)
        ├── → OpenAI API (Embeddings)
        └── → Anthropic API (LLM)
```

---

## 📁 Key Files

### **Infrastructure**
- `k8s-backend-deployment.yaml` - Backend Kubernetes manifest
- `k8s-frontend-deployment.yaml` - Frontend Kubernetes manifest
- `.github/workflows/backend-cicd.yml` - Backend CI/CD
- `.github/workflows/frontend-cicd.yml` - Frontend CI/CD
- `Dockerfile` (backend) - API container image
- `frontend/Dockerfile` - Frontend container image

### **Backend**
- `api.py` - FastAPI application
- `query_rag.py` - RAG query logic
- `ingest_pipeline.py` - Data ingestion
- `pdf_generator.py` - PDF creation
- `config.py` - Configuration management
- `.env` - Environment variables

### **Frontend**
- `frontend/src/App.tsx` - Main React app
- `frontend/src/CaseViewer.tsx` - Case detail view
- `frontend/src/components/ui/sparkles.tsx` - Sparkle animation
- `frontend/tailwind.config.js` - Tailwind configuration
- `frontend/index.html` - HTML entry point

---

## 🔐 Security & Configuration

### **Secrets Management**
- Azure Key Vault for production secrets
- Kubernetes secrets for API keys
- Environment-based configuration (.env files)

### **API Keys Required**
- `PINECONE_API_KEY`
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`

### **CORS Configuration**
- Allow all origins (`*`) for production
- Credentials enabled
- All methods and headers allowed

---

## 📈 Performance & Scalability

### **Optimization**
- Horizontal pod autoscaling (HPA)
- Connection pooling for Pinecone
- Async/await for concurrent requests
- Vector index optimization
- CDN for frontend assets (optional)

### **Monitoring** (Recommended)
- Azure Monitor / Application Insights
- Kubernetes metrics server
- Pinecone dashboard for vector DB stats
- Custom health check endpoints

---

## 🎨 UI/UX Features

- **Professional Design**:
  - Corporate navy/teal gradient background (#0a1929, #0d2438)
  - Slate gray message bubbles
  - Inter font family
  - Sparkles animation in header

- **User Experience**:
  - Real-time streaming responses
  - Copy-to-clipboard functionality
  - Clickable case citations
  - In-page case viewer with full opinion text
  - PDF download option
  - Example questions for onboarding
  - Responsive mobile design

---

## 📝 Future Enhancements

- [ ] Add user authentication
- [ ] Implement conversation history persistence
- [ ] Multi-user support with sessions
- [ ] Advanced filters (date range, jurisdiction, court)
- [ ] Export chat transcripts
- [ ] Integration with legal research databases
- [ ] Fine-tuned embeddings model
- [ ] Multi-language support
- [ ] Real-time collaboration features
- [ ] Analytics dashboard for query insights

---

## 📄 License & Data

- **Codebase**: MIT License (or your preferred license)
- **Legal Data**: Caselaw Access Project (free and open)
- **Dataset Size**: 1,671+ U.S. court cases
- **Jurisdictions**: Federal and state courts

---

**Built with**: React, TypeScript, FastAPI, Claude Sonnet 4.5, Pinecone, AWS S3, Azure Kubernetes Service
