#!/usr/bin/env bash
# ===========================================================================
# run_talos.sh -- Cross-Platform POSIX Launcher for Project TALOS v5.7.1
#
# Mirrors run_talos.bat with 5 options for Linux/macOS/Unix environments:
#   [1] Full Setup (virtualenv + pip install)
#   [2] Start FastAPI Server (uvicorn, port 8001)
#   [3] Start MCP Server
#   [4] Launch Interim UI (Cherry Studio provisioner)
#   [5] Run Test Suite (pytest -v)
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
    echo "   Project TALOS v5.7.1"
    echo "   Research Intelligence Platform"
    echo "   Multi-Tier LLM Routing Active"
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
    echo "   [1] Full Setup (virtualenv + pip install)"
    echo "   [2] Start FastAPI Server (uvicorn, port 8001)"
    echo "   [3] Start MCP Server"
    echo "   [4] Launch Interim UI (Cherry Studio)"
    echo "   [5] Run Test Suite (pytest -v)"
    echo "   [6] Exit"
    echo ""
    echo -n "   Select mode [1-6]: "
}

# ---------------------------------------------------------------------------
# -- Option 1: Full Setup --
# ---------------------------------------------------------------------------

do_setup() {
    clear
    echo "============================================="
    echo "   Full Setup: Virtual Environment + Pip Install"
    echo "============================================="
    echo ""

    # Check Python.
    echo "[1/3] Checking Python..."
    if ! command -v "$PYTHON_CMD" &> /dev/null; then
        echo -e "${RED}[ERROR] Python not found on PATH.${NC}"
        echo "Please install Python 3.10+ from https://python.org"
        press_enter
        return
    fi
    echo -e "${GREEN}Python found:${NC} $($PYTHON_CMD --version)"

    # Create virtual environment.
    echo "[2/3] Creating virtual environment at $VENV_DIR..."
    $PYTHON_CMD -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
    echo -e "${GREEN}Virtual environment activated.${NC}"

    # Install dependencies.
    echo "[3/3] Installing Python dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo -e "${YELLOW}[WARNING] Some packages failed to install. Check the output above.${NC}"
    else
        echo -e "${GREEN}All dependencies installed successfully.${NC}"
    fi

    echo ""
    echo "============================================="
    echo -e "   ${GREEN}Setup complete. TALOS v5.7.1 is ready.${NC}"
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
    echo "   Starting TALOS FastAPI Server (v5.7.1)"
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
    echo "   Starting TALOS MCP Server (v5.7.1)"
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
    $PYTHON_CMD -m src.mcp_server
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
# -- Option 5: Run Test Suite --
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
            5) do_test ;;
            6)
                echo ""
                echo "============================================="
                echo "   Closing Project TALOS v5.7.1..."
                echo "============================================="
                exit 0
                ;;
            *)
                echo -e "${RED}Invalid choice. Please select [1-6].${NC}"
                sleep 1
                ;;
        esac
    done
}

# -- Entry point --
main