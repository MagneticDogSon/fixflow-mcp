# Use Python 3.11 slim for a small, fast image
FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

WORKDIR /app

# Install build dependencies (needed for some python packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install project dependencies
COPY fastmcp_docs_server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the server code
COPY fastmcp_docs_server/ ./fastmcp_docs_server/

# Render sets the PORT environment variable automatically
ENV PORT=10000
EXPOSE 10000

# Start the server using uvicorn pointing to the ASGI 'app' in server.py
# This provides the best stability for Render's SSE handling
CMD ["sh", "-c", "uvicorn fastmcp_docs_server.server:app --host 0.0.0.0 --port ${PORT}"]
