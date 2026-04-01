#!/usr/bin/env bash
set -euo pipefail
# 车端实时采集 + 检测（需可用摄像头或虚拟设备）
# 用法: ./scripts/run_live.sh [traffic_sign|traffic_light] [camera_device]
# 例: ./scripts/run_live.sh traffic_sign 0
#     ./scripts/run_live.sh traffic_sign /dev/video0

TASK="${1:-traffic_sign}"
CAM="${2:-}"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT/src:${PYTHONPATH:-}"

CMD=(python3 -m perception_stack.main --mode live --config configs/pipeline.yaml --task "$TASK")
if [[ -n "$CAM" ]]; then
  CMD+=(--camera "$CAM")
fi

echo "[run_live] ${CMD[*]}"
exec "${CMD[@]}"
