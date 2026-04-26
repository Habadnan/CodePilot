from typing import Optional
from parsers import parse_imports


class DependencyGraphBuilder:
    def __init__(self):
        self.nodes = {}
        self.edges = []
        self.file_index = {}
    
    def build(self, files: list[dict]) -> dict:
        self.nodes = {}
        self.edges = []
        self.file_index = {}
        
        for i, file_data in enumerate(files):
            path = file_data['path']
            self.nodes[path] = {
                'id': path,
                'data': {
                    'path': path,
                    'language': file_data['language'],
                    'lines': file_data.get('lines', 0),
                    'size': file_data.get('size', 0)
                }
            }
            self.file_index[path] = i
        
        for file_data in files:
            path = file_data['path']
            language = file_data['language']
            content = file_data['content']
            
            imports = parse_imports(content, language)
            
            for imp in imports:
                resolved = self._resolve_import(imp, path, files)
                if resolved and resolved != path:
                    edge = {
                        'source': resolved,
                        'target': path,
                        'type': 'dependency'
                    }
                    if edge not in self.edges:
                        self.edges.append(edge)
        
        return {
            'nodes': list(self.nodes.values()),
            'edges': self.edges
        }
    
    def _resolve_import(self, import_path: str, current_file: str, files: list[dict]) -> Optional[str]:
        import_base = import_path.replace('./', '').replace('../', '').split('/')[0]
        
        if import_base in self.file_index:
            return files[self.file_index[import_base]]['path']
        
        for f in files:
            f_name = f['path'].split('/')[-1].split('.')[0]
            if f_name == import_base or import_base in f['path']:
                return f['path']
        
        return None
    
    def get_file_dependencies(self, file_path: str) -> dict:
        deps = {
            'imports': [],
            'imported_by': []
        }
        
        for edge in self.edges:
            if edge['source'] == file_path:
                deps['imports'].append(edge['target'])
            elif edge['target'] == file_path:
                deps['imported_by'].append(edge['source'])
        
        return deps
    
    def find_entry_files(self, files: list[dict]) -> list[str]:
        entry_priorities = [
            'index.js', 'index.ts', 'main.js', 'main.ts', 'app.js', 'app.ts',
            'server.js', 'server.ts', 'src/index.js', 'src/index.ts',
            'main.py', 'index.py', '__main__.py', 'main.go', 'cmd/server/main.go'
        ]
        
        entry_files = []
        for ep in entry_priorities:
            for f in files:
                if f['path'].endswith(ep):
                    entry_files.append(f['path'])
        
        return entry_files[:5]
    
    def calculate_centrality(self) -> list[dict]:
        centrality = {}
        
        for edge in self.edges:
            target = edge['target']
            centrality[target] = centrality.get(target, 0) + 1
        
        sorted_files = sorted(centrality.items(), key=lambda x: x[1], reverse=True)
        
        return [{'file': f, 'import_count': c} for f, c in sorted_files]