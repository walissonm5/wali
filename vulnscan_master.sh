#!/bin/bash

# ================================================================
#   VulnScan PRO Master Automation Script
#   Controla a execução do VulnScan PRO e seus scripts complementares.
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
    echo -e "  ${DGRAY}$(printf \'%.0s═\' {1..73})${RESET}"
    echo -e "  ${RED}VulnScan PRO Master Control${RESET}  ${DGRAY}│${RESET}  ${YELLOW}Gerenciador de Ferramentas de Pentest${RESET}"
    echo -e "  ${DGRAY}$(printf \'%.0s═\' {1..73})${RESET}"
    echo ""
}

# ── MAIN MENU ────────────────────────────────────────────────────
main_menu() {
    while true; do
        banner
        echo -e "  ${BOLD}${WHITE}┌──────────────── MENU PRINCIPAL ─────────────────┐${RESET}"
        echo -e "  ${BOLD}${WHITE}│${RESET}  ${GREEN}1)${RESET} Executar VulnScan PRO (Scanner Principal) ${WHITE}│${RESET}"
        echo -e "  ${BOLD}${WHITE}│${RESET}  ${CYAN}2)${RESET} Executar MSF Handler Automation         ${WHITE}│${RESET}"
        echo -e "  ${BOLD}${WHITE}│${RESET}  ${YELLOW}3)${RESET} Executar Log Analyzer & Reporter        ${WHITE}│${RESET}"
        echo -e "  ${BOLD}${WHITE}│${RESET}  ${MAGENTA}4)${RESET} Executar Network Utilities              ${WHITE}│${RESET}"
        echo -e "  ${BOLD}${WHITE}│${RESET}  ${DGRAY}0)${RESET} Sair                                    ${WHITE}│${RESET}"
        echo -e "  ${BOLD}${WHITE}└─────────────────────────────────────────────────┘${RESET}"
        echo ""
        echo -ne "  ${YELLOW}▶ Escolha uma opção:${RESET} "
        read -r OPTION

        case "$OPTION" in
            1)
                log INFO "Iniciando VulnScan PRO..."
                "$BASE_DIR/vulnscan_pro_updated.sh"
                ;;
            2)
                log INFO "Iniciando MSF Handler Automation..."
                "$BASE_DIR/msf_handler_automation.sh"
                ;;
            3)
                log INFO "Iniciando Log Analyzer & Reporter..."
                "$BASE_DIR/log_analyzer.sh"
                ;;
            4)
                log INFO "Iniciando Network Utilities..."
                "$BASE_DIR/network_utilities.sh"
                ;;
            0)
                log INFO "Encerrando VulnScan PRO Master Control."
                exit 0
                ;;
            *)
                log WARN "Opção inválida: $OPTION"
                ;;
        esac
        echo -ne "\n  ${GRAY}Pressione ENTER para voltar ao menu principal...${RESET}"
        read -r
    done
}

# ── EXECUÇÃO ─────────────────────────────────────────────────────
main_menu
