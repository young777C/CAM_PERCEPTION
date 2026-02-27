#!/usr/bin/env bash
set -euo pipefail

# -----------------------------
# Defaults (can be overridden)
# -----------------------------
REPLAY_ROOT="${1:-data/samples/replay_min}"
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
)

echo "[run_replay] cmd: ${CMD[*]}"
"${CMD[@]}"

# -----------------------------
# Basic sanity checks
# -----------------------------
echo "[run_replay] outputs:"
echo "  overlay_count=$(ls -1 logs/overlay 2>/dev/null | wc -l || true)"
echo "  metrics_count=$(ls -1 logs/metrics 2>/dev/null | wc -l || true)"

# You can tighten these once visualizer/publisher are implemented:
# e.g. require at least 1 overlay image and 1 metrics file.
exit 0
