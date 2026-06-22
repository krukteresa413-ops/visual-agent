#!/bin/bash
# Restart uvicorn safely without killing the SSH session
set -e
cd /opt/visual-agent/app/backend
source .venv/bin/activate

# Kill old uvicorn
pkill -f "uvicorn main:app" 2>/dev/null || true
sleep 2

# Start new
nohup .venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 > /tmp/uvicorn.log 2>&1 &
UVICORN_PID=$!
echo "Started uvicorn PID=$UVICORN_PID"

# Wait for health
for i in $(seq 1 10); do
  sleep 1
  if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    echo "HEALTHY after ${i}s"
    curl -s http://localhost:8000/health
    exit 0
  fi
done
echo "FAILED to start"
cat /tmp/uvicorn.log | tail -20
exit 1
