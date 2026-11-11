# Backend Host Compose Deployment Guide

Standard deployment procedure for `deploy/compose/backend-host/` — runs FastAPI + PostgreSQL + Redis on a single host.

## Prerequisites

| Requirement | Minimum |
|-------------|---------|
| OS | Linux (Debian/Ubuntu recommended) |
| Docker | 24+ with BuildKit |
| Docker Compose | v2 |
| Disk | 15 GB free (image ~6 GB, DB + logs) |
| GPU host | Separate machine running inference services (Embedding :8002, Rerank :8003, Doc-Parse :44321) |

## Directory Layout

```
deploy/compose/backend-host/
├── docker-compose.yml
├── .env                          # secrets & environment vars (git-ignored)
├── .env.example                  # template
├── config/
│   ├── production.yaml           # app config overrides (git-ignored)
│   ├── vault/
│   │   └── production.yaml       # secrets: DB password, LLM keys (git-ignored, 0600)
│   └── README.md
├── logs/                         # backend log output
├── data/                         # runtime data
├── downloads/                    # downloaded files
└── output/                       # generated reports
```

## Step-by-Step Deployment

### 1. Build and push the Docker image (on local machine)

Images are built locally and pushed to Docker Hub. Do not use GitHub Actions for image builds.

```bash
# From repo root — prepare docker-artifacts/, build, smoke-test, push
cd backend
uv sync --no-dev --frozen
mkdir -p ../docker-artifacts
tar czf ../docker-artifacts/site-packages.tar.gz \
  --exclude='__pycache__' --exclude='*.pyc' --dereference \
  -C .venv/lib/python3.12/site-packages .
tmp=$(mktemp -d)
cp -P .venv/bin/* "$tmp"/ 2>/dev/null || true
rm -f "$tmp"/python* 2>/dev/null || true
sed -i "s|$(pwd)/.venv/bin/python3|/opt/venv/bin/python3|g" "$tmp"/* 2>/dev/null || true
tar czf ../docker-artifacts/venv-bin.tar.gz -C "$tmp" .
rm -rf "$tmp"
cd ..

./scripts/deploy/build_push_backend_image.sh --tag latest
# optional: ./scripts/deploy/build_push_backend_image.sh --tag 20261111
```

Default remote image: `docker.io/lanshi47/lingua-seeker-backend:<tag>`.

### 2. Pull image on the server

```bash
# On server (public Docker Hub repo needs no login)
cd /path/to/project/deploy/compose/backend-host
IMAGE_TAG=latest docker compose --env-file .env pull
```

### 3. Prepare config files (on server)

```bash
cd /path/to/project/deploy/compose/backend-host

# Create .env from template
cp .env.example .env
# Edit .env — set POSTGRES_PASSWORD, API_KEY, inference URLs, etc.
vi .env

# Create app config from templates
cp ../../../backend/config/environments/production.yaml.example config/production.yaml
cp ../../../backend/config/vault/production.yaml.example config/vault/production.yaml

# Edit configs for the server environment
vi config/production.yaml
vi config/vault/production.yaml
```

### 4. Set file permissions

The container runs as user `deploy` (UID 1000). All host-mounted paths must be readable by this user.

```bash
# Config files — UID 1000 needs read access
setfacl -m u:1000:r config/production.yaml config/vault/production.yaml

# Volume directories — UID 1000 needs read+write
chown 1000:1000 logs data downloads output
```

> **Why `setfacl` instead of `chown`?** Config files are owned by root and mounted read-only. `setfacl` grants read access to UID 1000 without changing ownership. Volume directories need `chown` because the container writes to them.

### 5. Start the stack

```bash
docker compose -f deploy/compose/backend-host/docker-compose.yml \
  --env-file deploy/compose/backend-host/.env \
  up -d --build
```

This starts 3 containers: `postgres`, `redis`, `backend`. The backend waits for both datastores to be healthy before starting.

### 6. Run database migrations

The database starts empty. Run Alembic migrations to create the schema:

