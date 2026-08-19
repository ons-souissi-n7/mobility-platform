#!/bin/sh
# Runs as root: docker-compose.dev.yml bind-mounts ./backend:/app, and Docker
# Desktop's bind-mount layer presents everything under it as root-owned inside
# the container regardless of the build-time chown or of who created a given
# file — observed on .ruff_cache, .pytest_cache and coverage.xml. Re-chown at
# container start, then drop to the unprivileged appuser before exec'ing the
# actual command.
set -e

chown -R appuser:appgroup /app 2>/dev/null || true

exec su appuser -s /bin/sh -c 'exec "$0" "$@"' -- "$@"
