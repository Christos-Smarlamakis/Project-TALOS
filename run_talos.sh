#!/usr/bin/env bash
# ===========================================================================
# script         : run_talos.sh
# version        : v5.10.0 (Academic Ingestion Expansion)
# description    : Cross-Platform POSIX Dashboard for Project TALOS.
#                  Implements Two-Column UI, IEEE WEIGD standard telemetry,
#                  defensive error handling, Universal ASCII rendering, and
#                  OS-Aware Zero-Click Miniconda Provisioning (Linux/macOS).
# ===========================================================================

set -e  # Exit on critical error

# ---------------------------------------------------------------------------
# [ INIT ] Enforce Terminal Viewport Dimensions (xterm compatible)
# Width: 105, Height: 32. Ensures NO SCROLLBAR appears and logo stays at top.
# ---------------------------------------------------------------------------
printf '\033[8;32;105t'

# ---------------------------------------------------------------------------
# [ INIT ] Color Palette Definition (IEEE WEIGD Compliance - True Color)
# ---------------------------------------------------------------------------
C_RESET='\033[0m'
C_IEEE_LIGHT='\033[38;2;0;102;153m'
C_IEEE_DARK='\033[38;2;0;28;85m'
C_GREEN='\033[38;2;40;167;69m'
C_RED='\033[38;2;220;53;69m'
C_YELLOW='\033[38;2;255;193;7m'
C_CYAN='\033[38;2;23;162;184m'

# ---------------------------------------------------------------------------
# [ INIT ] Working Directory & Interpreter Resolution
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PYTHON_CMD="python3"
if ! command -v python3 &>/dev/null; then
    PYTHON_CMD="python"
fi

# ===========================================================================
# SYSTEM SUBROUTINES
# ===========================================================================

log_info()    { echo -e "${C_CYAN}[$(date +%T)] [ INFO ]${C_RESET} $1"; }
log_success() { echo -e "${C_GREEN}[$(date +%T)] [ SUCCESS ]${C_RESET} $1"; }
log_warn()    { echo -e "${C_YELLOW}[$(date +%T)] [ WARNING ]${C_RESET} $1"; }
log_error()   { echo -e "${C_RED}[$(date +%T)] [ ERROR ]${C_RESET} $1"; }

press_enter() {
    echo ""
    read -r -p "Press Enter to return to the menu..."
}

check_port_silent() {
    local port=$1
    local var_name=$2
    local is_online=1

    # Cross-platform port resolution (macOS/Linux)
    if command -v nc >/dev/null 2>&1; then
        nc -z 127.0.0.1 "$port" >/dev/null 2>&1 && is_online=0
    elif command -v lsof >/dev/null 2>&1; then
        lsof -i ":$port" >/dev/null 2>&1 && is_online=0
    elif command -v ss >/dev/null 2>&1; then
        ss -tln | grep -q ":$port " && is_online=0
    else
        netstat -tln | grep -q ":$port " && is_online=0
    fi

    if [ $is_online -eq 0 ]; then
        eval "$var_name=\"${C_GREEN}ONLINE${C_RESET}\""
    else
        eval "$var_name=\"${C_RED}OFFLINE${C_RESET}\""
    fi
}

