import argparse, ast, sys, os, json
from auditors.efficiency_auditor import EfficiencyAuditor
from auditors.hallucination_detector import HallucinationDetector
from auditors.shadow_dependency_scanner import ShadowDependencyScanner

class Colors:
    HEADER, BLUE, GREEN, YELLOW, RED, ENDC, BOLD = '\033[95m', '\033[94m', '\033[92m', '\033[93m', '\033[91m', '\033[0m', '\033[1m'

def get_local_modules(path):
    base = path if os.path.isdir(path) else os.path.dirname(path)
    try: return {d for d in os.listdir(base or '.') if os.path.isdir(os.path.join(base or '.', d))}
    except: return set()

def main():
    parser = argparse.ArgumentParser(description="ZenithFix: AI-Code Shield")
    parser.add_argument('path', help="Caminho para auditar")
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()

    local_mods = get_local_modules(args.path)
    eff_auditor = EfficiencyAuditor()
    hal_auditor = HallucinationDetector()
    sha_auditor = ShadowDependencyScanner()

    # Atualiza whitelists com pastas locais
    hal_auditor.high_reputation_libs.update(local_mods)
    sha_auditor.high_reputation_libraries.update(local_mods)

    auditors = [eff_auditor, hal_auditor, sha_auditor]
    results = {}

    target = os.path.abspath(args.path)
    if os.path.isfile(target):
        results[args.path] = audit_file(target, auditors)
    else:
        for root, _, files in os.walk(target):
            for f in files:
                if f.endswith('.py'):
                    full = os.path.join(root, f)
                    results[os.path.relpath(full, os.getcwd())] = audit_file(full, auditors)
    
    if args.json: print(json.dumps(results, indent=4))
    else: display_report(results)

def audit_file(file_path, auditors):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())
        issues = []
        for a in auditors: issues.extend(a.audit(tree))
        unique = {f"{i['line']}_{i['type']}": i for i in issues}.values()
        return sorted(list(unique), key=lambda x: x['line'])
    except Exception as e: return [{'type': 'Error', 'message': str(e), 'line': 0}]

def display_report(results):
    total = 0
    print(f"\n{Colors.BOLD}{Colors.HEADER}🔍 ZENITHFIX v1.0{Colors.ENDC}\n")
    for file, issues in results.items():
        print(f"{Colors.BLUE}📄 {file}{Colors.ENDC}")
        if not issues: print(f"  {Colors.GREEN}✅ Código íntegro.{Colors.ENDC}")
        else:
            for i in issues:
                total += 1
                color = Colors.RED if i.get('severity') == 'HIGH' else Colors.YELLOW
                icon = "🚨" if i.get('severity') == 'HIGH' else "💡"
                print(f"  {color}{icon} [{i['type']}] Linha {i['line']}:{Colors.ENDC} {i['message']}")
        print("-" * 50)
    print(f"\n{Colors.BOLD}RESUMO: {total} alertas encontrados.{Colors.ENDC}")

if __name__ == "__main__": main()
