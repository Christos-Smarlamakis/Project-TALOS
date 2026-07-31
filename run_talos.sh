#!/usr/bin/env bash
# ===========================================================================
# run_talos.sh -- Cross-Platform POSIX Launcher for Project TALOS v5.8.1
#
# Provides a 9-option structured menu:
#   Section 1: REST API & FRONTEND
#     [1] Full Setup (virtualenv + pip install + Frontend Provisioner)
#     [2] Start FastAPI Server (uvicorn, port 8001)
#     [3] Start MCP Server (python src/mcp_server.py)
#     [4] Launch Interim UI (Cherry Studio)
#   Section 2: CLI & STANDALONE DAEMONS
#     [5] TALOS Terminal CLI (python talos.py)
#     [6] Autonomous Research Daemon (python src/ai/drl/talos_service.py)
#     [7] Live DRL Agent (python src/ai/drl/talos_live_agent.py --verbose)
#   Section 3: TESTING & SYSTEM
#     [8] Run Test Suite (pytest -v)
#     [9] Exit
#
# TALOS FastAPI runs on port 8001 (port 8000 is reserved for SYNAPSE bus).
#
# Usage:
#   chmod +x run_talos.sh
#   ./run_talos.sh
# ===========================================================================

set -e  # Exit on error, but handle gracefully in menu choices

# -- Color codes for terminal output --
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# -- Detect project root (directory containing this script) --
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# -- Resolve Python command (prefer python3 on Linux) --
PYTHON_CMD="python3"
if ! command -v python3 &> /dev/null; then
    PYTHON_CMD="python"
fi

# -- Venv path --
VENV_DIR="$SCRIPT_DIR/talosenv"

# ---------------------------------------------------------------------------
# -- Helper functions --
# ---------------------------------------------------------------------------

print_banner() {
    clear
    echo "============================================="
    echo "   Project TALOS v5.8.1"
    echo "   Research Intelligence Platform"
    echo "   SYNAPSE Protocol Active (Bus :8000 / API :8001)"
    echo "============================================="
    echo ""
}

press_enter() {
    echo ""
    echo "Press Enter to return to the menu..."
    read -r
}

# ---------------------------------------------------------------------------
# -- Menu --
# ---------------------------------------------------------------------------

show_menu() {
    print_banner
    echo "   -- Section 1: REST API and FRONTEND --"
    echo "   [1] Full Setup (virtualenv + pip install + Frontend Provisioner)"
    echo "   [2] Start FastAPI Server (uvicorn, port 8001)"
    echo "   [3] Start MCP Server (python src/mcp_server.py)"
    echo "   [4] Launch Interim UI (Cherry Studio)"
    echo ""
    echo "   -- Section 2: CLI and STANDALONE DAEMONS --"
    echo "   [5] TALOS Terminal CLI (python talos.py)"
    echo "   [6] Autonomous Research Daemon (24/7 Service)"
    echo "   [7] Live DRL Agent (python src/ai/drl/talos_live_agent.py --verbose)"
    echo ""
    echo "   -- Section 3: TESTING and SYSTEM --"
    echo "   [8] Run Test Suite (pytest -v)"
    echo "   [9] Exit"
    echo ""
    echo -n "   Select mode [1-9]: "
}

# ---------------------------------------------------------------------------
# -- Option 1: Full Setup --
# ---------------------------------------------------------------------------

