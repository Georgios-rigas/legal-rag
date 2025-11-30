# Legal RAG Frontend

Modern, professional React frontend for the Legal RAG system.

## Features

- 🎨 Beautiful dark theme UI with Tailwind CSS
- 💬 Real-time chat interface
- 📚 Source citations with relevance scores
- 📱 Responsive design
- ⚡ Built with React + TypeScript + Vite
- 🎯 Fast and optimized

## Setup

### Prerequisites

- Node.js 18+ and npm
- Backend API running on http://localhost:8000

### Installation

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The app will be available at http://localhost:3000

### Build for Production

```bash
npm run build
npm run preview
```

## Technology Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **Axios** - HTTP client
- **React Markdown** - Markdown rendering
- **Lucide React** - Icons

## Project Structure

```
frontend/
├── src/
│   ├── App.tsx          # Main chat component
│   ├── main.tsx         # Entry point
│   ├── index.css        # Global styles
│   └── App.css          # Component styles
├── public/              # Static assets
├── index.html           # HTML template
├── package.json         # Dependencies
├── tsconfig.json        # TypeScript config
├── tailwind.config.js   # Tailwind config
└── vite.config.ts       # Vite config
```

## API Integration

The frontend connects to the FastAPI backend at `http://localhost:8000/api/query`

Request format:
```json
{
  "question": "Your legal question here",
  "top_k": 5
}
```

Response format:
```json
{
  "query": "...",
  "answer": "...",
  "sources": [...],
  "num_sources": 5
}
```
