FROM python:3.11-slim

WORKDIR /app

# Install system deps for Playwright and websocket-client
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget gnupg2 && \
    rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    playwright install chromium && \
    playwright install-deps

COPY backend/ .

EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
