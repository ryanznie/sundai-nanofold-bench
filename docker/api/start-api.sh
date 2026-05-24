#!/usr/bin/env bash
set -euo pipefail

cd /app
exec uv run uvicorn service.app:app --host 0.0.0.0 --port 8000
