#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/frontend"
[ -f yarn.lock ] && exec yarn start || exec npm start
