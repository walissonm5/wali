#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e
# Print commands and their arguments as they are executed.
set -x

REPO_DIR="$(dirname "$0")"
VENV_DIR="$REPO_DIR/.venv"
PCAP_CRACKER_PRO_PY="$REPO_DIR/pcapcracker_pro.py"

# Cores para o terminal
GREEN="\033[0;32m"
RED="\033[0;31m"
NC="\033[0m" # No Color

log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

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

echo -e "${GREEN}[INFO]${NC} Ambiente virtual ativado. Executando PCAPCracker Pro..."

# Executar o script principal
python3 "$PCAP_CRACKER_PRO_PY"

# Desativar o ambiente virtual ao sair
deactivate

echo -e "${GREEN}[INFO]${NC} PCAPCracker Pro finalizado. Ambiente virtual desativado."
