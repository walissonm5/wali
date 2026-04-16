#!/bin/bash

# --- Configurações Iniciais ---
REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG_FILE="$REPO_DIR/config.ini"
VENV_DIR="$REPO_DIR/.venv"

# Cores para o terminal
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
NC="\033[0m" # No Color

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

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
# No Parrot/Kali, esses pacotes costumam estar presentes, mas vamos garantir.
install_apt_package python3-venv
install_apt_package hashcat
install_apt_package hcxdumptool
install_apt_package tshark

# --- Configuração do Ambiente Virtual ---
log_info "Criando ambiente virtual em $VENV_DIR..."
if [ -d "$VENV_DIR" ]; then
    log_warn "Ambiente virtual já existe. Removendo para reinstalação limpa..."
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
pip install groq colorama tqdm
deactivate

# --- Configuração de Diretórios ---
log_info "Configurando diretórios de trabalho..."
mkdir -p "$REPO_DIR/pcap" "$REPO_DIR/wordlist" "$REPO_DIR/hash" "$REPO_DIR/rules" "$REPO_DIR/logs/html" "$REPO_DIR/logs/json"

# --- Configuração da API GroqCloud ---
echo -e "\n${YELLOW}--- Configuração da API GroqCloud (Grátis) ---${NC}"
echo -e "Obtenha sua chave em: ${GREEN}https://console.groq.com/keys${NC}"
read -p "Insira sua GROQ_API_KEY: " GROQ_KEY_INPUT

if [ -z "$GROQ_KEY_INPUT" ]; then
    log_error "A chave da API não pode estar vazia."
    exit 1
fi

# Seleção do Modelo
AI_MODELS=("llama-3.3-70b-versatile" "llama-3.1-8b-instant" "mixtral-8x7b-32768")
echo -e "\n${YELLOW}Modelos Groq disponíveis:${NC}"
for i in "${!AI_MODELS[@]}"; do
    echo -e "  ${GREEN}[$i]${NC} ${AI_MODELS[$i]}"
done

read -p "Escolha o número do modelo [0]: " MODEL_IDX
MODEL_IDX=${MODEL_IDX:-0}
SELECTED_MODEL="${AI_MODELS[$MODEL_IDX]}"

# Salvar no config.ini
cat << EOF > "$CONFIG_FILE"
[AI]
GROQ_API_KEY=$GROQ_KEY_INPUT
MODEL=$SELECTED_MODEL
EOF

log_info "Configurações salvas em $CONFIG_FILE"

# --- Finalização ---
log_info "Configuração concluída com sucesso!"
log_info "Para iniciar a ferramenta, use: ${GREEN}./run.sh${NC}"

chmod +x "$REPO_DIR/setup.sh"
