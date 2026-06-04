# ─── Stage 1: Builder ────────────────────────────────────────────
# Install dependencies in a separate stage so the final image is lean
FROM python:3.11-slim AS builder

WORKDIR /app

# Install system deps needed for compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first (Docker cache layer optimisation)
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt


# ─── Stage 2: Production ─────────────────────────────────────────
FROM python:3.11-slim AS production

WORKDIR /app

# Security: never run as root in production
RUN groupadd --gid 1001 appgroup && \
    useradd --uid 1001 --gid appgroup --no-create-home appuser

# Copy installed packages from builder stage
COPY --from=builder /root/.local /home/appuser/.local

# Copy application code
COPY --chown=appuser:appgroup . .

# Streamlit config — disable telemetry, set server options
RUN mkdir -p /home/appuser/.streamlit
COPY --chown=appuser:appgroup .streamlit/config.toml /home/appuser/.streamlit/config.toml

# Switch to non-root user
USER appuser

# Ensure local pip packages are on PATH
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Health check — Streamlit exposes on 8501
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')"

EXPOSE 8501

# Use exec form — signals reach the process directly (clean shutdown)
ENTRYPOINT ["python", "-m", "streamlit", "run", "app.py", \
    "--server.port=8501", \
    "--server.address=0.0.0.0", \
    "--server.headless=true", \
    "--browser.gatherUsageStats=false"]
