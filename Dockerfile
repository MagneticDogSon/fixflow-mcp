FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY fastmcp_docs_server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY fastmcp_docs_server/ ./fastmcp_docs_server/

ENV PORT=10000
EXPOSE 10000

# Run using FastMCP native SSE transport (exposes /sse endpoint)
CMD ["sh", "-c", "python -m fastmcp_docs_server"]
