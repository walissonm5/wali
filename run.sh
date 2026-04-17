#!/bin/bash

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$REPO_DIR/.venv"
PCAP_CRACKER_PRO_PY="$REPO_DIR/pcapcracker_pro.py"

# Cores para o terminal
GREEN="\033[0;32m"
RED="\033[0;31m"
NC="\033[0m" # Sem cor

log_error() { echo -e "${RED}[ERRO]${NC} $1"; }

# Verificar se o ambiente virtual existe
if [ ! -d "$VENV_DIR" ]; then
    log_error "Ambiente virtual não encontrado em $VENV_DIR. Por favor, execute ./setup.sh primeiro."
    exit 1
fi

# Ativar o ambiente virtual
source "$VENV_DIR/bin/activate"
if [ $? -ne 0 ]; then
    log_error "Falha ao ativar o ambiente virtual. Verifique a instalação."
    exit 1
fi

# Executar o script principal ou teste
if [ "$1" == "test" ]; then
    echo -e "${GREEN}[INFO]${NC} Executando teste da IA..."
    python3 "$REPO_DIR/test_ai.py"
else
    echo -e "${GREEN}[INFO]${NC} Ambiente virtual ativado. Iniciando PCAPCracker Pro..."
    python3 "$PCAP_CRACKER_PRO_PY"
fi

# Desativar o ambiente virtual ao sair
deactivate
