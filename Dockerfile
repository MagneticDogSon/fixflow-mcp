# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=utf-8

# Set work directory
WORKDIR /app

# Install system dependencies (if any)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY fastmcp_docs_server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY fastmcp_docs_server/ ./fastmcp_docs_server/

# Set Python path to find the module
ENV PYTHONPATH=/app

# Expose the port FixFlow SSE will run on
EXPOSE 8000

# Command to run the SSE server
# Using -u for unbuffered output to see logs in real-time
CMD ["python", "-u", "fastmcp_docs_server/server.py", "sse"]
