# Use the official Playwright Python image — Chromium + ALL system dependencies
# are pre-installed and tested by Microsoft. This is the ONLY reliable way to
# run Playwright in Docker without fighting missing OS package errors.
#
# Version MUST match playwright==1.49.0 in requirements.txt.
# "jammy" = Ubuntu 22.04 LTS (officially supported by Playwright).
FROM mcr.microsoft.com/playwright/python:v1.49.0-jammy

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies.
# Note: playwright pip package is already in the base image; re-installing
# the pinned version from requirements.txt is safe — pip install does NOT
# re-download browsers (that's a separate `playwright install` step).
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Fix line endings for shell scripts (Windows CRLF → Unix LF)
RUN sed -i 's/\r//' entrypoint.sh && chmod +x entrypoint.sh

# Create logs directory
RUN mkdir -p logs

# Expose port (Railway sets $PORT dynamically; 8000 is the local dev default)
EXPOSE 8000

# Health check — polls /health (JSON 200) not / (which redirects)
HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Use shell form (not exec/JSON-array) so $PORT is expanded by the shell.
# exec form bypasses the shell → $PORT stays as the literal string "$PORT" → crash.
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
