#!/bin/bash

# ================================================================
#   Network Utilities - VulnScan PRO Complementary Script
#   Oferece utilitários de rede como ARP Scan e DNS Enumeration.
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
arp_scan() {
    echo -ne "  ${YELLOW}▶ Digite a interface de rede (ex: eth0, wlan0) ou deixe em branco para auto-detectar:${RESET} "
    read -r IFACE

    if [ -z "$IFACE" ]; then
        IFACE=$(ip route | grep default | awk 
            \'{print $5}\' | head -1)
        log INFO "Interface auto-detectada: $IFACE"
    fi

    if [ -z "$IFACE" ]; then
        log ERROR "Não foi possível detectar a interface de rede. Por favor, especifique manualmente."
        return 1
    fi

    log STEP "Realizando ARP Scan na interface $IFACE..."
    div
    sudo arp-scan --interface="$IFACE" --localnet
    div
    log OK "ARP Scan concluído."
}

dns_enum() {
    echo -ne "  ${YELLOW}▶ Digite o domínio para enumeração DNS (ex: example.com):${RESET} "
    read -r DOMAIN

    if [ -z "$DOMAIN" ]; then
        log WARN "Domínio não especificado."
        return 1
    fi

    log STEP "Realizando enumeração DNS para $DOMAIN..."
    div
    log INFO "Registros A (Endereço):"
    dig +short A "$DOMAIN"
    log INFO "Registros MX (Mail Exchange):"
    dig +short MX "$DOMAIN"
    log INFO "Registros NS (Name Server):"
    dig +short NS "$DOMAIN"
    log INFO "Registros TXT (Texto):"
    dig +short TXT "$DOMAIN"
    log INFO "Registros SOA (Start of Authority):"
    dig +short SOA "$DOMAIN"
    div
    log OK "Enumeração DNS concluída."
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
        echo -e "  ${RED}Network Utilities${RESET}  ${DGRAY}│${RESET}  ${YELLOW}Ferramentas complementares de rede${RESET}"
        echo -e "  ${DGRAY}$(printf \'%.0s═\' {1..73})${RESET}"
        echo ""

        echo -e "  ${BOLD}${WHITE}┌──────────────── MENU DE UTILITÁRIOS DE REDE ────────────────┐${RESET}"
        echo -e "  ${BOLD}${WHITE}│${RESET}  ${CYAN}1)${RESET} ARP Scan (Descoberta de Hosts na Rede Local) ${WHITE}│${RESET}"
        echo -e "  ${BOLD}${WHITE}│${RESET}  ${CYAN}2)${RESET} Enumeração DNS (Registros A, MX, NS, TXT, SOA) ${WHITE}│${RESET}"
        echo -e "  ${BOLD}${WHITE}│${RESET}  ${DGRAY}0)${RESET} Sair                                        ${WHITE}│${RESET}"
        echo -e "  ${BOLD}${WHITE}└─────────────────────────────────────────────────────────────┘${RESET}"
        echo ""
        echo -ne "  ${YELLOW}▶ Escolha uma opção:${RESET} "
        read -r OPTION

        case "$OPTION" in
            1) arp_scan ;;
            2) dns_enum ;;
            0) exit 0 ;;
            *) log WARN "Opção inválida." ;;
        esac
        echo -ne "\n  ${GRAY}Pressione ENTER para continuar...${RESET}"
        read -r
    done
}

# ── EXECUÇÃO ─────────────────────────────────────────────────────
main_menu
