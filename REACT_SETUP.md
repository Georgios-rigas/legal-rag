# React + FastAPI Setup Guide

Complete guide to run your professional Legal RAG application.

## Architecture

```
┌─────────────────┐      HTTP/REST      ┌──────────────────┐
│  React Frontend │ ◄─────────────────► │  FastAPI Backend │
│  (Port 3000)    │                     │  (Port 8000)     │
└─────────────────┘                     └──────────────────┘
                                                 │
                                                 ▼
                                        ┌────────────────┐
                                        │  Pinecone DB   │
                                        │  Claude API    │
                                        │  Local Models  │
                                        └────────────────┘
```

## Prerequisites

1. **Python 3.12+** with venv activated
2. **Node.js 18+** and npm ([Download](https://nodejs.org/))
3. **Backend setup complete** (Pinecone indexed, .env configured)

## Step 1: Start the Backend API

Open a terminal (PowerShell):

```powershell
# Navigate to project
cd c:\Users\GeorgiosRigas\Downloads\legal_rag

# Activate virtual environment
.\venv\Scripts\activate

# Set UTF-8 encoding
$env:PYTHONIOENCODING="utf-8"

# Start FastAPI server
python api.py
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
🚀 Initializing Legal RAG system...
✅ Using local embeddings (all-MiniLM-L6-v2)
✅ Using Claude (claude-sonnet-4-5-20250929) for generation
✅ Legal RAG initialized with 1671 parent cases
✅ Legal RAG API ready!
```

**Keep this terminal running!**

## Step 2: Install Frontend Dependencies

Open a **NEW** terminal (PowerShell):

```powershell
# Navigate to frontend
cd c:\Users\GeorgiosRigas\Downloads\legal_rag\frontend

# Install dependencies (this will take a few minutes)
npm install
```

## Step 3: Start the React Frontend

In the same frontend terminal:

```powershell
# Start development server
npm run dev
```

You should see:
```
  VITE v5.2.11  ready in 500 ms

  ➜  Local:   http://localhost:3000/
  ➜  press h + enter to show help
```

## Step 4: Open the Application

Open your browser and go to:
```
http://localhost:3000
```

## What You'll See

### Welcome Screen
- Legal RAG branding with scale icon
- Example questions to get started
- Clean, professional dark theme

### Chat Interface
- Send legal questions
- Get AI-powered answers from Claude
- See source citations with relevance scores
- Beautiful markdown formatting

## Testing the Application

Try these example queries:

1. **"Can a landlord waive a lease covenant by accepting rent?"**
   - Should return detailed analysis with case citations

2. **"What is required to prove criminal intent?"**
   - Should cite relevant criminal law cases

3. **"What are the requirements for a broker to earn commission?"**
   - Should reference real estate and contract law cases

## Troubleshooting

### Backend Issues

**"ModuleNotFoundError: No module named 'fastapi'"**
```powershell
.\venv\Scripts\activate
python -m pip install fastapi uvicorn python-multipart
```

**"RAG system not initialized"**
- Check that your `.env` file has correct API keys
- Verify Pinecone index exists with `python embed_and_index.py`

**Port 8000 already in use**
```powershell
# Find and kill process using port 8000
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Frontend Issues

**"npm: command not found"**
- Install Node.js from https://nodejs.org/

**"CORS error in browser"**
- Make sure backend is running on port 8000
- Check that `api.py` has CORS middleware configured

**Port 3000 already in use**
- Frontend will automatically use port 3001
- Or kill the process:
```powershell
netstat -ano | findstr :3000
taskkill /PID <PID> /F
```

**Build errors**
```powershell
# Clear cache and reinstall
rm -r node_modules package-lock.json
npm install
```

## Development Workflow

### Making Changes

**Backend Changes (api.py, query_rag.py)**
- FastAPI auto-reloads on changes
- No need to restart server

**Frontend Changes (src/*.tsx)**
- Vite hot-reloads automatically
- Changes appear instantly in browser

### Production Build

```powershell
# Build frontend for production
cd frontend
npm run build

# Output will be in frontend/dist/
# Serve with: npm run preview
```

## Project Structure

```
legal_rag/
├── api.py                    # FastAPI backend
├── query_rag.py             # RAG logic
├── config.py                # Configuration
├── .env                     # API keys
├── frontend/
│   ├── src/
│   │   ├── App.tsx         # Main React component
│   │   ├── main.tsx        # Entry point
│   │   └── index.css       # Styles
│   ├── package.json        # Node dependencies
│   └── vite.config.ts      # Build config
└── chunked_output/         # Processed data
    ├── parents.json
    └── children.json
```

## API Endpoints

### GET /
Health check
```bash
curl http://localhost:8000/
```

### GET /health
Detailed health status
```bash
curl http://localhost:8000/health
```

### POST /api/query
Query the RAG system
```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Can a landlord waive a lease covenant by accepting rent?"}'
```

### GET /api/stats
System statistics
```bash
curl http://localhost:8000/api/stats
```

## Features

### Frontend Features
✅ Real-time chat interface
✅ Markdown rendering for answers
✅ Source citations with relevance scores
✅ Example questions
✅ Error handling
✅ Loading states
✅ Responsive design
✅ Dark theme
✅ Smooth animations

### Backend Features
✅ RESTful API
✅ CORS support
✅ Request validation
✅ Error handling
✅ Auto-reload in development
✅ OpenAPI documentation (http://localhost:8000/docs)

## Next Steps

1. **Customize the UI**: Edit `frontend/src/App.tsx`
2. **Add features**: User authentication, chat history, export to PDF
3. **Deploy**: Use Vercel (frontend) + Railway/Render (backend)
4. **Optimize**: Add caching, rate limiting, analytics

## Technology Stack

### Frontend
- React 18 + TypeScript
- Vite (build tool)
- Tailwind CSS (styling)
- Axios (HTTP client)
- React Markdown
- Lucide React (icons)

### Backend
- FastAPI (Python web framework)
- Uvicorn (ASGI server)
- Pydantic (validation)
- Claude Sonnet 4.5 (LLM)
- Pinecone (vector DB)
- Sentence Transformers (embeddings)

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review backend logs in the API terminal
3. Check browser console for frontend errors
4. Verify all environment variables are set

---

**Your professional Legal RAG application is ready!** 🎉
