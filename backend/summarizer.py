import os
import json
import tiktoken
import numpy as np
from typing import Optional
from openai import OpenAI
from models import FileChunk, OnboardingStep, ProjectSummary

os.environ.setdefault('OPENAI_API_KEY', os.getenv('OPENAI_API_KEY', ''))


class Summarizer:
    def __init__(self, api_key: Optional[str] = None):
        self.client = OpenAI(api_key=api_key or os.getenv('OPENAI_API_KEY'))
        self.model = os.getenv('LLM_MODEL', 'gpt-4-turbo-preview')
        self.embedding_model = os.getenv('EMBEDDING_MODEL', 'text-embedding-3-small')
        try:
            self.enc = tiktoken.get_encoding("cl100k_base")
        except:
            self.enc = None
    
    async def summarize_project(self, files: list[dict], graph: dict) -> ProjectSummary:
        key_files = self._get_key_files(files)
        
        prompt = self._build_summary_prompt(key_files, graph)
        
        if not os.getenv('OPENAI_API_KEY'):
            return self._generate_mock_summary(key_files, graph)
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a senior software engineer explaining a codebase. Provide clear, structured summaries."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        return ProjectSummary(**result)
    
    def _get_key_files(self, files: list[dict], max_chars: int = 50000) -> list[dict]:
        priority_files = []
        other_files = []
        
        priority_names = ['README.md', 'package.json', 'requirements.txt', 'go.mod', 
                         'Cargo.toml', 'pom.xml', 'Makefile', 'Dockerfile']
        
        for f in files:
            name = f['path'].split('/')[-1]
            if name in priority_names:
                priority_files.append(f)
            elif f['language'] in ('javascript', 'typescript', 'python', 'go'):
                other_files.append(f)
        
        priority_files.sort(key=lambda x: len(x['content']))
        
        result = priority_files[:15]
        remaining = max_chars - sum(len(f['content']) for f in result)
        
        for f in other_files:
            if remaining <= 0:
                break
            if len(f['content']) <= remaining:
                result.append(f)
                remaining -= len(f['content'])
        
        return result
    
    def _build_summary_prompt(self, files: list[dict], graph: dict) -> str:
        file_contents = []
        for f in files[:10]:
            file_contents.append(f"=== {f['path']} ===\n{f['content'][:2000]}")
        
        content_str = "\n\n".join(file_contents)
        
        return f"""Analyze this codebase and provide a structured summary in JSON format with:

- name: Project name (from package.json or folder name)
- purpose: 2-3 sentence description of what this project does
- tech_stack: List of technologies detected
- entry_points: Array of main entry files
- modules: Object mapping module names to brief descriptions
- file_count: Total number of files
- total_lines: Total lines of code

File contents:
{content_str}

Dependency graph nodes: {len(graph.get('nodes', []))}
Dependency graph edges: {len(graph.get('edges', []))}

Return only valid JSON, no markdown."""
    
    def _generate_mock_summary(self, files: list[dict], graph: dict) -> ProjectSummary:
        name = "CodePilot Project"
        for f in files:
            if 'package.json' in f['path']:
                name = "Node.js Project"
                break
            elif 'requirements.txt' in f['path']:
                name = "Python Project"
                break
        
        return ProjectSummary(
            name=name,
            purpose="A modern codebase with multiple modules and components",
            tech_stack=["JavaScript", "Node.js"],
            entry_points=[f['path'] for f in files if 'index' in f['path'] or 'main' in f['path']][:3],
            modules={},
            file_count=len(files),
            total_lines=sum(f.get('lines', 0) for f in files)
        )
    
    async def generate_onboarding_steps(self, files: list[dict], graph: dict, 
                                        entry_points: list[str]) -> list[OnboardingStep]:
        if not os.getenv('OPENAI_API_KEY'):
            return self._generate_mock_onboarding(files, entry_points)
        
        prompt = self._build_onboarding_prompt(files, graph, entry_points)
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a senior engineer providing onboarding guidance. Be clear and beginner-friendly."},
                {"role": "user", "content": prompt}
            ]
        )
        
        steps_text = response.choices[0].message.content
        
        return self._parse_onboarding_steps(steps_text, files)
    
    def _build_onboarding_prompt(self, files: list[dict], graph: dict, 
                                entry_points: list[str]) -> str:
        entry_content = []
        for ep in entry_points[:3]:
            for f in files:
                if f['path'] == ep:
                    entry_content.append(f"=== {ep} ===\n{f['content'][:1500]}")
        
        content = "\n\n".join(entry_content) if entry_content else "No entry files found."
        
        return f"""Create a step-by-step onboarding guide for this codebase. Format as numbered steps:

1. [filename] - Brief explanation
2. [filename] - Next step
...

Focus on logical flow from entry point through key modules.

Entry files:
{content}

Return as a simple numbered list: "Step number. filename - explanation"
Make 5-8 steps maximum. Be beginner-friendly."""
    
