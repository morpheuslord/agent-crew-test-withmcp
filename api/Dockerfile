# syntax=docker/dockerfile:1

# ---- build: resolve the locked dependencies into a virtualenv -------------------------------
FROM python:3.13.13-slim-trixie AS build
COPY --from=ghcr.io/astral-sh/uv:0.11.21 /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/opt/venv
WORKDIR /src
# Dependencies first (cached layer), installed exactly as locked.
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project
COPY src ./src
RUN uv sync --frozen --no-dev --no-editable

# ---- runtime: no build tools, no package manager caches, non-root -------------------------
FROM python:3.13.13-slim-trixie AS runtime
RUN groupadd --system --gid 10001 taskboard \
 && useradd --system --uid 10001 --gid taskboard --home-dir /app --shell /usr/sbin/nologin taskboard
ENV PATH=/opt/venv/bin:$PATH \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app
COPY --from=build /opt/venv /opt/venv
COPY alembic.ini ./
COPY migrations ./migrations
# Local attachment storage (development); the volume inherits this ownership.
RUN mkdir -p /data/attachments && chown 10001:10001 /data/attachments
USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=3s --start-period=20s --retries=3 \
  CMD ["python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=2).status == 200 else 1)"]
CMD ["uvicorn", "--factory", "taskboard.main:create_app", "--host", "0.0.0.0", "--port", "8000", "--no-server-header"]
