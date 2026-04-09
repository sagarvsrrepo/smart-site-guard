#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ -f .env ]; then
  export $(grep -v '^[[:space:]]*#' .env | xargs)
fi

mkdir -p logs

if command -v nohup >/dev/null 2>&1; then
  echo "Starting dashboard..."
  cd dashboard
  nohup python app.py > "$SCRIPT_DIR/logs/dashboard.log" 2>&1 &
  echo $! > "$SCRIPT_DIR/logs/dashboard.pid"
  cd "$SCRIPT_DIR"

  echo "Starting fog processor..."
  cd fog
  nohup python processor.py > "$SCRIPT_DIR/logs/fog.log" 2>&1 &
  echo $! > "$SCRIPT_DIR/logs/fog.pid"
  cd "$SCRIPT_DIR"

  echo "Starting simulator..."
  cd simulator
  nohup python publisher.py > "$SCRIPT_DIR/logs/simulator.log" 2>&1 &
  echo $! > "$SCRIPT_DIR/logs/simulator.pid"
  cd "$SCRIPT_DIR"
else
  echo "nohup not found; starting processes in the background instead."
  echo "Starting dashboard..."
  (cd dashboard && python app.py > "$SCRIPT_DIR/logs/dashboard.log" 2>&1 &) 
  echo $! > "$SCRIPT_DIR/logs/dashboard.pid"

  echo "Starting fog processor..."
  (cd fog && python processor.py > "$SCRIPT_DIR/logs/fog.log" 2>&1 &)
  echo $! > "$SCRIPT_DIR/logs/fog.pid"

  echo "Starting simulator..."
  (cd simulator && python publisher.py > "$SCRIPT_DIR/logs/simulator.log" 2>&1 &)
  echo $! > "$SCRIPT_DIR/logs/simulator.pid"
fi

echo "All components started."
echo "Dashboard: http://localhost:5000"
echo "Logs: $SCRIPT_DIR/logs/dashboard.log, $SCRIPT_DIR/logs/fog.log, $SCRIPT_DIR/logs/simulator.log"
