# Production image for the Medraxis platform.
# Multi-stage: build wheels with full build tooling, then a slim runtime that
# installs only the prebuilt wheels and runtime libraries, so the final image
# never ships compilers/headers.
FROM python:3.11-slim AS builder

ENV PIP_NO_CACHE_DIR=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip wheel --wheel-dir /wheels -r requirements.txt


FROM python:3.11-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    DJANGO_SETTINGS_MODULE=config.settings.production

# Runtime-only libpq (no -dev headers, no compilers).
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
COPY --from=builder /wheels /wheels
RUN pip install --upgrade pip \
    && pip install --no-index --find-links=/wheels -r requirements.txt \
    && rm -rf /wheels

COPY . .

# Collect static files (uses a dummy secret/host; not used at build time).
RUN DJANGO_SECRET_KEY=build-time-dummy DJANGO_ALLOWED_HOSTS=localhost \
    python manage.py collectstatic --noinput || true

# Run as a non-root user.
RUN useradd --create-home --uid 1000 medraxis \
    && chown -R medraxis:medraxis /app
USER medraxis

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request, sys; \
sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/docs/', timeout=3).status == 200 else 1)"

# Apply migrations then serve via gunicorn. Override CMD for a worker, etc.
CMD ["sh", "-c", "python manage.py migrate --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 120"]