do_setup() {
    clear
    echo "============================================="
    echo "   Full Setup: Virtual Environment + Pip Install + Frontend Provisioner"
    echo "============================================="
    echo ""

    # Check Python.
    echo "[1/4] Checking Python..."
    if ! command -v "$PYTHON_CMD" &> /dev/null; then
        echo -e "${RED}[ERROR] Python not found on PATH.${NC}"
        echo "Please install Python 3.10+ from https://python.org"
        press_enter
        return
    fi
    echo -e "${GREEN}Python found:${NC} $($PYTHON_CMD --version)"

    # Create virtual environment.
    echo "[2/4] Creating virtual environment at $VENV_DIR..."
    $PYTHON_CMD -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
    echo -e "${GREEN}Virtual environment activated.${NC}"

    # Install dependencies.
    echo "[3/4] Installing Python dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo -e "${YELLOW}[WARNING] Some packages failed to install. Check the output above.${NC}"
    else
        echo -e "${GREEN}All dependencies installed successfully.${NC}"
    fi

    # Run frontend provisioner.
    echo "[4/4] Running Frontend Provisioner..."
    $PYTHON_CMD src/utils/frontend_provisioner.py
    if [ $? -ne 0 ]; then
        echo -e "${YELLOW}[WARNING] Frontend provisioner exited with errors. Check the output above.${NC}"
    else
        echo -e "${GREEN}Frontend provisioner completed successfully.${NC}"
    fi

    echo ""
    echo "============================================="
    echo -e "   ${GREEN}Setup complete. TALOS v5.8.1 is ready.${NC}"
    echo "============================================="
    echo ""
    echo "   TALOS API will start on port 8001."
    echo "   SYNAPSE bus is expected on port 8000."
    echo ""
    echo "   Activate the environment with:"
    echo "     source $VENV_DIR/bin/activate"
    echo ""
    press_enter
}

# ---------------------------------------------------------------------------
# -- Option 2: Start FastAPI Server --
# ---------------------------------------------------------------------------

do_server() {
    clear
    echo "============================================="
    echo "   Starting TALOS FastAPI Server (v5.8.1)"
    echo "   Port: 8001"
    echo "   API Docs: http://localhost:8001/docs"
    echo "   Health:   http://localhost:8001/api/v1/health"
    echo "   Synapse:  http://localhost:8001/api/v1/synapse/webhook"
    echo "============================================="
    echo ""
    echo "   Press Ctrl+C to stop the server."
    echo ""

    # Activate venv if it exists.
    if [ -f "$VENV_DIR/bin/activate" ]; then
        source "$VENV_DIR/bin/activate"
    else
        echo -e "${YELLOW}[WARNING] Virtual environment not found. Using system Python.${NC}"
        echo "   Run option [1] first for full setup."
    fi

    # Launch uvicorn.
    $PYTHON_CMD -m uvicorn src.api.main_api:app --host 127.0.0.1 --port 8001
    press_enter
}

# ---------------------------------------------------------------------------
# -- Option 3: Start MCP Server --
# ---------------------------------------------------------------------------

do_mcp_server() {
    clear
    echo "============================================="
    echo "   Starting TALOS MCP Server (v5.8.1)"
    echo "============================================="
    echo ""
    echo "   Press Ctrl+C to stop the MCP server."
    echo ""

    # Activate venv if it exists.
    if [ -f "$VENV_DIR/bin/activate" ]; then
        source "$VENV_DIR/bin/activate"
    else
        echo -e "${YELLOW}[WARNING] Virtual environment not found. Using system Python.${NC}"
    fi

    # Launch MCP server.
    $PYTHON_CMD src/mcp_server.py
    press_enter
}

# ---------------------------------------------------------------------------
# -- Option 4: Launch Interim UI --
# ---------------------------------------------------------------------------

do_provision_ui() {
    clear
    echo "============================================="
    echo "   Interim UI Provisioner (Cherry Studio)"
    echo "============================================="
    echo ""

    # Activate venv if it exists.
    if [ -f "$VENV_DIR/bin/activate" ]; then
        source "$VENV_DIR/bin/activate"
    fi

    # Run the provisioner.
    $PYTHON_CMD src/utils/frontend_provisioner.py "$@"
    echo ""
    echo "============================================="
    echo "   Provisioning complete."
    echo "   See cherry_ui_isolated/LAUNCH_INSTRUCTIONS.txt"
    echo "============================================="
    echo ""
    press_enter
}

# ---------------------------------------------------------------------------
# -- Option 5: TALOS Terminal CLI --
# ---------------------------------------------------------------------------

