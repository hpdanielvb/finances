#!/usr/bin/env bash
pkill -f "react-scripts start" 2>/dev/null || true
pkill -f "vite" 2>/dev/null || true
echo "[OK] Frontend parado"
