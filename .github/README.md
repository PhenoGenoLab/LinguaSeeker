# GitHub Actions

> CI pipeline for lint/test. Container images are built on a local machine and
> pushed to Docker Hub — not built in GitHub Actions.

```
push to dev / master / release/**
        │
        ├──► ci.yml                 ──► backend ruff lint, frontend lint + type-check + test, rust test
        │
        └──► config-validation.yml ──► cross-service config consistency check

local machine (not CI)
        │
        └──► scripts/deploy/build_push_*.sh ──► docker.io/lanshi47/lingua-seeker-{backend,frontend}:<tag>

manual (optional)
        └──► deploy.yml ──► SSH to backend host: docker compose pull && up -d
```

## Workflows

| File | Trigger | Purpose |
|------|---------|---------|
| `.github/workflows/ci.yml` | push / PR | Backend lint (ruff), frontend lint + type-check + test (vitest), rust test |
| `.github/workflows/config-validation.yml` | push / PR touching config files | Cross-service configuration consistency validation across environments |
| `.github/workflows/deploy.yml` | manual only | SSH to backend host, `docker compose pull && up -d` from Docker Hub |

## Image Build And Push (local)

Build on a developer machine, then push to Docker Hub:

```bash
# Backend (requires docker-artifacts/*.tar.gz first; see scripts/README.md)
./scripts/deploy/build_push_backend_image.sh
./scripts/deploy/build_push_backend_image.sh --tag 20261111

# Frontend
./scripts/deploy/build_push_frontend_image.sh
./scripts/deploy/build_push_frontend_image.sh --tag 20261111
```

Default repositories:

| Image | Docker Hub |
|-------|------------|
| Backend | `docker.io/lanshi47/lingua-seeker-backend` |
| Frontend | `docker.io/lanshi47/lingua-seeker-frontend` |

Compose stacks pull these images. There is no cloud image-build workflow.

## Required Secrets / Environments

### Environment-level (`production` / `staging`)

> Create each in repo Settings > Environments. Place secrets in the environment, not at repo level, so you can add required reviewers for production deploys.

| Secret | Description |
|--------|-------------|
| `BACKEND_HOST` | Public / VPN address of the backend host |
| `BACKEND_USER` | SSH user on the backend host (needs `docker compose` permission) |
| `BACKEND_SSH_KEY` | Private key (PEM, no passphrase). Issue a dedicated deploy key; lock `authorized_keys` with `command=`. |

> Default SSH port is 22. For non-standard ports, add `port: ${{ secrets.BACKEND_PORT }}` to the `appleboy/ssh-action` step.

Public Docker Hub images do not need a pull token on the deploy host. If a repository is private, run `docker login` once on the host.

## Deploy Host Preparation

```bash
# 1. Install docker + compose v2 (omitted)

# 2. Clone repo to a fixed path (deploy.yml defaults to /opt/lingua-seeker; change via DEPLOY_ROOT)
sudo install -d -o "$USER" -g "$USER" /opt/lingua-seeker
git clone <repo-url> /opt/lingua-seeker

# 3. Fill in the .env for this host (not version-controlled)
cd /opt/lingua-seeker/deploy/compose/backend-host
cp .env.example .env  &&  vim .env

# 4. Mount config files
mkdir -p config/vault
cp ../../../backend/config/environments/production.yaml.example config/production.yaml
cp ../../../backend/config/vault/production.yaml.example         config/vault/production.yaml
chmod 600 config/vault/production.yaml

# 5. Allow the deploy user to run docker without sudo (add to docker group, re-login)
sudo usermod -aG docker $USER
```

> The automated deploy pipeline only does `git fetch && checkout origin/<branch> && docker compose pull && up -d`. It does **not** modify `.env` or mounted secrets.

## Trigger Modes

### CI (every push / PR)

- `ci.yml` runs ruff lint, mypy and pytest on the backend plus ESLint + TypeScript type-check + vitest on the frontend. The Rust extension is the published `rust-io` wheel, so there is no cargo job.

### Image publish (local only)

- Build and push with `scripts/deploy/build_push_backend_image.sh` / `build_push_frontend_image.sh`.
- Do not add a GitHub Actions job that builds or pushes container images.

### Manual Deploy / Rollback

GitHub > Actions > **deploy** > Run workflow:

| Input | Values |
|-------|--------|
| environment | `production` / `staging` |
| image_tag | e.g. `latest`, `20261111`, `v1.2.0` |

The deploy script includes migration and health checks:
- `docker compose exec backend uv run alembic upgrade head`, then `docker image prune -f`.

## Config Validation

`config-validation.yml` runs on PRs and pushes that touch configuration files. It validates configuration consistency across all environments, checking that backend config, Docker Compose, and Ansible inventories are aligned.

## Relationship with Ansible

- The Ansible deployment path (`deploy/ansible/`) is unaffected and is used for source-code + systemd bare-metal deployments.
- The GitHub Actions deployment path targets the Docker host topology using `deploy/compose/`.
- Both paths share the `backend/config/` configuration contract and the `X-API-Key` injection point. **Use only one path per machine** -- do not mix them.
