#!/bin/bash

# ================================================================
#   Log Analyzer & Reporter - VulnScan PRO Complementary Script
#   Analisa os logs gerados pelo VulnScan PRO e gera relatórios resumidos.
# ================================================================

# ── CORES ────────────────────────────────────────────────────────
RED=\'\\033[0;31m\
LRED=\'\\033[1;31m\
GREEN=\'\\033[0;32m\
LGREEN=\'\\033[1;32m\
YELLOW=\'\\033[1;33m\
LYELLOW=\'\\033[0;33m\
CYAN=\'\\033[0;36m\
LCYAN=\'\\033[1;36m\
BLUE=\'\\033[0;34m\
LBLUE=\'\\033[1;34m\
MAGENTA=\'\\033[0;35m\
LMAGENTA=\'\\033[1;35m\
WHITE=\'\\033[1;37m\
GRAY=\'\\033[0;37m\
DGRAY=\'\\033[1;30m\
BOLD=\'\\033[1m\
RESET=\'\\033[0m\

# ── DIRS & GLOBALS ───────────────────────────────────────────────
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOGS_DIR="$BASE_DIR/logs"
REPORTS_DIR="$BASE_DIR/relatorios"

# ── LOGGING (simplified for this script) ─────────────────────────
log() {
    local level="$1"; shift
    local msg="$*"
    case "$level" in
        INFO)   echo -e "  ${CYAN}[INFO]${RESET}    $msg" ;;
        OK)     echo -e "  ${GREEN}[OK]${RESET}      $msg" ;;
        WARN)   echo -e "  ${YELLOW}[WARN]${RESET}    $msg" ;;
        ERROR)  echo -e "  ${RED}[ERROR]${RESET}   $msg" ;;
        STEP)   echo -e "  ${LBLUE}[STEP]${RESET}    $msg" ;;
        *)
            echo -e "  ${GRAY}[$level]${RESET}    $msg" ;;
    esac
}

div() { echo -e "  ${DGRAY}$(printf \'%.0s─\' {1..72})${RESET}"; }

# ── FUNCTIONS ────────────────────────────────────────────────────
list_logs() {
    log STEP "Listando arquivos de log disponíveis em $LOGS_DIR..."
    div
    if ls "$LOGS_DIR"/*.log &>/dev/null; then
        echo -e "  ${BOLD}Data       Hora     Tamanho  Nome do Arquivo${RESET}"
        ls -lh "$LOGS_DIR"/*.log | awk 
            -v bold="${BOLD}" -v reset="${RESET}" \
            'BEGIN { printf("  %s%-10s %-8s %-8s %s%s\\n", bold, "Data", "Hora", "Tamanho", "Nome do Arquivo", reset) } \
            { printf("  %-10s %-8s %-8s %s\\n", $6" "$7, $8, $5, $9) }'
    else
        log WARN "Nenhum arquivo de log encontrado."
    fi
    div
}

view_log() {
    echo -ne "  ${YELLOW}▶ Digite o nome completo do arquivo de log para visualizar (ex: vulnscan_20231027_103000.log):${RESET} "
    read -r LOG_FILE_NAME
    local FULL_PATH="$LOGS_DIR/$LOG_FILE_NAME"

    if [ -f "$FULL_PATH" ]; then
        log INFO "Visualizando log: $LOG_FILE_NAME"
        div
        cat "$FULL_PATH"
        div
    else
        log ERROR "Arquivo de log não encontrado: $LOG_FILE_NAME"
    fi
}

analyze_log() {
    echo -ne "  ${YELLOW}▶ Digite o nome completo do arquivo de log para analisar:${RESET} "
    read -r LOG_FILE_NAME
    local FULL_PATH="$LOGS_DIR/$LOG_FILE_NAME"

    if [ ! -f "$FULL_PATH" ]; then
        log ERROR "Arquivo de log não encontrado: $LOG_FILE_NAME"
        return 1
    fi

    log STEP "Analisando log: $LOG_FILE_NAME"
    div

    local TOTAL_VULNS=0
    local CRITICAL_VULNS=0
    local HIGH_VULNS=0
    local MEDIUM_VULNS=0
    local LOW_VULNS=0
    declare -A VULN_SUMMARY

    while IFS= read -r line; do
        if echo "$line" | grep -q "\[VULN\]\|\[CRITICAL\]\|\[HIGH\]\|\[MEDIUM\]\|\[LOW\]"; then
            TOTAL_VULNS=$((TOTAL_VULNS+1))
            local vuln_info=$(echo "$line" | sed -E \'s/.*(\[(CRIT|HIGH|MED|LOW|VULN)\])\s*(.*)/\\3/
\')
            local severity=$(echo "$line" | sed -E \'s/.*\[(CRIT|HIGH|MED|LOW|VULN)\].*/\\1/
\')
            local ip=$(echo "$vuln_info" | grep -oE \'[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\' | head -1)
            local desc=$(echo "$vuln_info" | sed -E \'s/[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3} - //\')

            case "$severity" in
                CRIT) CRITICAL_VULNS=$((CRITICAL_VULNS+1)); VULN_SUMMARY["$ip"]+="${LRED}CRITICAL: ${RESET}$desc\n" ;;
                HIGH) HIGH_VULNS=$((HIGH_VULNS+1)); VULN_SUMMARY["$ip"]+="${RED}HIGH: ${RESET}$desc\n" ;;
                MED) MEDIUM_VULNS=$((MEDIUM_VULNS+1)); VULN_SUMMARY["$ip"]+="${YELLOW}MEDIUM: ${RESET}$desc\n" ;;
                LOW) LOW_VULNS=$((LOW_VULNS+1)); VULN_SUMMARY["$ip"]+="${GRAY}LOW: ${RESET}$desc\n" ;;
                VULN) VULN_SUMMARY["$ip"]+="${LRED}VULN: ${RESET}$desc\n" ;;
            esac
        fi
    done < "$FULL_PATH"

    echo -e "  ${BOLD}${WHITE}  RESUMO DA ANÁLISE DE LOG${RESET}"
    echo -e "  ${DGRAY}$(printf \'%.0s═\' {1..72})${RESET}"
    echo -e "  ${LRED}  ● CRÍTICO  : $CRITICAL_VULNS${RESET}"
    echo -e "  ${RED}  ● ALTO     : $HIGH_VULNS${RESET}"
    echo -e "  ${YELLOW}  ● MÉDIO    : $MEDIUM_VULNS${RESET}"
    echo -e "  ${GRAY}  ● BAIXO    : $LOW_VULNS${RESET}"
    echo -e "  ${CYAN}  ● Total Vulnerabilidades: $TOTAL_VULNS${RESET}"
    echo -e "  ${DGRAY}$(printf \'%.0s═\' {1..72})${RESET}"
    echo ""

    if [ "$TOTAL_VULNS" -gt 0 ]; then
        echo -e "  ${BOLD}${WHITE}  DETALHES POR HOST/IP${RESET}"
        for ip in "${!VULN_SUMMARY[@]}"; do
            echo -e "  ${LCYAN}┌── IP: $ip ──${RESET}"
            echo -e "${VULN_SUMMARY["$ip"]}"
            echo -e "  ${LCYAN}└──${RESET}"
            echo ""
        done
    else
        log OK "Nenhuma vulnerabilidade detectada neste log."
    fi
    div
}

