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

# Αντιγραφή όλου του κώδικα
COPY . .

# Περιβαλλοντικές μεταβλητές
ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=utf-8

# Εκκίνηση του μενού του TALOS
CMD ["python", "-u", "talos.py"]