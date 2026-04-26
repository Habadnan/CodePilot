from pydantic import BaseModel
from typing import Optional


class RepoRequest(BaseModel):
    url: str
    branch: Optional[str] = "main"


class FileNode(BaseModel):
    path: str
    content: str
    language: str
    lines: int


class DependencyEdge(BaseModel):
    source: str
    target: str
    type: str


class DependencyGraph(BaseModel):
    nodes: list[dict]
    edges: list[DependencyEdge]


class FileChunk(BaseModel):
    file_path: str
    chunk_index: int
    content: str
    embedding: Optional[list[float]] = None


class OnboardingStep(BaseModel):
    step: int
    file: str
    explanation: str
    highlights: list[str]


class ProjectSummary(BaseModel):
    name: str
    purpose: str
    tech_stack: list[str]
    entry_points: list[str]
    modules: dict[str, str]
    file_count: int
    total_lines: int


class QAResponse(BaseModel):
    question: str
    answer: str
    relevant_files: list[dict]
    confidence: float