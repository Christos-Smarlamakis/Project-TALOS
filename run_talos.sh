#!/usr/bin/env bash
# ===========================================================================
# run_talos.sh -- Cross-Platform POSIX Launcher for Project TALOS v5.9.0
#
# Provides a 10-option structured menu with full parity to run_talos.bat:
#   Section 1: REST API & FRONTEND
#     [1] Full Setup (virtualenv/Conda + pip install + Frontend Provisioner)
#     [2] Start FastAPI Server (uvicorn, port 8001) -- detached background
#     [3] Start MCP Server (python src/mcp_server.py) -- detached background
#     [4] Launch Interim UI (Cherry Studio) -- auto-start backend chain
#   Section 2: CLI & STANDALONE DAEMONS
#     [5] TALOS Terminal CLI (python talos.py)
#     [6] Autonomous Research Daemon (python src/ai/drl/talos_service.py)
#     [7] Live DRL Agent (python src/ai/drl/talos_live_agent.py --verbose)
#   Section 3: TESTING & SYSTEM
#     [8] Autonomous System Tester (RL Chaos Fuzzer)
#     [9] Run Test Suite (pytest -v)
#     [10] Exit
#
# TALOS FastAPI runs on port 8001 (port 8000 is reserved for SYNAPSE bus).
#
# Features (v5.9.0):
#   - Autonomous System Tester (RL-Driven Chaos Engineering with
#     LLM-as-a-Judge diagnostics).
#   - Auto-detects virtualenv (.venv/ or venv/) or Conda environments.
#   - Background servers launched as detached POSIX daemons.
#   - Option 4 auto-starts the FastAPI backend chain before provisioning.
#   - Automatic Fermion CPU server spawning when FAST_EDGE_MODEL contains
#     Neutrino or is set to local mode.
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

# -- Resolve Python command (prefer python3 on Linux/macOS) --
PYTHON_CMD="python3"
if ! command -v python3 &>/dev/null; then
    PYTHON_CMD="python"
fi

# ===========================================================================
# -- Auto-Environment Detection --
# Scans for a local virtualenv (.venv/ or venv/) first, then falls back to
# Conda if available. Activates the first valid environment found and exports
# the path for all subsequent operations.
# ===========================================================================

ACTIVATED_ENV=""

detect_and_activate_env() {
    # -- Already activated? Skip --
    if [ -n "$ACTIVATED_ENV" ]; then
        return 0
    fi

    # -- Priority 1: Local virtualenv (.venv/ or venv/) --
    if [ -f "$SCRIPT_DIR/.venv/bin/activate" ]; then
        echo -e "${GREEN}[INFO]${NC} Auto-detected virtualenv: $SCRIPT_DIR/.venv"
        source "$SCRIPT_DIR/.venv/bin/activate"
        ACTIVATED_ENV=".venv"
        return 0
    fi

    if [ -f "$SCRIPT_DIR/venv/bin/activate" ]; then
        echo -e "${GREEN}[INFO]${NC} Auto-detected virtualenv: $SCRIPT_DIR/venv"
        source "$SCRIPT_DIR/venv/bin/activate"
        ACTIVATED_ENV="venv"
        return 0
    fi

    # -- Priority 2: Conda environment --
    if command -v conda &>/dev/null; then
        # Dynamically resolve the Conda base path for non-standard installs.
        CONDA_BASE="$(conda info --base 2>/dev/null || echo "")"
        if [ -n "$CONDA_BASE" ] && [ -f "$CONDA_BASE/etc/profile.d/conda.sh" ]; then
            source "$CONDA_BASE/etc/profile.d/conda.sh"
        fi
        # Attempt to activate talosenv.
        if conda activate talosenv &>/dev/null; then
            echo -e "${GREEN}[INFO]${NC} Auto-detected Conda environment: talosenv (base: $CONDA_BASE)"
            ACTIVATED_ENV="conda:talosenv"
            return 0
        fi
    fi

    # -- Fallback: warn but continue with system Python --
    echo -e "${YELLOW}[WARNING]${NC} No virtualenv or Conda environment found. Using system Python."
    ACTIVATED_ENV="system"
    return 1
}

# ===========================================================================
# -- Helper Functions --
# ===========================================================================

