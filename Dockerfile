FROM python:3.11-slim

# Install uv package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Configure uv to use a specific venv path
ENV UV_PROJECT_ENVIRONMENT=/app/.venv
ENV PATH="/app/.venv/bin:$PATH"
ENV UV_COMPILE_BYTECODE=1

# Copy dependency manifests
COPY pyproject.toml uv.lock ./

# Sync dependencies without dev packages
RUN uv sync --frozen --no-dev

# Copy the rest of the application
COPY . .

# Ensure necessary directories exist
RUN mkdir -p data/artifacts logs

# Expose port
EXPOSE 8000

# Start FastAPI app
CMD ["uv", "run", "python", "app/fast_api_app.py"]
