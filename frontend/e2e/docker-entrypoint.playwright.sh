#!/bin/sh
# Runs as root: docker-compose.test.yml bind-mounts e2e/, playwright-report/
# and test-results/ over the image's build-time chown'd paths, so those
# mount points come back root-owned regardless of the Dockerfile's chown.
# Re-chown here, then drop to the unprivileged pwuser before exec'ing the
# actual test command.
set -e

chown -R pwuser:pwuser /app/e2e /app/playwright-report /app/test-results 2>/dev/null || true

exec su pwuser -s /bin/sh -c 'exec "$0" "$@"' -- "$@"