print_banner() {
    clear
    echo "============================================="
    echo "   Project TALOS v5.9.0"
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

# ===========================================================================
# -- Menu --
# ===========================================================================

show_menu() {
    print_banner
    echo "   -- Section 1: REST API and FRONTEND --"
    echo "   [1] Full Setup (virtualenv/Conda + pip install + Frontend Provisioner)"
    echo "   [2] Start FastAPI Server (uvicorn, port 8001 -- background)"
    echo "   [3] Start MCP Server (python src/mcp_server.py -- background)"
    echo "   [4] Launch Interim UI (Cherry Studio)"
    echo ""
    echo "   -- Section 2: CLI and STANDALONE DAEMONS --"
    echo "   [5] TALOS Terminal CLI (python talos.py)"
    echo "   [6] Autonomous Research Daemon (24/7 Service)"
    echo "   [7] Live DRL Agent (python src/ai/drl/talos_live_agent.py --verbose)"
    echo ""
    echo "   -- Section 3: TESTING and SYSTEM --"
    echo "   [8] Autonomous System Tester (RL Chaos Fuzzer)"
    echo "   [9] Run Test Suite (pytest -v)"
    echo "   [10] Exit"
    echo ""
    echo -n "   Select mode [1-10]: "
}

# ===========================================================================
# -- Option 1: Full Setup --
# ===========================================================================

do_setup() {
    clear
    echo "============================================="
    echo "   Full Setup: Virtual Environment + Pip Install + Frontend Provisioner"
    echo "============================================="
    echo ""

    # Check Python.
    echo "[1/4] Checking Python..."
    if ! command -v "$PYTHON_CMD" &>/dev/null; then
        echo -e "${RED}[ERROR] Python not found on PATH.${NC}"
        echo "Please install Python 3.10+ from https://python.org"
        press_enter
        return
    fi
    echo -e "${GREEN}Python found:${NC} $($PYTHON_CMD --version)"

    # Create virtual environment if neither venv nor conda is active.
    echo "[2/4] Setting up Python environment..."
    if [ -f "$SCRIPT_DIR/.venv/bin/activate" ]; then
        echo "Found existing .venv/ environment."
        source "$SCRIPT_DIR/.venv/bin/activate"
        ACTIVATED_ENV=".venv"
    elif [ -f "$SCRIPT_DIR/venv/bin/activate" ]; then
        echo "Found existing venv/ environment."
        source "$SCRIPT_DIR/venv/bin/activate"
        ACTIVATED_ENV="venv"
    elif command -v conda &>/dev/null; then
        CONDA_BASE="$(conda info --base 2>/dev/null || echo "")"
        if [ -n "$CONDA_BASE" ] && [ -f "$CONDA_BASE/etc/profile.d/conda.sh" ]; then
            source "$CONDA_BASE/etc/profile.d/conda.sh"
        fi
        conda create -n talosenv python=3.11 -y &>/dev/null
        conda activate talosenv
        ACTIVATED_ENV="conda:talosenv"
        echo "Conda environment 'talosenv' created and activated."
    else
        echo "Creating virtual environment at $SCRIPT_DIR/.venv..."
        $PYTHON_CMD -m venv "$SCRIPT_DIR/.venv"
        source "$SCRIPT_DIR/.venv/bin/activate"
        ACTIVATED_ENV=".venv"
        echo "Virtual environment created at .venv/"
    fi
    echo -e "${GREEN}Python environment activated: ${ACTIVATED_ENV}${NC}"

    # Install dependencies.
    echo "[3/4] Installing Python dependencies..."
    pip install --upgrade pip &>/dev/null
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
    echo -e "   ${GREEN}Setup complete. TALOS v5.9.0 is ready.${NC}"
    echo "============================================="
    echo ""
    echo "   TALOS API will start on port 8001."
    echo "   SYNAPSE bus is expected on port 8000."
    echo ""
    echo "   Activate the environment with:"
    echo "     source $SCRIPT_DIR/.venv/bin/activate"
    echo ""
    press_enter
}

# ===========================================================================
# -- Option 2: Start FastAPI Server (Detached Background Daemon) --
# ===========================================================================

do_server() {
    clear
    echo "============================================="
    echo "   Starting TALOS FastAPI Server (v5.9.0)"
    echo "   Port: 8001"
    echo "   API Docs: http://localhost:8001/docs"
    echo "   Health:   http://localhost:8001/api/v1/health"
    echo "   Synapse:  http://localhost:8001/api/v1/synapse/webhook"
    echo "============================================="
    echo ""
    echo "   Launching FastAPI server as a detached background process..."
    echo "   Use 'kill \$(lsof -ti:8001)' to stop it."
    echo ""

    # -- Activate environment --
    detect_and_activate_env

    # -- Launch uvicorn in background with output redirected --
    $PYTHON_CMD -m uvicorn src.api.main_api:app \
        --host 127.0.0.1 --port 8001 \
        > /dev/null 2>&1 &
    FASTAPI_PID=$!
    echo -e "${GREEN}[INFO]${NC} TALOS FastAPI server started (PID: $FASTAPI_PID)."

    # -- Auto-start Fermion CPU daemon if FAST_EDGE_MODEL is Neutrino/local --
    check_fermion

    echo "[INFO] Wait a few seconds then visit http://localhost:8001/docs"
    echo ""
    echo "Press Enter to return to the main menu..."
    read -r
}

# ===========================================================================
# -- Option 3: Start MCP Server (Detached Background Daemon) --
# ===========================================================================

do_mcp_server() {
    clear
    echo "============================================="
    echo "   Starting TALOS MCP Server (v5.9.0)"
    echo "============================================="
    echo ""
    echo "   Launching MCP server as a detached background process..."
    echo ""

    # -- Activate environment --
    detect_and_activate_env

    # -- Launch MCP server in background with output redirected --
    $PYTHON_CMD src/mcp_server.py > /dev/null 2>&1 &
    MCP_PID=$!
    echo -e "${GREEN}[INFO]${NC} TALOS MCP server started (PID: $MCP_PID)."
    echo ""
    echo "Press Enter to return to the main menu..."
    read -r
}

# ===========================================================================
# -- Option 4: Launch Interim UI (Auto-Start Backend Chain) --
# ===========================================================================

do_provision_ui() {
    clear
    echo "============================================="
    echo "   Interim UI Provisioner (Cherry Studio)"
    echo "   Auto-Start Chain: FastAPI Backend -> UI"
    echo "============================================="
    echo ""

    # -- Activate environment --
    detect_and_activate_env

    # -- Step 1: Start FastAPI server in background --
    echo "[1/3] Starting TALOS FastAPI server in background (port 8001)..."
    $PYTHON_CMD -m uvicorn src.api.main_api:app \
        --host 127.0.0.1 --port 8001 \
        > /dev/null 2>&1 &
    FASTAPI_PID=$!
    echo -e "${GREEN}[INFO]${NC} FastAPI server started (PID: $FASTAPI_PID)."

    # -- Step 2: Wait for server to initialize --
    echo "[2/3] Waiting 2 seconds for server to initialize..."
    sleep 2
    echo -e "${GREEN}[INFO]${NC} Wait complete."

    # -- Step 3: Run the frontend provisioner --
    echo "[3/3] Running Frontend Provisioner..."
    $PYTHON_CMD src/utils/frontend_provisioner.py "$@"

    echo ""
    echo "============================================="
    echo "   Provisioning complete."
    echo "   FastAPI server running in background on port 8001 (PID: $FASTAPI_PID)."
    echo "   See cherry_ui_isolated/LAUNCH_INSTRUCTIONS.txt"
    echo "============================================="
    echo ""
    press_enter
}

# ===========================================================================
# -- Option 5: TALOS Terminal CLI --
# ===========================================================================

do_cli() {
    clear
    echo "============================================="
    echo "   TALOS Terminal CLI (v5.9.0)"
    echo "============================================="
    echo ""
    echo "   Launching the interactive TALOS command-line interface."
    echo "   Press Ctrl+C to exit back to this menu."
    echo ""

    # -- Activate environment --
    detect_and_activate_env

    # -- Launch talos.py CLI --
    $PYTHON_CMD talos.py
    press_enter
}

# ===========================================================================
# -- Option 6: Autonomous Research Daemon --
# ===========================================================================

do_daemon() {
    clear
    echo "============================================="
    echo "   Autonomous Research Daemon (v5.9.0)"
    echo "   24/7 Background Research Service"
    echo "============================================="
    echo ""
    echo "   This daemon continuously discovers, evaluates, and enriches"
    echo "   research papers in the background. It runs until interrupted."
    echo ""
    echo "   Press Ctrl+C to stop the daemon and return to this menu."
    echo ""

    # -- Activate environment --
    detect_and_activate_env

    # -- Launch talos_service.py --
    $PYTHON_CMD src/ai/drl/talos_service.py
    press_enter
}

# ===========================================================================
# -- Option 7: Live DRL Agent --
# ===========================================================================

do_live_drl() {
    clear
    echo "============================================="
    echo "   Live DRL Agent (v5.9.0)"
    echo "   Deep Reinforcement Learning Agent -- Verbose Mode"
    echo "============================================="
    echo ""
    echo "   The Live DRL Agent interacts with the environment in real-time,"
    echo "   making decisions about paper discovery, evaluation, and enrichment."
    echo "   Verbose mode is enabled for detailed step-by-step output."
    echo ""
    echo "   Press Ctrl+C to stop the agent and return to this menu."
    echo ""

    # -- Activate environment --
    detect_and_activate_env

    # -- Launch talos_live_agent.py with verbose flag --
    $PYTHON_CMD src/ai/drl/talos_live_agent.py --verbose
    press_enter
}

# ===========================================================================
# -- Option 8: Autonomous System Tester (RL Chaos Fuzzer) --
# ===========================================================================

do_auto_tester() {
    clear
    echo "============================================="
    echo "   Autonomous System Tester (v5.9.0)"
    echo "   RL-Driven Chaos Engineering with LLM-as-a-Judge"
    echo "============================================="
    echo ""
    echo "   Stress-tests TALOS system components using a Non-Stationary"
    echo "   Epsilon-Greedy Multi-Armed Bandit. Diagnoses crashes with the"
    echo "   Fast Edge LLM and saves Markdown reports in reports/autonomous_tester/."
    echo ""
    echo "   Target components: FastAPI Server, MCP Server, Daily Search,"
    echo "   Citation Analyzer. Q-table saved to data/tester_q_table.json."
    echo ""
    echo "   Press Ctrl+C to abort the test run early."
    echo ""

    # -- Activate environment --
    detect_and_activate_env

    # -- Launch autonomous tester --
    $PYTHON_CMD src/ai/testing/autonomous_tester.py "$@"
    press_enter
}

# ===========================================================================
# -- Option 9: Run Test Suite --
# ===========================================================================

do_test() {
    clear
    echo "============================================="
    echo "   Running TALOS Test Suite (pytest)"
    echo "============================================="
    echo ""

    # -- Activate environment --
    detect_and_activate_env

    # -- Check if pytest is installed --
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

# ===========================================================================
# -- Fermion Auto-Start Subroutine --
# Reads .env for FAST_EDGE_MODEL; if it contains "Neutrino" or equals
# "local", spawns fermion serve as a detached background daemon.
# ===========================================================================

check_fermion() {
    # -- Parse .env file for FAST_EDGE_MODEL --
    if [ ! -f "$SCRIPT_DIR/.env" ]; then
        return 0
    fi
    FAST_EDGE=""
    # shellcheck disable=SC2034
    while IFS='=' read -r key value; do
        case "$key" in
            FAST_EDGE_MODEL) FAST_EDGE="$value" ;;
        esac
    done < "$SCRIPT_DIR/.env"

    if [ -z "$FAST_EDGE" ]; then
        return 0
    fi

    # -- Check if FAST_EDGE_MODEL contains "Neutrino" or "local" --
    case "$FAST_EDGE" in
        *[Nn]eutrino*|*local*)
            echo ""
            echo "[FERMION] Fast Edge model requires CPU accelerator -- starting fermion serve..."
            echo "[FERMION] Model: $FAST_EDGE on port 11435"
            fermion serve --port 11435 > /dev/null 2>&1 &
            FERMION_PID=$!
            echo "[FERMION] Background daemon launched (PID: $FERMION_PID)."
            echo "[FERMION] Waiting 2 seconds for engine initialization..."
            sleep 2
            echo "[FERMION] Fast Edge engine ready on port 11435."
            ;;
    esac
    return 0
}

# ===========================================================================
# -- Main Loop --
# ===========================================================================

main() {
    # -- Run auto-detection once at startup --
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
                echo "============================================="
                echo "   Closing Project TALOS v5.9.0..."
                echo "============================================="
                exit 0
                ;;
            *)
                echo -e "${RED}Invalid choice. Please select [1-10].${NC}"
                sleep 1
                ;;
        esac
    done
}

# -- Entry point --
main