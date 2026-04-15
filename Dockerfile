# ============================================================
# Base image: python:3.11-slim-bookworm
# Explicitly pinned to Debian Bookworm (Debian 12).
#
# WHY NOT python:3.11-slim?
#   The untagged "slim" image recently moved to Debian Trixie (13).
#   Playwright doesn't recognise Trixie yet and falls back to Ubuntu
#   package lists, which reference ttf-unifont / ttf-ubuntu-font-family —
#   packages that DON'T EXIST on Debian. Build fails with exit code 100.
#
# WHY NOT playwright install --with-deps?
#   --with-deps runs apt-get using Playwright's internal OS-detection.
#   When the OS is unrecognised it falls back to Ubuntu lists → same crash.
#
# SOLUTION: Debian Bookworm IS officially supported by Playwright.
#   We manually install ONLY packages that exist in Bookworm repos,
#   then run `playwright install chromium` (no --with-deps).
#   This gives us full control and zero hidden apt failures.
# ============================================================
FROM python:3.11-slim-bookworm

# Prevent interactive prompts during apt-get
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# ── System dependencies for Chromium on Debian Bookworm ──────────────────
# These are the EXACT package names available in Bookworm repos.
# Notably ABSENT (Ubuntu-only, not needed for headless Chromium):
#   ✗ ttf-ubuntu-font-family  → Ubuntu package, doesn't exist on Debian
#   ✗ ttf-unifont             → renamed to fonts-unifont; skip — optional fonts only
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Utilities
    curl \
    ca-certificates \
    # Chromium core libs
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libglib2.0-0 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    # Fonts (Debian names — works on Bookworm)
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# ── Python dependencies ───────────────────────────────────────────────────
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# ── Playwright browser ────────────────────────────────────────────────────
# Install Chromium binary ONLY (no --with-deps: we already installed
# all deps above with the correct Bookworm package names).
RUN playwright install chromium

# ── Application code ──────────────────────────────────────────────────────
COPY . .

# Fix Windows CRLF line endings in shell scripts
RUN sed -i 's/\r//' entrypoint.sh && chmod +x entrypoint.sh

# Create logs directory
RUN mkdir -p logs

# ── Runtime ───────────────────────────────────────────────────────────────
EXPOSE 8000

# Healthcheck hits /health (returns JSON 200, no redirect)
HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Shell form: $PORT is expanded by sh at container start.
# JSON-array (exec) form would pass literal "$PORT" → uvicorn crash.
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
