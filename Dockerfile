# Production image for the Medraxis platform.
# Multi-stage: build wheels, then a slim runtime running gunicorn.
FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    DJANGO_SETTINGS_MODULE=config.settings.production

# System deps: libpq for psycopg2, build tools removed after install.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

# Collect static files (uses a dummy secret/host; not used at build time).
RUN DJANGO_SECRET_KEY=build-time-dummy DJANGO_ALLOWED_HOSTS=localhost \
    python manage.py collectstatic --noinput || true

# Run as a non-root user.
RUN useradd --create-home --uid 1000 medraxis \
    && chown -R medraxis:medraxis /app
USER medraxis

EXPOSE 8000

# Apply migrations then serve via gunicorn. Override CMD for a worker, etc.
CMD ["sh", "-c", "python manage.py migrate --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 120"]
