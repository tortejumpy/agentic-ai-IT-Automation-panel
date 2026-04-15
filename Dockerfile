FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install minimal system utilities needed before playwright
# (playwright install --with-deps will handle all browser-specific deps)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Install Playwright + ALL system browser dependencies in one step.
# --with-deps tells playwright to run apt-get and install every missing
# library that Chromium needs (libnss3, libnspr4, libgbm1, etc.).
# This is the ONLY reliable way to get a working browser on Debian/Ubuntu.
RUN playwright install --with-deps chromium

# Copy application code
COPY . .

# Fix line endings for shell scripts (critical when developed on Windows)
RUN sed -i 's/\r//' entrypoint.sh && chmod +x entrypoint.sh

# Create logs directory
RUN mkdir -p logs

# Expose port (Railway sets $PORT dynamically; 8000 is the local dev default)
EXPOSE 8000

# Health check — uses /health endpoint (JSON 200, no redirect)
HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# IMPORTANT: Use shell form (not exec/JSON-array form) so that $PORT is
# expanded by the shell at container start time. Railway injects PORT as an
# env var; exec form bypasses the shell and passes the literal string "$PORT"
# to uvicorn — which causes: Error: Invalid value for '--port': '$PORT'
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
