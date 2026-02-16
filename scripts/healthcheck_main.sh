#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "[1/4] Clean logs..."
rm -rf logs/overlay/* logs/metrics/* logs/profile/* 2>/dev/null || true
touch logs/overlay/.gitkeep logs/metrics/.gitkeep logs/profile/.gitkeep

echo "[2/4] Run replay smoke test..."
# 你后续可以替换为 run_replay.sh
python -m src.perception_stack.main --mode replay --frames 20

echo "[3/4] Check outputs..."
test -d logs/overlay
test -d logs/metrics

echo "[4/4] OK"
