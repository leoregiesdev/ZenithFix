import ast

class EfficiencyAuditor:
    def __init__(self):
        self.issues = []
        self.api_trigger_methods = {'chat', 'completions', 'generate', 'post', 'get', 'embed', 'create', 'request'}

    def audit(self, tree):
        self.issues = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.For, ast.While, ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
                self._check_api_calls_in_loop(node)
            if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
                self._check_prompt_concatenation(node)
        return self.issues

    def _check_api_calls_in_loop(self, node):
        for subnode in ast.walk(node):
            if isinstance(subnode, ast.Call):
                name = ""
                if isinstance(subnode.func, ast.Attribute): name = subnode.func.attr
                elif isinstance(subnode.func, ast.Name): name = subnode.func.id

                if name in self.api_trigger_methods:
                    is_comp = isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp))
                    msg = f"Token Bleeding Crítico: Chamada '{name}' em {'loop implícito' if is_comp else 'loop'}."
                    self.issues.append({
                        'type': 'Efficiency',
                        'severity': 'HIGH',
                        'message': f"{msg} Use Batching para economizar custos.",
                        'line': subnode.lineno
                    })

    def _check_prompt_concatenation(self, node):
        if any("prompt" in str(arg).lower() for arg in ast.walk(node)):
            self.issues.append({
                'type': 'Efficiency', 'severity': 'LOW',
                'message': "Concatenação de prompt detectada. Use f-strings para melhor performance.",
                'line': node.lineno
            })
          
