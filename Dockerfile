FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies required by Playwright on Linux
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libc6 \
    libcairo2 \
    libcups2 \
    libdbus-1-3 \
    libexpat1 \
    libfontconfig1 \
    libgbm1 \
    libglib2.0-0 \
    libgpg-error0 \
    libgtk-3-0 \
    libharfbuzz0b \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libpixman-1-0 \
    libstdc++6 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxinerama1 \
    libxkbcommon0 \
    libxrandr2 \
    libxrender1 \
    libxss1 \
    libxtst6 \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies with pip upgrade first
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (CRITICAL for production)
# Note: System dependencies already installed via apt-get above
# Do NOT use --with-deps in Docker (causes build to hang)
RUN playwright install chromium

# Copy application code
COPY . .

# Fix line endings for shell scripts (critical when developed on Windows)
RUN sed -i 's/\r//' entrypoint.sh && chmod +x entrypoint.sh

# Create logs directory
RUN mkdir -p logs

# Expose port (Railway sets $PORT dynamically; 8000 is the local dev default)
EXPOSE 8000

# Health check — uses $PORT so it works on Railway too
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# IMPORTANT: Use shell form (not exec/JSON-array form) so that $PORT is
# expanded by the shell at container start time. Railway injects PORT as an
# env var; exec form bypasses the shell and passes the literal string "$PORT"
# to uvicorn — which causes: Error: Invalid value for '--port': '$PORT'
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
