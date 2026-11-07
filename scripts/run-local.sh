#!/usr/bin/env bash
set -euo pipefail
project_root="$(cd "$(dirname "$0")/.." && pwd)"
if [ ! -f "$project_root/.env.personal" ]; then
  "$project_root/.venv/bin/python" "$project_root/scripts/create-personal-data-keys.py" "$project_root/.env.personal"
fi
set -a
source "$project_root/.env.personal"
set +a
cd "$project_root/backend"
../.venv/bin/python -m alembic upgrade head
../.venv/bin/python seed.py
ALLOW_MOCK_PAYMENTS="${ALLOW_MOCK_PAYMENTS:-true}" ../.venv/bin/python -m uvicorn main:app --host 127.0.0.1 --port 8000 &
api_pid=$!
web_pid=''
../.venv/bin/python notification_worker.py &
notification_pid=$!
cleanup() {
  kill "$api_pid" "$notification_pid" ${web_pid:+"$web_pid"} 2>/dev/null || true
}
trap cleanup EXIT INT TERM
cd "$project_root/frontend"
node node_modules/next/dist/bin/next start --hostname 127.0.0.1 --port 3000 &
web_pid=$!
wait -n "$api_pid" "$web_pid" "$notification_pid"
