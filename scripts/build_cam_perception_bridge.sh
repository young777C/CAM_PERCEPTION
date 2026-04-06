#!/usr/bin/env bash
# 用「当前已激活的 venv」编译 cam_perception_bridge，使 install 里 cam_perception_node 的 shebang 尽量指向该 venv。
# 用法：
#   source ~/venvs/cam_perception/bin/activate
#   bash /path/to/CAM_PERCEPTION/scripts/build_cam_perception_bridge.sh ~/ros2_ws/cam_perception
set -euo pipefail

WS="${1:?第一个参数：ROS2 工作空间路径，例如 ~/ros2_ws/cam_perception}"
WS="$(cd "$WS" && pwd)"

if ! command -v python3 >/dev/null 2>&1; then
  echo "[build_cam_perception_bridge] ERROR: python3 不在 PATH" >&2
  exit 1
fi

PY="$(command -v python3)"
echo "[build_cam_perception_bridge] using python3=$PY"
if [[ "$PY" == "/usr/bin/python3" ]] || [[ "$PY" == "/bin/python3" ]]; then
  echo "[build_cam_perception_bridge] WARN: 当前 python3 是系统路径；若希望 shebang 指向 venv，请先: source .../venv/bin/activate" >&2
fi

if [[ ! -f /opt/ros/humble/setup.bash ]]; then
  echo "[build_cam_perception_bridge] WARN: 未找到 /opt/ros/humble/setup.bash，请按本机 ROS2 发行版修改脚本" >&2
else
  # ROS setup.bash 会引用可能未设置的变量（如 AMENT_TRACE_SETUP_FILES）；本脚本 set -u 会导致 source 失败
  set +u
  # shellcheck source=/dev/null
  source /opt/ros/humble/setup.bash
  set -u
fi

cd "$WS"
colcon build --packages-select cam_perception_bridge "$@"

NODE="$WS/install/cam_perception_bridge/lib/cam_perception_bridge/cam_perception_node"
if [[ -f "$NODE" ]]; then
  echo "[build_cam_perception_bridge] shebang:"
  head -n 1 "$NODE"
fi
