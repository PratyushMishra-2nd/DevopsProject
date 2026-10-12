# syntax=docker/dockerfile:1.7
# ---- build stage: resolve wheels into an isolated virtualenv ----
FROM python:3.12-slim-trixie AS build
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
RUN python -m venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt \
 && pip uninstall -y pip

# ---- runtime stage: no compilers, no pip, non-root ----
FROM python:3.12-slim-trixie AS runtime
ARG GIT_SHA=unknown
LABEL org.opencontainers.image.title="pantrypulse-backend" \
      org.opencontainers.image.description="PantryPulse FastAPI service" \
      org.opencontainers.image.authors="Pratyush Mishra" \
      org.opencontainers.image.source="https://github.com/PratyushMishra-2nd/DevopsProject" \
      org.opencontainers.image.revision="${GIT_SHA}"

# Pick up Debian security fixes released after the base image was built,
# drop pip from the system interpreter (the app runs from /opt/venv) and
# create an unprivileged user with a fixed numeric UID.
RUN apt-get update && apt-get upgrade -y --no-install-recommends \
 && rm -rf /var/lib/apt/lists/* \
 && (python -m pip uninstall -y pip setuptools wheel || true) \
 && groupadd --system --gid 10001 app \
 && useradd --system --uid 10001 --gid 10001 --no-create-home --home-dir /nonexistent --shell /usr/sbin/nologin app

ENV PATH=/opt/venv/bin:$PATH \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    GIT_SHA=${GIT_SHA}
WORKDIR /app
COPY --from=build /opt/venv /opt/venv
COPY alembic.ini ./
COPY alembic ./alembic
COPY app ./app
COPY --chmod=0755 docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh

# Numeric UID so Kubernetes runAsNonRoot can verify it without /etc/passwd.
USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=3s --start-period=20s --retries=3 \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"]
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