do_cli() {
    clear
    echo "============================================="
    echo "   TALOS Terminal CLI (v5.8.1)"
    echo "============================================="
    echo ""
    echo "   Launching the interactive TALOS command-line interface."
    echo "   Type 'help' inside the CLI for available commands."
    echo "   Press Ctrl+C to exit back to this menu."
    echo ""

    # Activate venv if it exists.
    if [ -f "$VENV_DIR/bin/activate" ]; then
        source "$VENV_DIR/bin/activate"
    else
        echo -e "${YELLOW}[WARNING] Virtual environment not found. Using system Python.${NC}"
    fi

    # Launch talos.py CLI.
    $PYTHON_CMD talos.py
    press_enter
}

# ---------------------------------------------------------------------------
# -- Option 6: Autonomous Research Daemon --
# ---------------------------------------------------------------------------

do_daemon() {
    clear
    echo "============================================="
    echo "   Autonomous Research Daemon (v5.8.1)"
    echo "   24/7 Background Research Service"
    echo "============================================="
    echo ""
    echo "   This daemon continuously discovers, evaluates, and enriches"
    echo "   research papers in the background. It runs until interrupted."
    echo ""
    echo "   Press Ctrl+C to stop the daemon and return to this menu."
    echo ""

    # Activate venv if it exists.
    if [ -f "$VENV_DIR/bin/activate" ]; then
        source "$VENV_DIR/bin/activate"
    else
        echo -e "${YELLOW}[WARNING] Virtual environment not found. Using system Python.${NC}"
    fi

    # Launch talos_service.py.
    $PYTHON_CMD src/ai/drl/talos_service.py
    press_enter
}

# ---------------------------------------------------------------------------
# -- Option 7: Live DRL Agent --
# ---------------------------------------------------------------------------

do_live_drl() {
    clear
    echo "============================================="
    echo "   Live DRL Agent (v5.8.1)"
    echo "   Deep Reinforcement Learning Agent -- Verbose Mode"
    echo "============================================="
    echo ""
    echo "   The Live DRL Agent interacts with the environment in real-time,"
    echo "   making decisions about paper discovery, evaluation, and enrichment."
    echo "   Verbose mode is enabled for detailed step-by-step output."
    echo ""
    echo "   Press Ctrl+C to stop the agent and return to this menu."
    echo ""

    # Activate venv if it exists.
    if [ -f "$VENV_DIR/bin/activate" ]; then
        source "$VENV_DIR/bin/activate"
    else
        echo -e "${YELLOW}[WARNING] Virtual environment not found. Using system Python.${NC}"
    fi

    # Launch talos_live_agent.py with verbose flag.
    $PYTHON_CMD src/ai/drl/talos_live_agent.py --verbose
    press_enter
}

# ---------------------------------------------------------------------------
# -- Option 8: Run Test Suite --
# ---------------------------------------------------------------------------

do_test() {
    clear
    echo "============================================="
    echo "   Running TALOS Test Suite (pytest)"
    echo "============================================="
    echo ""

    # Activate venv if it exists.
    if [ -f "$VENV_DIR/bin/activate" ]; then
        source "$VENV_DIR/bin/activate"
    fi

    # Check if pytest is installed.
    $PYTHON_CMD -m pytest --version > /dev/null 2>&1
    if [ $? -ne 0 ]; then
        echo -e "${YELLOW}[WARNING] pytest not found. Installing...${NC}"
        pip install pytest > /dev/null 2>&1
    fi

    echo "Running tests..."
    echo ""
    $PYTHON_CMD -m pytest -v --tb=short 2>&1

    if [ $? -ne 0 ]; then
        echo ""
        echo "============================================="
        echo -e "   ${RED}Some tests FAILED. Review output above.${NC}"
        echo "============================================="
    else
        echo ""
        echo "============================================="
        echo -e "   ${GREEN}All tests PASSED.${NC}"
        echo "============================================="
    fi

    echo ""
    press_enter
}

# ---------------------------------------------------------------------------
# -- Main Loop --
# ---------------------------------------------------------------------------

main() {
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
            8) do_test ;;
            9)
                echo ""
                echo "============================================="
                echo "   Closing Project TALOS v5.8.1..."
                echo "============================================="
                exit 0
                ;;
            *)
                echo -e "${RED}Invalid choice. Please select [1-9].${NC}"
                sleep 1
                ;;
        esac
    done
}

# -- Entry point --
main