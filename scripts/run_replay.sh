#!/usr/bin/env bash
set -euo pipefail

# -----------------------------
# Defaults (can be overridden)
# -----------------------------
REPLAY_ROOT="${1:-data/samples/replay_min}"
CONFIG_PATH="${3:-configs/pipeline.yaml}"
echo "[run_replay] config=$CONFIG_PATH"
FRAMES="${2:-20}"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT/src:${PYTHONPATH:-}"
echo "[run_replay] repo_root=$ROOT"
echo "[run_replay] replay_root=$REPLAY_ROOT"
echo "[run_replay] frames=$FRAMES"

# -----------------------------
# Prepare output dirs
# -----------------------------
mkdir -p logs/overlay logs/metrics logs/profile
# Keep dirs but clean old outputs
rm -f logs/overlay/* logs/metrics/* logs/profile/* 2>/dev/null || true
touch logs/overlay/.gitkeep logs/metrics/.gitkeep logs/profile/.gitkeep 2>/dev/null || true

# -----------------------------
# Choose python entrypoint
# -----------------------------
PYTHON_BIN="${PYTHON_BIN:-python3}"

# -----------------------------
# TODO: Replace the command below with your real pipeline CLI
# -----------------------------
# Option A (module):
#   $PYTHON_BIN -m src.perception_stack.main --mode replay --replay_root "$REPLAY_ROOT" --frames "$FRAMES"
#
# Option B (file):
#   $PYTHON_BIN src/perception_stack/main.py --mode replay --replay_root "$REPLAY_ROOT" --frames "$FRAMES"
#
# If your args are different, only edit this ONE place.

# todo：客制化
CMD=(
  "$PYTHON_BIN"  "-m" "perception_stack.main"
  "--mode" "replay"
  "--replay_root" "$REPLAY_ROOT"
  "--frames" "$FRAMES"
  "--config" "$CONFIG_PATH"
)

echo "[run_replay] cmd: ${CMD[*]}"
"${CMD[@]}"

# -----------------------------
# Basic sanity checks
# -----------------------------
# Count only real files (exclude .gitkeep)
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
# You can tighten these once visualizer/publisher are implemented:
# e.g. require at least 1 overlay image and 1 metrics file.
exit 0
