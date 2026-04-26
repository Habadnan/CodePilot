import os
import re
from pathlib import Path
from typing import Optional


INCLUDE_EXTENSIONS = {
    '.js', '.jsx', '.ts', '.tsx', '.py', '.java', '.go', '.rs', '.rb',
    '.c', '.cpp', '.h', '.hpp', '.cs', '.php', '.swift', '.kt', '.scala'
}

EXCLUDE_DIRS = {
    'node_modules', '.git', '__pycache__', 'dist', 'build', 'target',
    'vendor', 'bin', 'obj', '.next', '.nuxt', 'coverage', '.venv',
    'venv', 'env', 'android', 'ios', 'Pods', '.gradle'
}

EXCLUDE_FILES = {
    '.DS_Store', 'Thumbs.db', '.gitkeep', '.env.example'
}

MAX_FILE_SIZE = 100_000
MAX_TOTAL_SIZE = 10 * 1024 * 1024


def should_include_file(file_path: str) -> bool:
    path = Path(file_path)
    
    if path.name in EXCLUDE_FILES:
        return False
    
    for exclude_dir in EXCLUDE_DIRS:
        if exclude_dir in path.parts:
            return False
    
    if path.suffix.lower() in EXCLUDE_FILES:
        return False
    
    return path.suffix.lower() in INCLUDE_EXTENSIONS or path.suffix.lower() in {'.json', '.md', '.yaml', '.yml', '.toml', '.xml', '.env'}


def get_language(file_path: str) -> str:
    ext = Path(file_path).suffix.lower()
    lang_map = {
        '.js': 'javascript', '.jsx': 'javascript', '.ts': 'typescript',
        '.tsx': 'typescript', '.py': 'python', '.java': 'java',
        '.go': 'go', '.rs': 'rust', '.rb': 'ruby', '.c': 'c',
        '.cpp': 'cpp', '.h': 'c', '.hpp': 'cpp', '.cs': 'csharp',
        '.php': 'php', '.swift': 'swift', '.kt': 'kotlin',
        '.scala': 'scala', '.json': 'json', '.md': 'markdown',
        '.yaml': 'yaml', '.yml': 'yaml', '.toml': 'toml'
    }
    return lang_map.get(ext, 'unknown')


def normalize_path(path: str) -> str:
    return str(Path(path).as_posix())


def parse_imports_js(content: str) -> list[str]:
    imports = []
    patterns = [
        r'import\s+(?:[\w*{}\s,]+\s+from\s+)?[\'"]([^\'"]+)[\'"]',
        r'require\([\'"]([^\'"]+)[\'"]\)'
    ]
    for pattern in patterns:
        imports.extend(re.findall(pattern, content))
    return list(set(imports))


def parse_imports_python(content: str) -> list[str]:
    imports = []
    patterns = [
        r'^import\s+([\w.]+)',
        r'^from\s+([\w.]+)\s+import'
    ]
    for pattern in patterns:
        imports.extend(re.findall(pattern, content, re.MULTILINE))
    return list(set(imports))


def parse_imports_go(content: str) -> list[str]:
    imports = re.findall(r'import\s+(?:"([^\"]+)"|\(.*?"([^"]+)"\s*\))', content, re.DOTALL)
    return [imp[0] or imp[1] for imp in imports if imp[0] or imp[1]]


def parse_imports(content: str, language: str) -> list[str]:
    parsers = {
        'javascript': parse_imports_js,
        'typescript': parse_imports_js,
        'python': parse_imports_python,
        'go': parse_imports_go
    }
    parser = parsers.get(language, lambda x: [])
    return parser(content)


def extract_functions(content: str, language: str) -> list[dict]:
    functions = []
    
    if language in ('javascript', 'typescript'):
        pattern = r'(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\([^)]*\)'
        functions = [{'name': m, 'type': 'function'} for m in re.findall(pattern, content)]
        
        class_pattern = r'class\s+(\w+)(?:\s+extends\s+\w+)?'
        functions.extend([{'name': m, 'type': 'class'} for m in re.findall(class_pattern, content)])
    
    elif language == 'python':
        pattern = r'def\s+(\w+)\s*\([^)]*\):'
        functions = [{'name': m, 'type': 'function'} for m in re.findall(pattern, content)]
        
        class_pattern = r'class\s+(\w+)(?:\([^)]*\))?:'
        functions.extend([{'name': m, 'type': 'class'} for m in re.findall(class_pattern, content)])
    
    elif language == 'go':
        pattern = r'func\s+(\w+)\s*\([^)]*\)'
        functions = [{'name': m, 'type': 'function'} for m in re.findall(pattern, content)]
        
        type_pattern = r'type\s+(\w+)\s+struct'
        functions.extend([{'name': m, 'type': 'struct'} for m in re.findall(type_pattern, content)])
    
    return functions


def find_entry_points(files: list[str]) -> list[str]:
    priorities = [
        'index.js', 'index.ts', 'main.js', 'main.ts', 'app.js', 'app.ts',
        'server.js', 'server.ts', 'index.py', 'main.py', 'app.py',
        'main.go', 'cmd/server/main.go', 'src/index.js', 'src/main.ts'
    ]
    
    entry_points = []
    for priority in priorities:
        for file in files:
            if file.endswith(priority):
                entry_points.append(file)
    
    return entry_points[:5]


def detect_tech_stack(files: list[str]) -> list[str]:
    tech_stack = set()
    
    for file in files:
        if 'package.json' in file:
            tech_stack.add('Node.js')
        if 'requirements.txt' in file or 'setup.py' in file:
            tech_stack.add('Python')
        if 'go.mod' in file:
            tech_stack.add('Go')
        if 'Cargo.toml' in file:
            tech_stack.add('Rust')
        if 'pom.xml' in file:
            tech_stack.add('Java/Maven')
        if 'build.gradle' in file:
            tech_stack.add('Java/Gradle')
        if 'composer.json' in file:
            tech_stack.add('PHP')
        if '*.csproj' in file:
            tech_stack.add('C#/.NET')
        if 'package.json' in file:
            if 'react' in str(open(file, 'r', errors='ignore').read().lower()):
                tech_stack.add('React')
            if 'next' in str(open(file, 'r', errors='ignore').read().lower()):
                tech_stack.add('Next.js')
        if 'tsconfig.json' in file:
            tech_stack.add('TypeScript')
        if 'webpack' in file:
            tech_stack.add('Webpack')
        if 'dockerfile' in file.lower():
            tech_stack.add('Docker')
        if 'kubernetes' in file.lower() or 'k8s' in file.lower():
            tech_stack.add('Kubernetes')
    
    return list(tech_stack)