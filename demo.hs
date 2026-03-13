#!/bin/bash
# ZenithFix Quick Demo

echo "🚀 Inicializando ZenithFix Demo..."
echo "-----------------------------------"

# Instalação rápida (opcional se já tiver venv)
# pip install -r requirements.txt

# Executa o auditor no arquivo de testes
python src/zenithfix_cli.py tests/test_sample.py

echo ""
echo "✅ Demo finalizada. Explore os logs acima para ver a detecção de IA."
