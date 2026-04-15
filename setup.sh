#!/bin/bash

# --- Configurações Iniciais ---
REPO_DIR="$(dirname "$0")"
PCAP_CRACKER_PRO_PY="$REPO_DIR/pcapcracker_pro.py"
CONFIG_FILE="$REPO_DIR/config.ini"
VENV_DIR="$REPO_DIR/.venv"

# Cores para o terminal (corrigido o escape)
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
        sudo apt-get update -y
        sudo apt-get install -y $PACKAGE
        if [ $? -ne 0 ]; then
            log_error "Falha ao instalar $PACKAGE. Por favor, instale manualmente ou verifique os repositórios."
            exit 1
        fi
    else
        log_info "$PACKAGE já está instalado."
    fi
}

install_pip_package() {
    PACKAGE=$1
    log_info "Verificando e instalando $PACKAGE (pip) no ambiente virtual..."
    # Ativa o venv temporariamente para instalar
    source "$VENV_DIR/bin/activate"
    pip install $PACKAGE
    if [ $? -ne 0 ]; then
        log_error "Falha ao instalar $PACKAGE via pip. Por favor, instale manualmente."
        deactivate # Desativa o venv em caso de erro
        exit 1
    fi
    deactivate # Desativa o venv após a instalação
    log_info "$PACKAGE instalado no ambiente virtual."
}

# --- Instalação de Dependências do Sistema ---
log_info "Iniciando instalação de dependências do sistema..."
install_apt_package python3-venv # Para criar ambientes virtuais
install_apt_package hashcat
install_apt_package hcxdumptool

# hcxpcapngtool pode ter nome diferente ou ser parte de hcxdumptool em algumas distros
log_info "Tentando instalar hcxpcapngtool..."
if ! dpkg -s hcxpcapngtool &> /dev/null; then
    sudo apt-get install -y hcxpcapngtool
    if [ $? -ne 0 ]; then
        log_warn "hcxpcapngtool não encontrado ou falha na instalação via apt. Pode ser parte de hcxdumptool ou requerer instalação manual."
        log_warn "Verifique se 'hcxpcapngtool' está disponível em seus repositórios ou instale-o manualmente se necessário."
    else
        log_info "hcxpcapngtool instalado."
    fi
else
    log_info "hcxpcapngtool já está instalado."
fi

install_apt_package tshark # Para conversão de .scap

# --- Configuração do Ambiente Virtual ---
log_info "Criando e ativando ambiente virtual Python..."
python3 -m venv "$VENV_DIR"
if [ $? -ne 0 ]; then
    log_error "Falha ao criar o ambiente virtual. Certifique-se de que 'python3-venv' esteja instalado."
    exit 1
fi
source "$VENV_DIR/bin/activate"
log_info "Ambiente virtual ativado: $VENV_DIR"

# --- Instalação de Dependências Python no Ambiente Virtual ---
log_info "Iniciando instalação de dependências Python no ambiente virtual..."
pip install --upgrade pip
install_pip_package openai
install_pip_package colorama
install_pip_package tqdm

# --- Configuração de Diretórios ---
log_info "Configurando diretórios necessários..."
mkdir -p "$REPO_DIR/pcap"
mkdir -p "$REPO_DIR/wordlist"
mkdir -p "$REPO_DIR/hash"
mkdir -p "$REPO_DIR/rules"
mkdir -p "$REPO_DIR/logs/html"
mkdir -p "$REPO_DIR/logs/json"

# --- Configuração da API Key da OpenAI ---
log_info "Configurando a chave da API OpenAI..."
read -p "${YELLOW}Por favor, insira sua chave da API OpenAI (OPENAI_API_KEY): ${NC}" OPENAI_API_KEY_INPUT
export OPENAI_API_KEY="$OPENAI_API_KEY_INPUT"

# Salvar a chave da API em um arquivo de configuração para persistência
# (Opcional, pode ser configurado como variável de ambiente no .bashrc/.zshrc)
# echo "OPENAI_API_KEY=\"$OPENAI_API_KEY_INPUT\"" > "$REPO_DIR/.env"
# log_info "Chave da API salva em $REPO_DIR/.env"

# --- Seleção do Modelo de IA ---
log_info "Selecionando o modelo de IA..."
AI_MODELS=("gpt-4.1-mini" "gemini-2.5-flash" "gpt-3.5-turbo")

echo -e "${YELLOW}Modelos de IA disponíveis:${NC}"
for i in "${!AI_MODELS[@]}"; do
    echo -e "  ${GREEN}[$i]${NC} ${AI_MODELS[$i]}"
done

SELECTED_MODEL_INDEX=""
while ! [[ "$SELECTED_MODEL_INDEX" =~ ^[0-9]+$ ]] || ! (( SELECTED_MODEL_INDEX >= 0 && SELECTED_MODEL_INDEX < ${#AI_MODELS[@]} )); do
    read -p "${YELLOW}Escolha o número do modelo de IA a ser usado (ex: 0 para gpt-4.1-mini): ${NC}" SELECTED_MODEL_INDEX
done

SELECTED_AI_MODEL="${AI_MODELS[$SELECTED_MODEL_INDEX]}"
log_info "Modelo de IA selecionado: ${SELECTED_AI_MODEL}"

# Salvar o modelo de IA selecionado em um arquivo de configuração
cat << EOF > "$CONFIG_FILE"
[AI]
MODEL=$SELECTED_AI_MODEL
EOF
log_info "Modelo de IA salvo em $CONFIG_FILE"

# --- Finalização ---
deactivate # Desativa o ambiente virtual após a configuração
log_info "Configuração concluída!"
log_info "Para executar o PCAPCracker Pro, use o script 'run.sh':"
log_info "  chmod +x run.sh"
log_info "  ./run.sh"
log_info "Certifique-se de que a variável de ambiente OPENAI_API_KEY esteja definida antes de executar."

chmod +x "$REPO_DIR/setup.sh"
