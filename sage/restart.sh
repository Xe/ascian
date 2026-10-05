#!/usr/bin/env bash
set -euo pipefail
root="$(cd -- "$(dirname -- "$0")/.." && pwd)"
realm="${SAGE_REALM_COMPOSE:-/home/xe/code/ffxi2adt/server/compose.yaml}"
python3 "$root/sage/probe_guard.py"
if [[ -d "$root/build/runtime-next" ]]; then
  # Existing mounts retain the old inode until Compose recreates the container.
  if [[ -d "$root/build/runtime" ]]; then
    mv "$root/build/runtime" "$root/build/runtime-previous-$(date +%s)"
  fi
  mv "$root/build/runtime-next" "$root/build/runtime"
fi
python3 "$root/sage/probe_guard.py"
docker compose -f "$realm" -f "$root/sage/compose.override.yaml" up -d --no-deps --force-recreate worldserver
