#!/usr/bin/env bash
pkill -f "uvicorn api_shim:app" 2>/dev/null || true
lsof -ti :8010 -sTCP:LISTEN | xargs kill -9 2>/dev/null || true
echo "[OK] Backend parado (porta 8010 livre)"
