#!/usr/bin/env bash
set -euo pipefail

# -----------------------------
# Defaults (can be overridden)
# -----------------------------
REPLAY_ROOT="data/samples/replay_min"
FRAMES="20"
CONFIG_PATH="configs/pipeline.yaml"
TASK="traffic_light"  # 默认任务

# 如果提供了第四个参数，就覆盖 TASK
if [ $# -ge 1 ]; then
    TASK="$1"
fi

echo "[run_replay] config=$CONFIG_PATH"
echo "[run_replay] task=$TASK"
echo "[run_replay] frames=$FRAMES"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT/src:${PYTHONPATH:-}"
echo "[run_replay] repo_root=$ROOT"
echo "[run_replay] replay_root=$REPLAY_ROOT"

# -----------------------------
# Prepare output dirs
# -----------------------------
mkdir -p logs/overlay logs/metrics logs/profile
rm -f logs/overlay/* logs/metrics/* logs/profile/* 2>/dev/null || true
touch logs/overlay/.gitkeep logs/metrics/.gitkeep logs/profile/.gitkeep 2>/dev/null || true

# -----------------------------
# Choose python entrypoint
# -----------------------------
PYTHON_BIN="${PYTHON_BIN:-python3}"

# -----------------------------
# Command
# -----------------------------
CMD=(
    "$PYTHON_BIN" -m perception_stack.main
    --mode replay
    --replay_root "$REPLAY_ROOT"
    --frames "$FRAMES"
    --config "$CONFIG_PATH"
    --task "$TASK"
)

echo "[run_replay] cmd: ${CMD[*]}"
"${CMD[@]}"

# -----------------------------
# Basic sanity checks
# -----------------------------
overlay_count=$(find logs/overlay -maxdepth 1 -type f ! -name ".gitkeep" | wc -l || true)
metrics_count=$(find logs/metrics -maxdepth 1 -type f ! -name ".gitkeep" | wc -l || true)

echo "[run_replay] outputs:"
echo "  overlay_count=$overlay_count"
echo "  metrics_count=$metrics_count"

if [ "$overlay_count" -lt 1 ]; then
  echo "[run_replay] ERROR: no overlay generated"
  exit 1
fi

if [ "$metrics_count" -lt 1 ]; then
  echo "[run_replay] ERROR: no metrics json generated"
  exit 1
fi

exit 0