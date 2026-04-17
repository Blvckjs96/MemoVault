FROM python:3.12-slim

WORKDIR /app

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy project files
COPY pyproject.toml README.md ./
COPY src/ src/

# Install dependencies
RUN uv pip install --system --no-cache .

# Create data directory
RUN mkdir -p /app/memovault_data

# Expose ports
EXPOSE 8080 8000

# Default: run REST API server
CMD ["memovault", "api", "--host", "0.0.0.0", "--port", "8080"]
