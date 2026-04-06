# 在 CAM_PERCEPTION 仓库中接入 ROS 2
smile~
说明如何编译 `ros2/src/cam_perception_bridge`、发布 **`vision_msgs/msg/Detection2DArray`**，以及让节点加载仓库内的 `perception_stack`（**WSL + Python 虚拟环境**与单机 Ubuntu 相同思路）。

---

## 1. 依赖

- **ROS 2**（下文以 **Humble** 为例）。
- `sudo apt install ros-humble-vision-msgs`（或已装 `ros-humble-desktop`）。
- 与离线推理**同一套** venv：`requirements.txt`（含 ONNX / PyTorch / ultralytics 等）。

---


## 2. 仓库布局

```text
CAM_PERCEPTION/
  src/perception_stack/           # 感知管线（非 ROS 包）
  ros2/src/cam_perception_bridge/ # ament_python 包
```

运行时会把 **`CAM_PERCEPTION_ROOT/src`** 加入 `sys.path`。若推断失败，请设置 **`CAM_PERCEPTION_ROOT`** 或参数 **`cam_perception_root`**。

---

## 3. 工作空间与编译（venv 中的 Python）

推理依赖装在 venv 里时，应让 **`cam_perception_node` 入口脚本的 shebang 指向该 venv**（`ament_python` 在 `colcon build` 时用当前 `python3` 生成，勿手改 `install/`）。

```bash
# 示例路径请按本机修改
export REPO=/home/yuhe/workspace/CAM_PERCEPTION
export WS=~/ros2_ws/cam_perception

mkdir -p "$WS/src"
ln -sf "$REPO/ros2/src/cam_perception_bridge" "$WS/src/cam_perception_bridge"

source ~/venvs/cam_perception/bin/activate
which python3   # 应为 .../venvs/.../bin/python3

bash "$REPO/scripts/build_cam_perception_bridge.sh" "$WS"
source /opt/ros/humble/setup.bash
source "$WS/install/setup.bash"
```

若 **`which python3` 仍是 `/usr/bin/python3`**，入口脚本会缺包：请在 venv 内 `pip install colcon-common-extensions`，并用 **`which colcon` 指向 venv** 后再 `colcon build`。

---

## 4. 端到端验证摘要（已跑通示例）

以下对应 **WSL + venv** 下「编译 → 终端 A 跑节点 → 终端 B 看话题」的完整链路。

### 4.1 确认感知代码在 venv 中可导入

```bash
cd /home/yuhe/workspace/CAM_PERCEPTION
source ~/venvs/cam_perception/bin/activate
export PYTHONPATH="$PWD/src:${PYTHONPATH:-}"
python3 -c "from perception_stack.pipeline import load_cfg; print('ok', load_cfg('configs/pipeline.yaml')['enabled_tasks'])"
```

期望类似：`ok ['traffic_light', 'traffic_sign']`。

### 4.2 终端 A：启动节点（发布端）

```bash
source /opt/ros/humble/setup.bash
source ~/ros2_ws/cam_perception/install/setup.bash
source ~/venvs/cam_perception/bin/activate
export CAM_PERCEPTION_ROOT=/home/yuhe/workspace/CAM_PERCEPTION

ros2 run cam_perception_bridge cam_perception_node \
  --ros-args \
  -p source:=replay \
  -p task:=traffic_light \
  -p pipeline_config:=configs/pipeline.yaml \
  -p replay_root:=data/samples/replay_min \
  -p publish_topic:=/camera_perception/detections \
  -p timer_period_s:=0.2
```

- **`replay`**：循环读取 **`$CAM_PERCEPTION_ROOT/<replay_root>/cam_test/`** 下 `.png` / `.jpg`，无需摄像头。
- 成功时日志示例：加载 `models/tl.onnx`、周期性 **`Published detections=N`**（`N` 随画面可为 0 或正整数）。

### 4.3 终端 B：验证话题

```bash
source /opt/ros/humble/setup.bash
source ~/ros2_ws/cam_perception/install/setup.bash

ros2 topic list
```

期望包含 **`/camera_perception/detections`**（另常见 `/parameter_events`、`/rosout`）。

进一步：

```bash
ros2 topic info /camera_perception/detections
ros2 topic echo /camera_perception/detections --once
```

- **类型**：`vision_msgs/msg/Detection2DArray`
- **`echo`**：`detections` 数组在有目标时非空；与终端 A 的 `Published detections=N` 一致。

---

## 5. 节点参数

| 参数 | 含义 |
|------|------|
| `cam_perception_root` | 仓库根；默认用 `CAM_PERCEPTION_ROOT` 或从安装路径推断 |
| `pipeline_config` | 相对仓库根，默认 `configs/pipeline.yaml` |
| `task` | `traffic_light` 或 `traffic_sign` |
| `source` | `replay`：读图；`live`：摄像头（WSL 需设备可用） |
| `replay_root` | 相对仓库根，默认 `data/samples/replay_min` |
| `camera` | `live` 时设备，如 `0`；空则用 `pipeline.yaml` 的 `capture.device` |
| `publish_topic` | 默认 `/camera_perception/detections` |
| `timer_period_s` | 定时节拍（秒） |
| `max_frames` | `>0` 时仅处理有限帧（调试） |

**Launch**：`ros2 launch cam_perception_bridge perception.launch.py cam_perception_root:=<REPO> source:=replay`

---

## 6. 消息字段（`Detection2DArray`）

- `header`：`frame_id` 与配置中 `capture.frame_id` 一致。
- 每条 `Detection2D`：`bbox`（像素框）、`results` 中 `class_id` / `score`、`id`（跟踪 ID）。

---

## 7. 故障排除

| 现象 | 处理 |
|------|------|
| `Cannot find CAM_PERCEPTION repo` | `export CAM_PERCEPTION_ROOT=...` 或 `-p cam_perception_root:=...` |
| `Config not found` | 确认路径相对仓库根；`CAM_PERCEPTION_ROOT` 指向仓库根 |
| 节点 `ModuleNotFoundError`（如 ultralytics） | 用 venv 的 `python3` 参与编译；见第 3 节 |
| `source .../setup.bash: AMENT_TRACE_SETUP_FILES: unbound variable` | 当前 shell 启用了 `set -u` 时可能出现；新开终端或使用 `set +u` 后再 `source` ROS |
| `vision_msgs` 导入失败 | `sudo apt install ros-humble-vision-msgs` |
| 无检测 / 始终空列表 | 查 `models/` 与 `configs/models.yaml`；`cam_test` 是否有图 |

离线回放与相机说明见 [CAMERA_LIVE_USAGE.md](./CAMERA_LIVE_USAGE.md)。
