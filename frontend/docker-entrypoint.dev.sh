#!/bin/sh
# Runs as root: docker-compose.dev.yml bind-mounts ./frontend:/app, and
# Docker Desktop's bind-mount layer presents everything under it as
# root-owned inside the container regardless of the image's build-time
# chown or of who created a given file — observed on .next (anonymous
# volume), node_modules (anonymous volume), and coverage/ (a plain
# subdirectory of the bind mount, e.g. `npm run test:coverage` failing
# with EACCES on lcov.info). Re-chown the whole tree at container start,
# then drop to the unprivileged appuser before exec'ing the actual command.
set -e

chown -R appuser:appgroup /app 2>/dev/null || true

exec su appuser -s /bin/sh -c 'exec "$0" "$@"' -- "$@"
