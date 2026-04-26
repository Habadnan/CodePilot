# CodePilot

AI-powered codebase onboarding engineer that transforms any repository into an interactive, guided experience.

## Overview

CodePilot acts like a senior engineer walking you through a codebase. Instead of manually digging through unfamiliar repositories, developers can instantly understand architecture, dependencies, and execution flow through intelligent summaries, visual graphs, and step-by-step onboarding guidance.

## Features

- **Repository Ingestion** - Clone GitHub repos or upload ZIP files
- **Codebase Summarization** - AI-generated project overview with tech stack detection
- **Dependency Graph** - Visual mapping of file/module relationships
- **Guided Onboarding** - Step-by-step walkthrough with beginner-friendly explanations
- **Ask the Codebase** - Natural language Q&A with RAG-powered retrieval
- **Interactive Visualization** - Clickable node-based dependency graph

## Tech Stack

### Frontend
- Next.js 14
- TypeScript
- Tailwind CSS
- React Flow (graph visualization)

### Backend
- Python
- FastAPI
- OpenAI GPT-4 (summarization & Q&A)
- GitPython (repo cloning)

## Getting Started

### Prerequisites

- Node.js 18+
- Python 3.10+
- OpenAI API key

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
cp .env.example .env
# Add your OPENAI_API_KEY to .env
uvicorn main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Usage

1. Enter a GitHub repository URL (e.g., `facebook/react` or `https://github.com/facebook/react`)
2. Click "Analyze" to process the repository
3. View the generated summary, dependency graph, and onboarding guide
4. Use "Ask Codebase" to query specific aspects

## Environment Variables

```env
OPENAI_API_KEY=your-api-key-here
LLM_MODEL=gpt-4-turbo-preview
EMBEDDING_MODEL=text-embedding-3-small
```

## API Endpoints

- `POST /analyze` - Analyze a repository
- `POST /qa` - Ask a question about the codebase
- `GET /session/{session_id}` - Get session info
- `GET /files/{session_id}` - List files in session
- `DELETE /session/{session_id}` - Delete session

## License

MIT