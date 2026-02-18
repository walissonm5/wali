#!/bin/bash

# Cores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}[*] Iniciando configuração do ambiente Identity Engine...${NC}"

# 1. Verificar dependências do sistema
echo -e "[*] Verificando dependências do sistema..."
sudo apt-get update -y && sudo apt-get install -y tor curl python3-venv python3-pip

# 2. Configurar o Tor para permitir controle (necessário para renovar IP)
echo -e "[*] Configurando Tor Control Port..."
if ! grep -q "ControlPort 9051" /etc/tor/torrc; then
    echo "ControlPort 9051" | sudo tee -a /etc/tor/torrc
    echo "CookieAuthentication 0" | sudo tee -a /etc/tor/torrc
    sudo systemctl restart tor
fi

# 3. Criar ambiente virtual
echo -e "[*] Criando ambiente virtual Python (venv)..."
python3 -m venv venv
source venv/bin/activate

# 4. Instalar dependências Python
echo -e "[*] Instalando dependências do projeto..."
pip install --upgrade pip
pip install requests python-Levenshtein sherlock maigret stem fake-useragent

# 5. Criar estrutura de pastas
mkdir -p relatorio
mkdir -p config

# 6. Criar arquivo de exemplo de proxies
if [ ! -f config/proxies.txt ]; then
    echo "# Adicione seus proxies aqui (um por linha)" > config/proxies.txt
    echo "# Formato: http://user:pass@ip:port ou socks5://ip:port" >> config/proxies.txt
fi

echo -e "${GREEN}[✓] Configuração concluída!${NC}"
echo -e "[*] Para usar o script, ative o ambiente: ${GREEN}source venv/bin/activate${NC}"