detect_and_activate_env() {
    if [ -f "$SCRIPT_DIR/.venv/bin/activate" ]; then
        source "$SCRIPT_DIR/.venv/bin/activate"
        return 0
    elif [ -f "$SCRIPT_DIR/venv/bin/activate" ]; then
        source "$SCRIPT_DIR/venv/bin/activate"
        return 0
    elif command -v conda >/dev/null 2>&1 || [ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
        local CONDA_BASE=""
        if command -v conda >/dev/null 2>&1; then
            CONDA_BASE="$(conda info --base 2>/dev/null || echo "")"
        fi
        [ -z "$CONDA_BASE" ] && CONDA_BASE="$HOME/miniconda3"
        
        if [ -f "$CONDA_BASE/etc/profile.d/conda.sh" ]; then
            source "$CONDA_BASE/etc/profile.d/conda.sh"
            conda activate talosenv >/dev/null 2>&1 || true
        fi
        return 0
    fi
    return 1
}

# ===========================================================================
# MAIN DASHBOARD (Two-Column User Interface)
# ===========================================================================

show_menu() {
    clear
    check_port_silent 8001 API_STATUS
    check_port_silent 8000 SYNAPSE_STATUS
    check_port_silent 11435 EDGE_STATUS

    echo -e "${C_IEEE_DARK}=====================================================================================================${C_RESET}"
    echo -e "${C_IEEE_LIGHT}          #########   ######   ##         ######    ###### ${C_RESET}"
    echo -e "${C_IEEE_LIGHT}             ##      ##    ##  ##        ##    ##  ##      ${C_RESET}"
    echo -e "${C_IEEE_LIGHT}             ##      ########  ##        ##    ##  ####### ${C_RESET}"
    echo -e "${C_IEEE_LIGHT}             ##      ##    ##  ##        ##    ##       ## ${C_RESET}"
    echo -e "${C_IEEE_LIGHT}             ##      ##    ##  ########   ######   ######  ${C_RESET}"
    echo -e "${C_IEEE_DARK}=====================================================================================================${C_RESET}"
    echo -e "  ${C_CYAN}Project TALOS v5.10.0 -- Research Intelligence Ecosystem (IEEE WEIGD Supported)${C_RESET}"
    echo -e "${C_IEEE_DARK}=====================================================================================================${C_RESET}"
    echo -e "  [ SYSTEM TELEMETRY ]    API (8001): ${API_STATUS}   |   BUS (8000): ${SYNAPSE_STATUS}   |   EDGE (11435): ${EDGE_STATUS}"
    echo -e "${C_IEEE_DARK}-----------------------------------------------------------------------------------------------------${C_RESET}"
    echo -e "  ${C_IEEE_LIGHT}[ INFRASTRUCTURE & UI ]${C_RESET}                       ${C_IEEE_LIGHT}[ REASONING AGENTS ]${C_RESET}"
    echo -e "  [1] Full Setup (Auto-Conda + Pip + UI)       [5] TALOS Console (Interactive CLI)"
    echo -e "  [2] Start FastAPI Server (Background)        [6] Autonomous Research Daemon (24/7)"
    echo -e "  [3] Start MCP Server (Background)            [7] Live DRL Agent (Verbose Output)"
    echo -e "  [4] Launch UI (Cherry Studio Provisioner)"
    echo -e ""
    echo -e "  ${C_IEEE_LIGHT}[ TESTING & MAINTENANCE ]${C_RESET}"
    echo -e "  [8] Autonomous Red Tester (RL Chaos Fuzzer)   [10] Terminate Session"
    echo -e "  [9] Execute Test Framework (Pytest Suite)"
    echo -e "${C_IEEE_DARK}=====================================================================================================${C_RESET}"
    echo -e ""
    echo -ne "  ${C_CYAN}Select Operational Directive [1-10]:${C_RESET} "
}

# ===========================================================================
# EXECUTION MATRICES
# ===========================================================================

do_setup() {
    clear
    log_info "Initiating Global Setup Sequence..."
    
    # Check for Conda
    if ! command -v conda >/dev/null 2>&1 && [ ! -d "$HOME/miniconda3" ]; then
        log_warn "Conda distribution not found on system PATH."
        log_info "Initiating OS-Aware Zero-Click Miniconda3 Deployment..."
        
        OS_TYPE=$(uname -s)
        ARCH_TYPE=$(uname -m)
        MC_URL=""
        
        if [ "$OS_TYPE" = "Linux" ]; then
            if [ "$ARCH_TYPE" = "aarch64" ]; then
                MC_URL="https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-aarch64.sh"
            else
                MC_URL="https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh"
            fi
        elif [ "$OS_TYPE" = "Darwin" ]; then
            if [ "$ARCH_TYPE" = "arm64" ]; then
                MC_URL="https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-arm64.sh"
            else
                MC_URL="https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh"
            fi
        fi
        
        if [ -n "$MC_URL" ]; then
            log_info "Downloading Miniconda3 for $OS_TYPE ($ARCH_TYPE)..."
            curl -# -k -o miniconda_installer.sh "$MC_URL"
            log_info "Executing silent background installation to $HOME/miniconda3..."
            bash miniconda_installer.sh -b -p "$HOME/miniconda3" >/dev/null 2>&1
            rm miniconda_installer.sh
            export PATH="$HOME/miniconda3/bin:$PATH"
            log_success "Miniconda3 subsystem successfully installed."
        else
            log_error "Unsupported Architecture for automatic Conda deployment."
            exit 1
        fi
    fi

    log_info "Provisioning 'talosenv' runtime (Python 3.11)..."
    detect_and_activate_env || true
    conda create -n talosenv python=3.11 -y >/dev/null 2>&1 || true
    source "$HOME/miniconda3/etc/profile.d/conda.sh" 2>/dev/null || true
    conda activate talosenv >/dev/null 2>&1 || true

    log_info "Resolving and installing Python dependencies..."
    pip install -r requirements.txt >/dev/null 2>&1
    log_success "All dependencies successfully integrated."

    log_info "Triggering Frontend Provisioner..."
    $PYTHON_CMD src/utils/frontend_provisioner.py

    echo "[5/5] Provisioning Local AI Models (Air-Gap Readiness)..."
    log_info "Pulling Fast Edge Model (fermionresearch/Neutrino-8B)..."
    fermion pull fermionresearch/Neutrino-8B >/dev/null 2>&1 || log_warn "Fermion pull skipped or offline."

    if command -v ollama >/dev/null 2>&1; then
        log_info "Pulling Heavy Reasoning Model (qwen2.5:14b)..."
        ollama pull qwen2.5:14b || log_warn "Ollama pull skipped."
    else
        log_warn "Ollama not found on PATH. Skipping GPU model pull."
    fi

    log_success "TALOS v5.10.0 deployment finalized."
    press_enter
}

do_server() {
    clear
    local STATUS=""
    check_port_silent 8001 STATUS
    if [[ "$STATUS" == *"ONLINE"* ]]; then
        log_warn "Port 8001 is engaged. FastAPI Server is already operational."
        press_enter
        return
    fi

    log_info "Bootstrapping FastAPI Microservice..."
    detect_and_activate_env
    nohup $PYTHON_CMD -m uvicorn src.api.main_api:app --host 127.0.0.1 --port 8001 > /dev/null 2>&1 &
    log_success "Microservice dispatched to background (PID: $!)."
    check_fermion
    press_enter
}

do_mcp_server() {
    clear
    log_info "Bootstrapping MCP Server..."
    detect_and_activate_env
    nohup $PYTHON_CMD src/mcp_server.py > /dev/null 2>&1 &
    log_success "MCP Server operational in background (PID: $!)."
    press_enter
}

do_provision_ui() {
    clear
    local STATUS=""
    log_info "Validating Backend Data Stream..."
    check_port_silent 8001 STATUS
    
    if [[ "$STATUS" == *"ONLINE"* ]]; then
        log_success "FastAPI Server detected."
    else
        log_info "FastAPI offline. Auto-starting backend..."
        detect_and_activate_env
        nohup $PYTHON_CMD -m uvicorn src.api.main_api:app --host 127.0.0.1 --port 8001 > /dev/null 2>&1 &
        sleep 2
    fi

    log_info "Deploying React User Interface..."
    detect_and_activate_env
    $PYTHON_CMD src/utils/frontend_provisioner.py "$@"
    press_enter
}

do_cli() {
    clear
    log_info "Initializing Terminal Interactive Mode..."
    detect_and_activate_env
    $PYTHON_CMD talos.py
}

do_daemon() {
    clear
    log_info "Engaging Autonomous Research Daemon..."
    detect_and_activate_env
    $PYTHON_CMD src/ai/drl/talos_service.py
}

do_live_drl() {
    clear
    log_info "Engaging Deep Reinforcement Learning Agent..."
    detect_and_activate_env
    $PYTHON_CMD src/ai/drl/talos_live_agent.py --verbose
}

do_auto_tester() {
    clear
    log_info "Deploying Autonomous Red Tester (RL Chaos Fuzzer)..."
    detect_and_activate_env
    $PYTHON_CMD src/ai/testing/red_tester.py "$@"
    press_enter
}

do_test() {
    clear
    log_info "Executing Comprehensive Pytest Suite..."
    detect_and_activate_env
    if ! command -v pytest >/dev/null 2>&1; then
        log_warn "Pytest framework absent. Initializing installation..."
        pip install pytest >/dev/null 2>&1
    fi
    $PYTHON_CMD -m pytest -v --tb=short 2>&1
    press_enter
}

check_fermion() {
    if [ ! -f "$SCRIPT_DIR/.env" ]; then return 0; fi
    
    local FAST_EDGE=""
    while IFS='=' read -r key value; do
        if [ "$key" == "FAST_EDGE_MODEL" ]; then FAST_EDGE="$value"; fi
    done < "$SCRIPT_DIR/.env"

    if [[ "$FAST_EDGE" == *"[Nn]eutrino"* ]] || [[ "$FAST_EDGE" == *"local"* ]]; then
        local STATUS=""
        check_port_silent 11435 STATUS
        if [[ "$STATUS" == *"OFFLINE"* ]]; then
            log_info "Bootstrapping Fermion CPU Edge Accelerator..."
            nohup fermion serve --port 11435 > /dev/null 2>&1 &
            sleep 2
        fi
    fi
}

# ===========================================================================
# MAIN LOOP
# ===========================================================================
detect_and_activate_env

while true; do
    show_menu
    read -r choice
    case "$choice" in
        1) do_setup ;;
        2) do_server ;;
        3) do_mcp_server ;;
        4) do_provision_ui ;;
        5) do_cli ;;
        6) do_daemon ;;
        7) do_live_drl ;;
        8) do_auto_tester ;;
        9) do_test ;;
        10)
            echo ""
            echo -e "${C_IEEE_DARK}=====================================================================================================${C_RESET}"
            echo -e "  Closing Project TALOS v5.10.0..."
            echo -e "${C_IEEE_DARK}=====================================================================================================${C_RESET}"
            # Reset viewport constraint on exit
            printf '\033[8;24;80t' >/dev/null 2>&1 || true
            exit 0
            ;;
        *)
            echo -e "${C_RED}Invalid directive. Please select [1-10].${C_RESET}"
            sleep 1
            ;;
    esac
done