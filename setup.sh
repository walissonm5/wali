#!/bin/bash

# --- Configurações Iniciais ---
REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG_FILE="$REPO_DIR/config.ini"
VENV_DIR="$REPO_DIR/.venv"

# Cores para o terminal
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
CYAN="\033[0;36m"
NC="\033[0m" # Sem cor

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[AVISO]${NC} $1"; }
log_error() { echo -e "${RED}[ERRO]${NC} $1"; }

clear
echo -e "${GREEN}  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░${NC}"
echo -e "${GREEN}  ░   INSTALADOR AUTOMÁTICO - PCAPCRACKER PRO v2.3        ░${NC}"
echo -e "${GREEN}  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░${NC}"

# --- Funções de Instalação ---
install_apt_package() {
    PACKAGE=$1
    log_info "Verificando e instalando $PACKAGE..."
    if ! dpkg -s $PACKAGE &> /dev/null; then
        log_info "Atualizando e instalando $PACKAGE via sudo..."
        sudo apt-get update -y && sudo apt-get install -y $PACKAGE
        if [ $? -ne 0 ]; then
            log_error "Falha ao instalar $PACKAGE. Por favor, instale manualmente."
            exit 1
        fi
    else
        log_info "$PACKAGE já está instalado."
    fi
}

# --- Instalação de Dependências do Sistema ---
log_info "Iniciando instalação de dependências do sistema..."
install_apt_package python3-venv
install_apt_package hashcat
install_apt_package hcxtools
install_apt_package tshark
install_apt_package curl

# --- Configuração do Ambiente Virtual ---
log_info "Configurando ambiente virtual em $VENV_DIR..."
if [ -d "$VENV_DIR" ]; then
    log_warn "Ambiente virtual já existe. Recriando para garantir instalação limpa..."
    rm -rf "$VENV_DIR"
fi

python3 -m venv "$VENV_DIR"
if [ $? -ne 0 ]; then
    log_error "Falha ao criar ambiente virtual. Tente instalar python3-venv manualmente."
    exit 1
fi

# Ativar venv para instalar pacotes pip
source "$VENV_DIR/bin/activate"
log_info "Instalando dependências Python no ambiente virtual..."
pip install --upgrade pip
pip install groq colorama tqdm requests
deactivate

# --- Configuração de Diretórios ---
log_info "Configurando diretórios de trabalho..."
mkdir -p "$REPO_DIR/pcap" "$REPO_DIR/wordlist" "$REPO_DIR/hash" "$REPO_DIR/rules" "$REPO_DIR/logs/html" "$REPO_DIR/logs/json"

# --- Configuração da IA ---
echo -e "\n${YELLOW}--- Configuração de IA ---${NC}"
echo -e "Escolha o provedor de IA que deseja usar:"
echo -e "  ${GREEN}[1]${NC} GroqCloud (Nuvem - Grátis e Rápido)"
echo -e "  ${GREEN}[2]${NC} Ollama (Local - Privacidade Total)"
read -p "Opção [1]: " AI_CHOICE
AI_CHOICE=${AI_CHOICE:-1}

PROVIDER="groq"
MODEL="llama-3.3-70b-versatile"
GROQ_KEY=""
OLLAMA_URL="http://localhost:11434/api/generate"

if [ "$AI_CHOICE" == "2" ]; then
    PROVIDER="ollama"
    log_info "Configurando Ollama Local..."
    read -p "Digite o nome do modelo (ex: llama3.1:8b): " MODEL
    MODEL=${MODEL:-"llama3.1:8b"}
    read -p "URL do Ollama [http://localhost:11434/api/generate]: " USER_URL
    OLLAMA_URL=${USER_URL:-$OLLAMA_URL}
else
    PROVIDER="groq"
    echo -e "\n${YELLOW}--- GroqCloud ---${NC}"
    echo -e "Obtenha sua chave em: ${GREEN}https://console.groq.com/keys${NC}"
    read -p "Insira sua GROQ_API_KEY: " GROQ_KEY
    
    AI_MODELS=("llama-3.3-70b-versatile" "llama-3.1-8b-instant" "mixtral-8x7b-32768")
    echo -e "\n${YELLOW}Modelos Groq disponíveis:${NC}"
    for i in "${!AI_MODELS[@]}"; do
        echo -e "  ${GREEN}[$i]${NC} ${AI_MODELS[$i]}"
    done
    read -p "Escolha o número do modelo [0]: " MODEL_IDX
    MODEL_IDX=${MODEL_IDX:-0}
    MODEL="${AI_MODELS[$MODEL_IDX]}"
fi

# Salvar no config.ini
cat << EOF > "$CONFIG_FILE"
[AI]
PROVIDER=$PROVIDER
MODEL=$MODEL
GROQ_API_KEY=$GROQ_KEY
OLLAMA_URL=$OLLAMA_URL
EOF

log_info "Configurações salvas em $CONFIG_FILE"

# --- Finalização ---
log_info "Configuração concluída com sucesso!"
log_info "Para iniciar a ferramenta, use: ${GREEN}./run.sh${NC}"

chmod +x "$REPO_DIR/setup.sh"
chmod +x "$REPO_DIR/run.sh"
