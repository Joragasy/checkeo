# API FastAPI. Contexte de build : racine du dépôt.
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.8.22 /uv /usr/local/bin/uv

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PROJECT_ENVIRONMENT=/opt/venv
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY backend/checkeo ./checkeo
RUN uv sync --frozen --no-dev

ENV PATH=/opt/venv/bin:$PATH CHECKEO_DATA_DIR=/data
EXPOSE 8000
CMD ["uvicorn", "checkeo.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
