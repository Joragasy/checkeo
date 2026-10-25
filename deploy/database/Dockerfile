# Ingestion des données SNCF et interface web DuckDB. Contexte de build : racine du dépôt.
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.8.22 /uv /usr/local/bin/uv
RUN apt-get update && apt-get install -y --no-install-recommends socat && rm -rf /var/lib/apt/lists/*

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PROJECT_ENVIRONMENT=/opt/venv
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY backend/checkeo ./checkeo
RUN uv sync --frozen --no-dev

ENV PATH=/opt/venv/bin:$PATH CHECKEO_DATA_DIR=/data
# Extension ui embarquée dans l'image (évite le téléchargement au démarrage).
RUN python -c "import duckdb; duckdb.connect().execute('INSTALL ui')"

COPY deploy/database/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh
EXPOSE 4214
CMD ["entrypoint.sh"]
