import ast
import sys
import importlib

class HallucinationDetector:
    def __init__(self):
        self.issues = []
        self.standard_library = set(sys.stdlib_module_names)
        self.aliases = {} # Mapeia aliases (pd -> pandas) e instâncias (df -> pandas)
        self.high_reputation_libs = {
            'requests', 'pandas', 'numpy', 'openai', 'flask', 
            'django', 'pytest', 'sklearn', 'os', 'json', 'sys'
        }
        self.verified_signatures = {
            'requests': ['get', 'post', 'put', 'delete', 'patch', 'Session', 'exceptions'],
            'os': ['path', 'getcwd', 'listdir', 'mkdir', 'remove', 'environ', 'walk'],
            'json': ['loads', 'dumps', 'load', 'dump', 'JSONEncoder'],
            'openai': ['OpenAI', 'AzureOpenAI', 'ChatCompletion']
        }

    def audit(self, tree):
        self.issues = []
        self.aliases = {}
        # Passo 1: Mapear Imports e Atribuições de variáveis
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                self._register_imports(node)
            if isinstance(node, ast.Assign):
                self._track_assignments(node)
        
        # Passo 2: Validar Chamadas
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                self._check_api_hallucinations(node)
        return self.issues

    def _register_imports(self, node):
        if isinstance(node, ast.Import):
            for alias in node.names:
                actual_mod = alias.name.split('.')[0]
                self.aliases[alias.asname or alias.name] = actual_mod
        elif isinstance(node, ast.ImportFrom) and node.module:
            actual_mod = node.module.split('.')[0]
            self.aliases[node.module] = actual_mod

    def _track_assignments(self, node):
        """Rastreia se uma variável é instância de uma lib conhecida (ex: df = pd.DataFrame())"""
        if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Attribute):
            if isinstance(node.value.func.value, ast.Name):
                obj_name = node.value.func.value.id
                lib_name = self.aliases.get(obj_name, obj_name)
                if lib_name in self.high_reputation_libs:
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            self.aliases[target.id] = lib_name

    def _check_api_hallucinations(self, node):
        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
            obj_name = node.func.value.id
            method_name = node.func.attr
            lib_name = self.aliases.get(obj_name, obj_name)
            
            if lib_name in self.high_reputation_libs or lib_name in self.standard_library:
                if not self._is_method_real(lib_name, method_name):
                    self.issues.append({
                        'type': 'Hallucination',
                        'severity': 'HIGH',
                        'message': f"Alucinação Detectada: O método '.{method_name}' não existe na biblioteca '{lib_name}'.",
                        'line': node.lineno
                    })

    def _is_method_real(self, lib_name, method_name):
        try:
            module = importlib.import_module(lib_name)
            return hasattr(module, method_name)
        except:
            return method_name in self.verified_signatures.get(lib_name, [])
