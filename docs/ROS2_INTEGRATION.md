# 在 CAM_PERCEPTION 仓库中接入 ROS 2

本文说明如何编译 `ros2/src/cam_perception_bridge` 包、发布 **`vision_msgs/Detection2DArray`**，以及如何让节点找到本仓库里的 `perception_stack` Python 代码。

---

## 1. 依赖

- 已安装 **ROS 2**（文档以 **Humble** 为例；Jazzy 等需自行核对包名）。
- 系统包：`ros-humble-vision-msgs`、`ros-humble-rclpy` 等（通过 `apt` 安装 `ros-humble-desktop` 或最小集即可）。
- 本仓库的 Python 依赖（`requirements.txt`）：OpenCV、PyTorch/ONNX 推理栈等，需与 `perception_stack` 一致。

---

## 2. 包在仓库中的位置

```text
CAM_PERCEPTION/
  src/perception_stack/          # 感知管线（非 ROS 包）
  ros2/src/cam_perception_bridge/ # ament_python ROS 2 包
    package.xml
    setup.py
    launch/perception.launch.py
    cam_perception_bridge/perception_node.py
```

节点在运行时把 **`仓库根目录/src`** 加入 `sys.path`，从而 `import perception_stack`。若安装路径下无法自动找到仓库根目录，需设置 **`CAM_PERCEPTION_ROOT`** 或参数 **`cam_perception_root`**（见下文）。

---

## 3. 编译

在**独立工作空间**中把本仓库的 `ros2` 目录作为 `src`（或软链），然后 `colcon build`：

```bash
mkdir -p ~/ws_cam_perception/src
cd ~/ws_cam_perception/src
ln -s /path/to/CAM_PERCEPTION/ros2/src/cam_perception_bridge .

cd ~/ws_cam_perception
source /opt/ros/humble/setup.bash
colcon build --packages-select cam_perception_bridge --symlink-install
source install/setup.bash
```

`--symlink-install` 便于开发；节点仍通过 `CAM_PERCEPTION_ROOT` 或路径推断加载 `perception_stack`。

若未使用 symlink 且安装后的 `perception_node.py` 不在源码树中，**必须**设置环境变量：

```bash
export CAM_PERCEPTION_ROOT=/path/to/CAM_PERCEPTION
```

或在启动时传入参数 `cam_perception_root:=/path/to/CAM_PERCEPTION`。

---

## 4. 运行节点

```bash
source /opt/ros/humble/setup.bash
source ~/ws_cam_perception/install/setup.bash
export CAM_PERCEPTION_ROOT=/path/to/CAM_PERCEPTION

ros2 run cam_perception_bridge cam_perception_node \
  --ros-args \
  -p source:=replay \
  -p task:=traffic_sign \
  -p pipeline_config:=configs/pipeline.yaml \
  -p replay_root:=data/samples/replay_min \
  -p publish_topic:=/camera_perception/detections
```

### 常用参数

| 参数 | 含义 |
|------|------|
| `cam_perception_root` | 仓库根目录；空则使用 `CAM_PERCEPTION_ROOT` 或从源码路径推断 |
| `pipeline_config` | 相对于仓库根的配置，默认 `configs/pipeline.yaml` |
| `task` | `traffic_sign` 或 `traffic_light` |
| `source` | `replay`：循环读取 `replay_root/cam_test` 下图片；`live`：本机摄像头 |
| `replay_root` | 相对仓库根，默认 `data/samples/replay_min` |
| `camera` | `live` 时设备，如 `0` 或 `/dev/video0`；空则用 `pipeline.yaml` 里 `capture.device` |
| `publish_topic` | 发布话题名，默认 `/camera_perception/detections` |
| `timer_period_s` | 定时器周期（秒）；`replay`/`live` 均在定时器里取帧并推理 |
| `max_frames` | 大于 0 时处理若干帧后仍 spin 但不再发布（调试用） |

### Launch 示例

```bash
ros2 launch cam_perception_bridge perception.launch.py \
  cam_perception_root:=/path/to/CAM_PERCEPTION \
  source:=replay
```

---

## 5. 订阅与消息类型

- **话题**：默认 `/camera_perception/detections`
- **类型**：`vision_msgs/msg/Detection2DArray`

每条 `Detection2D` 含：

- `header`：时间戳由 `CameraFrame.header.stamp_ms` 转换；`frame_id` 与配置中 `capture.frame_id` 一致
- `bbox`：`BoundingBox2D`（像素，中心 + `size_x` / `size_y`）
- `results`：`ObjectHypothesisWithPose`，`hypothesis.class_id` / `score` 来自稳定类别与置信度
- `id`：跟踪 ID（字符串）

查看一次消息：

```bash
ros2 topic echo /camera_perception/detections --once
```

---

## 6. 与落盘 JSON 的关系

`Publisher` 仍可将结果写入 `logs/metrics/`；ROS 2 发布为**在线、类型化**的同一语义层。规划或其它节点应**订阅话题**而不是读 JSON；JSON 适合调试与录包外分析。

---

## 7. 故障排除

| 现象 | 处理 |
|------|------|
| `Cannot find CAM_PERCEPTION repo` | 设置 `export CAM_PERCEPTION_ROOT=...` 或 `-p cam_perception_root:=...` |
| `Config not found` | 确认 `pipeline_config` 相对仓库根存在，且 `CAM_PERCEPTION_ROOT` 正确 |
| 无检测结果 | 检查 `models/` 与 `pipeline.yaml` 中 `model_path`；`replay` 时确认 `cam_test` 下有图片 |
| `vision_msgs` 导入失败 | `sudo apt install ros-humble-vision-msgs` |

更多相机离线/实时运行说明见 [CAMERA_LIVE_USAGE.md](./CAMERA_LIVE_USAGE.md)。