def _parse_onboarding_steps(self, text: str, files: list[dict], entry_points: list[str] = None) -> list[OnboardingStep]:
        steps = []
        lines = text.strip().split('\n')
        if entry_points is None:
            entry_points = []
        
        for i, line in enumerate(lines[:8], 1):
            line = line.strip()
            if not line:
                continue
            
            parts = line.split(' - ', 1) if ' - ' in line else line.split('. ', 1)
            if len(parts) < 2:
                parts = [f"file_{i}", line]
            
            filename = parts[0].lstrip('0123456789. ').split(' - ')[0].strip()
            
            found_file = None
            for f in files:
                if filename.lower() in f['path'].lower():
                    found_file = f['path']
                    break
            
            if not found_file:
                found_file = filename
            
            steps.append(OnboardingStep(
                step=i,
                file=found_file,
                explanation=parts[1] if len(parts) > 1 else parts[0],
                highlights=[]
            ))
        
        return steps if steps else self._generate_mock_onboarding(files, entry_points)

    def _generate_mock_onboarding(self, files: list[dict], 
                                  entry_points: list[str]) -> list[OnboardingStep]:
        steps = []
        selected = entry_points[:5] if entry_points else [f['path'] for f in files[:5]]
        
        for i, path in enumerate(selected, 1):
            steps.append(OnboardingStep(
                step=i,
                file=path,
                explanation=f"Review {path.split('/')[-1]} to understand core functionality",
                highlights=[]
            ))
        
        return steps


class Embedder:
    def __init__(self, api_key: Optional[str] = None):
        self.client = OpenAI(api_key=api_key or os.getenv('OPENAI_API_KEY'))
        self.embedding_model = os.getenv('EMBEDDING_MODEL', 'text-embedding-3-small')
        self.chunks = []
    
    async def create_embeddings(self, files: list[dict], chunk_size: int = 1000) -> list[FileChunk]:
        self.chunks = []
        
        for file_data in files:
            content = file_data['content']
            path = file_data['path']
            
            if len(content) <= chunk_size:
                embedding = await self._embed(content)
                self.chunks.append(FileChunk(
                    file_path=path,
                    chunk_index=0,
                    content=content[:3000],
                    embedding=embedding
                ))
            else:
                chunk_index = 0
                for i in range(0, len(content), chunk_size):
                    chunk = content[i:i + chunk_size]
                    embedding = await self._embed(chunk)
                    self.chunks.append(FileChunk(
                        file_path=path,
                        chunk_index=chunk_index,
                        content=chunk[:3000],
                        embedding=embedding
                    ))
                    chunk_index += 1
        
        return self.chunks
    
    async def _embed(self, text: str) -> list[float]:
        if not os.getenv('OPENAI_API_KEY'):
            return list(np.random.randn(1536))
        
        response = self.client.embeddings.create(
            model=self.embedding_model,
            input=text[:8000]
        )
        
        return response.data[0].embedding
    
    def find_relevant_chunks(self, query: str, top_k: int = 5) -> list[FileChunk]:
        if not self.chunks:
            return []
        
        return self.chunks[:top_k]


class QAEngine:
    def __init__(self, summarizer: Summarizer, embedder: Embedder):
        self.summarizer = summarizer
        self.embedder = embedder
    
    async def answer_question(self, question: str, files: list[dict], 
                           graph: dict) -> dict:
        if not os.getenv('OPENAI_API_KEY'):
            return {
                'question': question,
                'answer': f"This codebase contains {len(files)} files. The structure includes various modules and components.",
                'relevant_files': [{'path': f['path']} for f in files[:3]],
                'confidence': 0.7
            }
        
        relevant_chunks = self.embedder.find_relevant_chunks(question)
        
        context = "\n\n".join([c.content for c in relevant_chunks])
        
        response = self.summarizer.client.chat.completions.create(
            model=self.summarizer.model,
            messages=[
                {"role": "system", "content": "You are a helpful code assistant. Answer based on the provided codebase context."},
                {"role": "user", "content": f"Question: {question}\n\nContext:\n{context}"}
            ]
        )
        
        return {
            'question': question,
            'answer': response.choices[0].message.content,
            'relevant_files': [{'path': c.file_path} for c in relevant_chunks],
            'confidence': 0.85
        }