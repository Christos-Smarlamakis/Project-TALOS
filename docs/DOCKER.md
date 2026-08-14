# TALOS -- Docker Usage Guide

This document describes how to build, run, and operate Project TALOS with Docker.
The container runs the headless FastAPI server on port 8001 and connects to a
host-side Ollama instance for 100% local, air-gapped inference.

---

## 1. Prerequisites

- **Docker Engine** (Linux) or **Docker Desktop** (Windows / macOS). Docker 24+ recommended.
- **Docker Compose v2** (the `docker compose` plugin, not the legacy `docker-compose`). Verify with `docker compose version`.
- **Ollama** running on the host, with the models you intend to use pulled, for example:
  ```bash
  ollama pull qwen2.5:14b
  ollama pull nomic-embed-text
  ```
- A `.env` file (copy `example.env` to `.env`). All keys are optional for local-only mode.

---

## 2. Quick Start (Docker Compose)

```bash
# 1. Prepare the environment file
cp example.env .env          # Linux / macOS
copy example.env .env        # Windows (PowerShell / cmd)

# 2. Build and start the API server in the background
docker compose up -d --build

# 3. Verify it is healthy
curl http://localhost:8001/api/v1/health

# 4. Follow the logs
docker compose logs -f talos

# 5. Stop (keeps volumes intact)
docker compose down
```

The API is reachable at `http://localhost:8001` (interactive docs at `/docs`).

---

## 3. Run Modes

### 3.1 Headless API server (default)

`docker compose up -d` runs the default entrypoint (uvicorn on port 8001). This is
the recommended mode for a long-running backend that other tools (MCP server, React
frontend, SYNAPSE) call over HTTP.

### 3.2 Interactive TUI / CLI

To use the full TALOS menu (search, analysis, DRL, and the autonomous research
process), override the entrypoint and run `talos.py` inside the container:

```bash
docker compose run --rm talos python talos.py
```

This opens the interactive `rich` menu, including option 9 (Autonomous Research
Process). Because the same volume mounts are applied, any papers found are written
to the host's `data/` directory.

---

## 4. Building and Running Without Compose

```bash
# Build the image
docker build -t talos:5.10.1 .

# Run the API server
docker run --rm -p 8001:8001 \
  --add-host=host.docker.internal:host-gateway \
  -v "$(pwd)/data:/app/data" \
  -v "$(pwd)/models:/app/models" \
  -v "$(pwd)/logs:/app/logs" \
  -v "$(pwd)/_profiles:/app/_profiles" \
  --env-file .env \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  talos:5.10.1

# Run the interactive TUI instead
docker run --rm -it \
  --add-host=host.docker.internal:host-gateway \
  -v "$(pwd)/data:/app/data" \
  -v "$(pwd)/models:/app/models" \
  -v "$(pwd)/logs:/app/logs" \
  -v "$(pwd)/_profiles:/app/_profiles" \
  --env-file .env \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  talos:5.10.1 python talos.py
```

On Windows PowerShell, replace `"$(pwd)/data:/app/data"` with
`"${PWD}/data:/app/data"`.

---

## 5. Connecting to Host Ollama (air-gapped / local-first)

The container cannot reach `127.0.0.1` on the host. Use `host.docker.internal`:

| Variable | Value in container | Purpose |
|----------|--------------------|---------|
| `OLLAMA_BASE_URL` | `http://host.docker.internal:11434` | Heavy reasoning tier (e.g. `qwen2.5:14b`) |
| `FAST_EDGE_BASE_URL` | `http://host.docker.internal:11435/v1` | Fast edge tier (e.g. `Neutrino-8B`) |
| `LOCAL_MODEL_BASE_URL` | `http://host.docker.internal:11434/v1` | Local provider (OpenAI-compatible) |
| `TALOS_EXECUTION_MODE` | `local` | `local` / `hybrid` / `cloud` |

These are pre-configured in `docker-compose.yml`. If Ollama runs on another host or
port, override them in `.env` or edit `docker-compose.yml`.

- **Windows / macOS:** `host.docker.internal` resolves automatically.
- **Linux:** it requires `extra_hosts: host.docker.internal:host-gateway`, which is
  already present in `docker-compose.yml`.

---

## 6. Persistent Volumes

The following host directories are mounted into the container so data survives
rebuilds and container removal:

| Host path | Container path | Purpose |
|-----------|----------------|---------|
| `./data` | `/app/data` | SQLite database (`talos_research.db`) and reports |
| `./models` | `/app/models` | Trained DRL models (`dddqn_trained.pth`) and GWO results |
| `./logs` | `/app/logs` | Daily daemon reports and logs |
| `./_profiles` | `/app/_profiles` | Per-topic research profiles (isolated DBs and configs) |

---

## 7. Healthcheck and Monitoring

- The image defines a `HEALTHCHECK` that polls `/api/v1/health` every 30 seconds.
- Check status: `docker inspect --format '{{.State.Health.Status}}' talos_api`
- The endpoint returns database statistics and embedding-model coverage.

---

## 8. Updating / Rebuilding

```bash
git pull
docker compose up -d --build
# docker compose down -v   # only if you want to reset volumes (DESTRUCTIVE)
```

---

## 9. Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `env file ... not found` | `.env` is missing | `cp example.env .env` |
| Ollama connection refused | container uses `127.0.0.1` | use `host.docker.internal` URLs |
| Port 8001 already in use | another TALOS / SYNAPSE process | `docker compose down`, or change the `ports` mapping |
| No GPU / CUDA is not used | image is CPU-only by design | run Ollama on the host with the GPU; the container only talks HTTP to it |
| Build is slow | the `torch` wheel is large | it is cached after the first build |

---

## 10. Environment Variables (complete list)

See `example.env` for the full commented list. The most relevant for Docker are:

- `TALOS_EXECUTION_MODE` -- `local` (air-gapped), `hybrid`, or `cloud`.
- `TALOS_USE_LOCAL=1` -- force local Ollama only (no cloud fallback).
- `TALOS_API_PORT` -- API port (8001).
- `OLLAMA_BASE_URL`, `FAST_EDGE_BASE_URL`, `LOCAL_MODEL_BASE_URL` -- model endpoints.
- `GEMINI_API_KEY`, `DEEPSEEK_API_KEY`, `HF_TOKEN` -- optional cloud providers.
- `SYNAPSE_BUS_URL` -- SYNAPSE event bus (runs on the host, port 8000).
