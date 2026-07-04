# TALOS v5.3.0 — Docker image
# Χρησιμοποιούμε ελαφριά έκδοση Python 3.10
FROM python:3.10-slim

# Εγκατάσταση βασικών εργαλείων συστήματος
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Ορισμός φακέλου εργασίας
WORKDIR /app

# Αντιγραφή και εγκατάσταση απαιτήσεων (γίνεται πρώτο για caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir streamlit

# Αντιγραφή όλου του κώδικα
COPY . .

# Περιβαλλοντικές μεταβλητές
ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=utf-8

# Expose ports: Flask Dashboard (5000) + Streamlit GUI (8501)
EXPOSE 5000 8501

# ── Documentation Builder (NEW in v5.3.0) ──────────────────────────────────
# To generate docs, run:  python scripts/generate_docs.py
# NOTE: This requires Ollama running on the HOST machine.
# The container accesses it via host.docker.internal:11434 (see docker-compose.yml).
# Set OLLAMA_HOST=http://host.docker.internal:11434 in your .env if using Docker.

# Default: CLI menu. Use `docker-compose run --rm talos streamlit` for GUI.
# Override with: docker-compose run --rm -e TALOS_START_MODE=streamlit talos
CMD if [ "$TALOS_START_MODE" = "streamlit" ]; then \
        python -m streamlit run app.py --server.port 8501 --server.address 0.0.0.0; \
    elif [ "$TALOS_START_MODE" = "dashboard" ]; then \
        python scripts/interactive_dashboard.py; \
    else \
        python -u talos.py; \
    fi
