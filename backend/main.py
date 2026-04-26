import os
import uuid
import asyncio
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from models import RepoRequest, ProjectSummary, OnboardingStep, QAResponse
from fetcher import RepoFetcher
from graph_builder import DependencyGraphBuilder
from summarizer import Summarizer, Embedder, QAEngine

sessions = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    for fetcher in [s.get('fetcher') for s in sessions.values() if s.get('fetcher')]:
        fetcher.cleanup()


app = FastAPI(title="CodePilot API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeResponse(BaseModel):
    session_id: str
    summary: ProjectSummary
    graph: dict
    onboarding_steps: list[OnboardingStep]


class QAPrompt(BaseModel):
    session_id: str
    question: str


class AnalysisStatus(BaseModel):
    session_id: str
    status: str
    progress: float
    message: str


@app.get("/")
async def root():
    return {"message": "CodePilot API", "version": "1.0.0"}


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_repo(request: RepoRequest):
    session_id = str(uuid.uuid4())
    
    try:
        fetcher = RepoFetcher()
        local_path, files = await fetcher.fetch_from_github(request.url, request.branch)
        
        graph_builder = DependencyGraphBuilder()
        graph = graph_builder.build(files)
        entry_points = graph_builder.find_entry_files(files)
        
        summarizer = Summarizer()
        summary = await summarizer.summarize_project(files, graph)
        
        onboarding_steps = await summarizer.generate_onboarding_steps(
            files, graph, entry_points
        )
        
        sessions[session_id] = {
            'fetcher': fetcher,
            'files': files,
            'graph': graph,
            'summary': summary,
            'entry_points': entry_points
        }
        
        embedder = Embedder()
        chunks = await embedder.create_embeddings(files)
        sessions[session_id]['chunks'] = chunks
        
        return AnalyzeResponse(
            session_id=session_id,
            summary=summary,
            graph=graph,
            onboarding_steps=onboarding_steps
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/qa", response_model=QAResponse)
async def ask_question(prompt: QAPrompt):
    session = sessions.get(prompt.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    summarizer = Summarizer()
    embedder = Embedder()
    qa_engine = QAEngine(summarizer, embedder)
    
    result = await qa_engine.answer_question(
        prompt.question,
        session['files'],
        session['graph']
    )
    
    return QAResponse(**result)


@app.get("/session/{session_id}")
async def get_session(session_id: str):
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session_id,
        "file_count": len(session['files']),
        "node_count": len(session['graph']['nodes']),
        "edge_count": len(session['graph']['edges'])
    }


@app.delete("/session/{session_id}")
async def delete_session(session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if sessions[session_id].get('fetcher'):
        sessions[session_id]['fetcher'].cleanup()
    
    del sessions[session_id]
    return {"message": "Session deleted"}


@app.get("/files/{session_id}")
async def get_files(session_id: str, limit: int = 50, offset: int = 0):
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    files = session['files']
    return {
        "total": len(files),
        "files": files[offset:offset + limit]
    }


@app.get("/status")
async def health_check():
    return {
        "status": "healthy",
        "sessions": len(sessions),
        "openai_configured": bool(os.getenv('OPENAI_API_KEY'))
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)