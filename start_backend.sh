#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/backend"
[ -d .venv ] && source .venv/bin/activate
exec uvicorn api_shim:app --env-file .env.local --host 127.0.0.1 --port 8010
