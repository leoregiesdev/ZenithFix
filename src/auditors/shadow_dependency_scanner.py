import ast
import sys

class ShadowDependencyScanner:
    def __init__(self):
        self.issues = []
        self.standard_library = set(sys.stdlib_module_names)
        self.high_reputation_libraries = {
            'requests', 'pandas', 'numpy', 'openai', 'flask', 
            'django', 'fastapi', 'pydantic', 'sqlalchemy', 'boto3'
        }

    def audit(self, tree):
        self.issues = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                self._check_dependency_reputation(node)
        return self.issues

    def _check_dependency_reputation(self, node):
        modules = []
        if isinstance(node, ast.Import):
            modules = [alias.name.split('.')[0] for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            if node.level > 0 or not node.module: return
            modules = [node.module.split('.')[0]]

        for mod in modules:
            if mod not in self.standard_library and mod not in self.high_reputation_libraries:
                self.issues.append({
                    'type': 'Security',
                    'severity': 'HIGH',
                    'message': f"Shadow Dependency: '{mod}' não é uma biblioteca reconhecida. Risco de Supply Chain.",
                    'line': node.lineno
                })