```bash
# Pre-create the alembic_version table with wide column (VARCHAR(128))
# to avoid truncation errors on long revision IDs.
docker exec -it backend-host-postgres-1 \
  psql -U lingua_seeker -d lingua_seeker -c "
    CREATE SCHEMA IF NOT EXISTS lingua;
    CREATE TABLE IF NOT EXISTS lingua.alembic_version (
      version_num VARCHAR(128) NOT NULL
    );
  "

# Copy migration scripts into the container
docker cp database backend-host-backend-1:/database

# Run migrations
docker exec -it backend-host-backend-1 \
  /opt/venv/bin/alembic -c /database/alembic.ini upgrade head
```

> **Why pre-create `alembic_version`?** Alembic defaults to `VARCHAR(32)` for the version column, but some revision IDs exceed 32 characters. Pre-creating with `VARCHAR(128)` prevents `StringDataRightTruncationError`.

### 7. Verify

```bash
# Check container status
docker compose -f deploy/compose/backend-host/docker-compose.yml \
  --env-file deploy/compose/backend-host/.env ps

# Check backend logs
docker compose -f deploy/compose/backend-host/docker-compose.yml \
  --env-file deploy/compose/backend-host/.env logs backend --tail 30

# Health check
curl http://127.0.0.1:8000/health
```

Expected log output:
```
Starting Lingua Seeker backend (env=production)
Pipeline orchestrator initialized
Job dispatcher started
Startup connectivity check passed
Application startup complete.
```

## Common Operations

### Restart backend only

```bash
docker compose -f deploy/compose/backend-host/docker-compose.yml \
  --env-file deploy/compose/backend-host/.env restart backend
```

### View live logs

```bash
docker compose -f deploy/compose/backend-host/docker-compose.yml \
  --env-file deploy/compose/backend-host/.env logs -f backend
```

### Rebuild after code changes

```bash
docker compose -f deploy/compose/backend-host/docker-compose.yml \
  --env-file deploy/compose/backend-host/.env up -d --build
```

### Run new migrations after code update

```bash
# Re-copy migration scripts (they may have changed)
docker cp database backend-host-backend-1:/database

# Run migrations
docker exec -it backend-host-backend-1 \
  /opt/venv/bin/alembic -c /database/alembic.ini upgrade head
```

### Connect to PostgreSQL

```bash
docker exec -it backend-host-postgres-1 \
  psql -U lingua_seeker -d lingua_seeker
```

## Troubleshooting

### Container fails to start: `Permission denied`

| Mount path | Cause | Fix |
|------------|-------|-----|
| `/app/config/vault/production.yaml` | File owned by root, container runs as UID 1000 | `setfacl -m u:1000:r config/vault/production.yaml` |
| `/logs/...` | Volume directory owned by root | `chown 1000:1000 logs data downloads output` |

### Docker build fails: `COPY docker-artifacts/... not found`

The `.dockerignore` must whitelist `docker-artifacts/`:

```
docker-artifacts
!docker-artifacts/*
```

### Docker build fails: `/opt/venv/bin/python: not found`

The venv-bin tarball overwrites Python symlinks with host-specific paths. The Dockerfile includes a symlink restoration step — if it's missing, add:

```dockerfile
RUN ln -sf /usr/local/bin/python3 /opt/venv/bin/python3 \
 && ln -sf python3 /opt/venv/bin/python \
 && ln -sf /usr/local/bin/python3 /opt/venv/bin/python3.12
```

### Migration fails: `value too long for type character varying(32)`

Pre-create the `alembic_version` table with a wider column before running Alembic (see Step 6).

### Container crash-loops after config file re-copy

Re-set permissions — `docker cp` and `cp` reset file ownership to root:

```bash
setfacl -m u:1000:r config/production.yaml config/vault/production.yaml
```

## Architecture Notes

- **Build context**: Repo root (`context: ../../../`), not `backend/`. The `.dockerignore` controls what enters the context.
- **Image**: Single-stage, ~6 GB. Pre-built venv from CI artifacts (`docker-artifacts/`), no pip install at build time.
- **Container user**: `deploy` (UID 1000). Never runs as root.
- **Config priority**: defaults → environment YAML → vault YAML → env vars (highest).
- **Inference services**: External Docker containers (Embedding/Rerank/Doc-Parse), not managed by this compose file.
