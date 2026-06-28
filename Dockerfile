# ─────────────────────────────────────────────────────────────────────────────
# Dockerfile
# Oota India Urban Concierge — Multi-stage Docker build
# Stage 1 installs dependencies; Stage 2 builds the lean runtime image.
# ─────────────────────────────────────────────────────────────────────────────

# ── Stage 1: Builder ──────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

# Copy only the project manifest so Docker caches the layer until it changes
COPY pyproject.toml .

# Upgrade pip then install the project and all its dependencies into /build/deps
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e . --target /build/deps

# ── Stage 2: Final runtime image ──────────────────────────────────────────────
FROM python:3.12-slim

LABEL org.opencontainers.image.title="Oota India Urban Concierge" \
      org.opencontainers.image.description="Privacy-first AI concierge for Indian cities" \
      org.opencontainers.image.version="0.1.0"

WORKDIR /app

# Copy installed packages from the builder stage
COPY --from=builder /build/deps /usr/local/lib/python3.12/site-packages

# Copy the full application source
COPY . .

# Create runtime directories that must exist before the app starts
RUN mkdir -p \
        data/chroma \
        data/documents \
        .agents/skills/auto \
        .agents/skills/.archive

# Expose the FastAPI / uvicorn port
EXPOSE 8000

# Health-check: curl the /health endpoint every 30 s
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" \
    || exit 1

# Default command — main.py reads WEBHOOK_MODE, TELEGRAM_BOT_TOKEN, etc. from env
CMD ["python", "main.py"]