# ── MAIN MENU ────────────────────────────────────────────────────
main_menu() {
    while true; do
        clear
        echo -e "${LRED}"
        echo "  ██╗   ██╗██╗   ██╗██╗     ███╗   ██╗███████╗ ██████╗ █████╗ ███╗  ██╗"
        echo "  ██║   ██║██║   ██║██║     ████╗  ██║██╔════╝██╔════╝██╔══██╗████╗ ██║"
        echo "  ██║   ██║██║   ██║██║     ██╔██╗ ██║███████╗██║     ███████║██╔██╗██║"
        echo "  ╚██╗ ██╔╝██║   ██║██║     ██║╚██╗██║╚════██║██║     ██╔══██║██║╚████║"
        echo "   ╚████╔╝ ╚██████╔╝███████╗██║ ╚████║███████║╚██████╗██║  ██║██║ ╚███║"
        echo "    ╚═══╝   ╚═════╝ ╚══════╝╚═╝  ╚═══╝╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚══╝"
        echo -e "${RESET}"
        echo -e "  ${DGRAY}$(printf \'%.0s═\' {1..73})${RESET}"
        echo -e "  ${RED}Log Analyzer & Reporter${RESET}  ${DGRAY}│${RESET}  ${YELLOW}Análise de logs do VulnScan PRO${RESET}"
        echo -e "  ${DGRAY}$(printf \'%.0s═\' {1..73})${RESET}"
        echo ""

        echo -e "  ${BOLD}${WHITE}┌──────────────── MENU DE ANÁLISE DE LOGS ────────────────┐${RESET}"
        echo -e "  ${BOLD}${WHITE}│${RESET}  ${CYAN}1)${RESET} Listar Logs Disponíveis                     ${WHITE}│${RESET}"
        echo -e "  ${BOLD}${WHITE}│${RESET}  ${CYAN}2)${RESET} Visualizar Conteúdo de um Log               ${WHITE}│${RESET}"
        echo -e "  ${BOLD}${WHITE}│${RESET}  ${CYAN}3)${RESET} Analisar e Resumir Vulnerabilidades de um Log ${WHITE}│${RESET}"
        echo -e "  ${BOLD}${WHITE}│${RESET}  ${DGRAY}0)${RESET} Sair                                        ${WHITE}│${RESET}"
        echo -e "  ${BOLD}${WHITE}└─────────────────────────────────────────────────────────┘${RESET}"
        echo ""
        echo -ne "  ${YELLOW}▶ Escolha uma opção:${RESET} "
        read -r OPTION

        case "$OPTION" in
            1) list_logs ;;
            2) view_log ;;
            3) analyze_log ;;
            0) exit 0 ;;
            *) log WARN "Opção inválida." ;;
        esac
        echo -ne "\n  ${GRAY}Pressione ENTER para continuar...${RESET}"
        read -r
    done
}

# ── EXECUÇÃO ─────────────────────────────────────────────────────
main_menu
