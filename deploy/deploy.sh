#!/usr/bin/env bash
# Construit, pousse et déploie les images Checkeo sur Nomad.
#   deploy/deploy.sh [frontend|backend|database|all] [--no-run]
set -euo pipefail

REGISTRY="${REGISTRY:-registry.enopt.ovh:80}"
export NOMAD_ADDR="${NOMAD_ADDR:-http://192.168.1.21:4646}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TAG="$(git -C "$ROOT" rev-parse --short HEAD)"
if [ -n "$(git -C "$ROOT" status --porcelain)" ]; then TAG="$TAG-dirty"; fi

target="${1:-all}"
run=1
[ "${2:-}" = "--no-run" ] && run=0

deploy() {
  local name="$1" image="$REGISTRY/checkeo-$1"
  echo "==> $name : $image:$TAG"
  docker build -f "$ROOT/deploy/$name/Dockerfile" -t "$image:$TAG" -t "$image:latest" "$ROOT"
  docker push "$image:$TAG"
  docker push "$image:latest"
  if [ "$run" = 1 ]; then
    nomad job run -var "image=$image:$TAG" "$ROOT/deploy/$name.nomad.hcl"
  fi
}

case "$target" in
  frontend|backend|database) deploy "$target" ;;
  all) for t in database backend frontend; do deploy "$t"; done ;;
  *) echo "usage: $0 [frontend|backend|database|all] [--no-run]" >&2; exit 2 ;;
esac
