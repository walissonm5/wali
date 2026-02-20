#!/bin/bash

# Identity Engine v2.0 - Wrapper Script
# Ativa o ambiente virtual automaticamente e executa o script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Verificar se o venv existe
if [ ! -d "venv" ]; then
    echo "[!] Ambiente virtual não encontrado!"
    echo "[*] Criando ambiente virtual..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -q -r requirements.txt 2>/dev/null || {
        pip install -q requests python-Levenshtein sherlock maigret stem fake-useragent
    }
    echo "[✓] Ambiente virtual criado e configurado!"
fi

# Ativar o ambiente virtual
source venv/bin/activate

# Executar o script com os argumentos passados
python3 identity_engine.py "$@"

# Desativar o venv ao sair
deactivate 2>/dev/null || true
