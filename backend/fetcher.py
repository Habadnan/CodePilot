import os
import tempfile
import asyncio
from pathlib import Path
from typing import Optional
import shutil
import httpx

from git import Repo
from parsers import should_include_file, get_language


class RepoFetcher:
    def __init__(self, max_size_mb: int = 10):
        self.max_size = max_size_mb * 1024 * 1024
        self.temp_dir = None
    
    async def fetch_from_github(self, url: str, branch: str = "main") -> tuple[str, list[dict]]:
        if not url.startswith('http'):
            url = f"https://github.com/{url}"
        
        if not url.endswith('.git'):
            url += '.git'
        
        self.temp_dir = tempfile.mkdtemp(prefix="codepilot_")
        local_path = os.path.join(self.temp_dir, "repo")
        
        try:
            Repo.clone_from(url, local_path, branch_name=branch, depth=1)
        except Exception as e:
            try:
                Repo.clone_from(url, local_path, depth=1)
            except:
                raise ValueError(f"Failed to clone repository: {e}")
        
        files = await self._process_files(local_path)
        return local_path, files
    
    async def _process_files(self, repo_path: str) -> list[dict]:
        files = []
        total_size = 0
        
        for root, dirs, filenames in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in {'.git', 'node_modules', '__pycache__', 'venv', '.venv'}]
            
            for filename in filenames:
                file_path = os.path.join(root, filename)
                rel_path = os.path.relpath(file_path, repo_path)
                
                try:
                    file_size = os.path.getsize(file_path)
                    if file_size > 1_000_000:
                        continue
                    total_size += file_size
                    if total_size > self.max_size:
                        break
                except:
                    continue
                
                if should_include_file(rel_path):
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        files.append({
                            'path': rel_path,
                            'content': content,
                            'language': get_language(rel_path),
                            'lines': len(content.splitlines()),
                            'size': file_size
                        })
                    except:
                        continue
        
        return files
    
    async def upload_zip(self, zip_path: str) -> tuple[str, list[dict]]:
        self.temp_dir = tempfile.mkdtemp(prefix="codepilot_")
        extract_path = os.path.join(self.temp_dir, "repo")
        
        shutil.unpack_archive(zip_path, extract_path)
        
        for root, dirs, files in os.walk(extract_path):
            if 'repo' in dirs:
                extract_path = os.path.join(root, 'repo')
                break
        
        files = await self._process_files(extract_path)
        return extract_path, files
    
    def cleanup(self):
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)