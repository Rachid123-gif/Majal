FROM python:3.12-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:0.12 /uv /uvx /bin/

# libexpat: needed by the GDAL library bundled with rasterio.
# pango/harfbuzz: PDF exports (WeasyPrint). EB Garamond (titles), Noto Sans and Noto Naskh
# Arabic (IBM Plex is not packaged in Debian: Noto Sans replaces it in the PDF).
RUN apt-get update \
    && apt-get install -y --no-install-recommends libexpat1 \
       libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0 \
       fonts-ebgaramond fonts-noto-core \
    && rm -rf /var/lib/apt/lists/*

ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_LINK_MODE=copy \
    PATH=/opt/venv/bin:$PATH \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project
COPY . .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
