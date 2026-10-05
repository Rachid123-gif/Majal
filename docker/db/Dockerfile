# PostgreSQL 16 + PostGIS 3 + pgvector, multi-architecture (Apple Silicon and Intel).
# Built from the official postgres image, whose apt sources already include apt.postgresql.org.
FROM postgres:16-bookworm

RUN apt-get update \
    && apt-get install -y --no-install-recommends postgresql-16-postgis-3 postgresql-16-pgvector \
    && rm -rf /var/lib/apt/lists/*

COPY init/ /docker-entrypoint-initdb.d/
