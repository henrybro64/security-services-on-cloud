FROM python:3.11-slim

WORKDIR /app

# Install nmap (for port scanning)
RUN apt-get update \
    && apt-get install -y --no-install-recommends nmap \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

ENV PYTHONUNBUFFERED=1 \
    PORT=8000

EXPOSE 8000

# Use shell form to allow PORT env var substitution
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
