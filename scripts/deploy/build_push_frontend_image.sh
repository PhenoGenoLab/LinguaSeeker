#!/usr/bin/env bash
# Build and push the frontend container image from a local machine.
#
# Run from anywhere inside the repo:
#   ./scripts/deploy/build_push_frontend_image.sh
#   ./scripts/deploy/build_push_frontend_image.sh --tag 20261111
#   VITE_BASE_PATH=/linguaseeker ./scripts/deploy/build_push_frontend_image.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

FRONTEND_IMAGE="${FRONTEND_IMAGE:-docker.io/lanshi47/lingua-seeker-frontend}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
LOCAL_TAG="${LOCAL_TAG:-lingua-seeker-frontend:local}"
VITE_BASE_PATH="${VITE_BASE_PATH:-/}"
PUSH_RETRIES="${PUSH_RETRIES:-3}"

PUSH_IMAGE=1

usage() {
    cat <<'USAGE'
Usage: scripts/deploy/build_push_frontend_image.sh [options]

Options:
  --image IMAGE       Frontend image repository. Default: docker.io/lanshi47/lingua-seeker-frontend
  --tag TAG           Image tag. Default: latest
  --local-tag TAG     Local image tag. Default: lingua-seeker-frontend:local
  --base-path PATH    Vite/nginx base path baked into the image. Default: /
  --retries N         Push retry count. Default: 3
  --no-push           Build only
  -h, --help          Show this help

Notes:
  Images are built on the local machine and pushed to Docker Hub.
  There is no cloud image-build workflow for this repository.
USAGE
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --image)
            FRONTEND_IMAGE="${2:?missing value for --image}"
            shift 2
            ;;
        --tag)
            IMAGE_TAG="${2:?missing value for --tag}"
            shift 2
            ;;
        --local-tag)
            LOCAL_TAG="${2:?missing value for --local-tag}"
            shift 2
            ;;
        --base-path)
            VITE_BASE_PATH="${2:?missing value for --base-path}"
            shift 2
            ;;
        --retries)
            PUSH_RETRIES="${2:?missing value for --retries}"
            shift 2
            ;;
        --no-push)
            PUSH_IMAGE=0
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "ERROR: unknown option: $1" >&2
            usage >&2
            exit 2
            ;;
    esac
done

REMOTE_REF="${FRONTEND_IMAGE}:${IMAGE_TAG}"

require_command() {
    local command_name="$1"
    if ! command -v "$command_name" >/dev/null 2>&1; then
        echo "ERROR: required command not found: $command_name" >&2
        exit 1
    fi
}

push_with_retries() {
    local ref="$1"
    local attempts="$2"
    local attempt=1
    local sleep_seconds

    while (( attempt <= attempts )); do
        echo "Pushing $ref (attempt $attempt/$attempts)..."
        if docker push "$ref"; then
            return 0
        fi

        if (( attempt == attempts )); then
            echo "ERROR: docker push failed after $attempts attempts: $ref" >&2
            return 1
        fi

        sleep_seconds=$(( attempt * 15 ))
        echo "Push failed; retrying in ${sleep_seconds}s..."
        sleep "$sleep_seconds"
        attempt=$(( attempt + 1 ))
    done
}

require_command docker
if [[ ! -f "$REPO_ROOT/frontend/Dockerfile" ]]; then
    echo "ERROR: missing frontend/Dockerfile" >&2
    exit 1
fi

if ! docker info >/dev/null 2>&1; then
    echo "ERROR: Docker daemon is not reachable." >&2
    exit 1
fi

echo "Frontend image: $REMOTE_REF"
echo "Local tag:      $LOCAL_TAG"
echo "Base path:      $VITE_BASE_PATH"
echo "Repo root:      $REPO_ROOT"
echo ""

cd "$REPO_ROOT"

DOCKER_BUILDKIT=1 docker build \
    -f frontend/Dockerfile \
    --build-arg "VITE_BASE_PATH=${VITE_BASE_PATH}" \
    -t "$LOCAL_TAG" \
    -t "$REMOTE_REF" \
    frontend

docker image inspect "$REMOTE_REF" \
    --format 'Built image: {{index .RepoTags 0}} id={{.Id}} size={{.Size}} created={{.Created}}'

if [[ "$PUSH_IMAGE" -eq 1 ]]; then
    push_with_retries "$REMOTE_REF" "$PUSH_RETRIES"
    echo "Pushed image: $REMOTE_REF"
    echo "Remote digest is printed by docker push above."
else
    echo "Skipping push because --no-push was set."
fi
