import ast
import sys
import importlib

class HallucinationDetector:
    def __init__(self):
        self.issues = []
        self.standard_library = set(sys.stdlib_module_names)
        self.aliases = {}  # Mapeia aliases (pd -> pandas) e caminhos de objetos
        self.high_reputation_libs = {
            'requests', 'pandas', 'numpy', 'openai', 'flask', 
            'django', 'pytest', 'sklearn', 'os', 'json', 'sys', 'datetime'
        }
        # Assinaturas manuais para libs que podem ser difíceis de importar dinamicamente
        self.verified_signatures = {
            'requests': ['get', 'post', 'put', 'delete', 'patch', 'Session', 'exceptions'],
            'os': ['path', 'getcwd', 'listdir', 'mkdir', 'remove', 'environ', 'walk'],
            'json': ['loads', 'dumps', 'load', 'dump', 'JSONEncoder'],
            'openai': ['OpenAI', 'AzureOpenAI', 'ChatCompletion']
        }

    def audit(self, tree):
        self.issues = []
        self.aliases = {}
        # Passo 1: Mapear Imports e Atribuições
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
                # Salva o nome real do módulo para verificação
                self.aliases[alias.asname or alias.name] = actual_mod
        elif isinstance(node, ast.ImportFrom) and node.module:
            for alias in node.names:
                # Caso crítico: from datetime import datetime
                # Mapeia o alias para o caminho completo: "datetime.datetime"
                full_path = f"{node.module}.{alias.name}"
                self.aliases[alias.asname or alias.name] = full_path

    def _track_assignments(self, node):
        """Rastreia se uma variável é instância de uma lib conhecida (ex: df = pd.DataFrame())"""
        if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Attribute):
            if isinstance(node.value.func.value, ast.Name):
                obj_name = node.value.func.value.id
                lib_name = self.aliases.get(obj_name, obj_name)
                # Se a lib está na lista de confiança, rastreamos a variável
                base_lib = lib_name.split('.')[0]
                if base_lib in self.high_reputation_libs:
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            self.aliases[target.id] = lib_name

    def _check_api_hallucinations(self, node):
        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
            obj_name = node.func.value.id
            method_name = node.func.attr
            # Recupera o caminho completo (ex: "datetime.datetime" ou "pandas")
            full_path = self.aliases.get(obj_name, obj_name)
            
            # Pega apenas o primeiro nome para checar se é uma lib conhecida
            base_lib = full_path.split('.')[0]
            
            if base_lib in self.high_reputation_libs or base_lib in self.standard_library:
                if not self._is_method_real(full_path, method_name):
                    self.issues.append({
                        'type': 'Hallucination',
                        'severity': 'HIGH',
                        'message': f"Alucinação Detectada: O método '.{method_name}' não existe em '{full_path}'.",
                        'line': node.lineno
                    })

    def _is_method_real(self, path, method_name):
        """Verifica recursivamente se o método existe no caminho do módulo/classe"""
        try:
            parts = path.split('.')
            # Importa o módulo base (ex: datetime)
            target = importlib.import_module(parts[0])
            
            # Navega pelas sub-partes (ex: .datetime)
            for part in parts[1:]:
                target = getattr(target, part)
            
            # Verifica se o método final existe no alvo
            return hasattr(target, method_name)
        except (ImportError, AttributeError):
            # Fallback para assinaturas manuais caso o import falhe no ambiente
            base_lib = path.split('.')[0]
            return method_name in self.verified_signatures.get(base_lib, [])
            
