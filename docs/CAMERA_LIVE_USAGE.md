# 相机感知运行说明（离线回放与车端实时）

本文说明如何在仓库根目录下配置环境、运行 **离线图片回放（replay）** 与 **车端/本机实时采集（live）**，以及 `configs/pipeline.yaml` 中与采集相关的字段含义。

---

## 1. 通用环境

在仓库根目录执行（将 `CAM_PERCEPTION` 换为你的实际路径）：

```bash
cd /path/to/CAM_PERCEPTION
export PYTHONPATH="$PWD/src:${PYTHONPATH:-}"
```

若使用项目虚拟环境：

```bash
source .venv/bin/activate   # 或你的 venv 路径
```

依赖需包含 OpenCV、PyYAML 及推理栈所需包（见仓库根目录 `requirements.txt`）。

---

## 2. 离线回放（`--mode replay`）

用于无摄像头时的冒烟测试或算法调试：从目录中顺序读取图片，走完整检测、跟踪、稳定化与落盘。

### 2.1 数据目录结构

默认根目录为 `data/samples/replay_min`（可用 `--replay_root` 修改）。其下需存在子目录 **`cam_test`**，内为 `.png` 或 `.jpg` 图片。

示例：

```text
data/samples/replay_min/
  cam_test/
    frame_001.jpg
    frame_002.jpg
```

### 2.2 命令行

```bash
python -m perception_stack.main \
  --mode replay \
  --replay_root data/samples/replay_min \
  --frames 20 \
  --config configs/pipeline.yaml \
  --task traffic_sign
```

| 参数 | 含义 |
|------|------|
| `--replay_root` | 回放根目录；图片在 `<replay_root>/cam_test/` |
| `--frames` | 最多处理的图片张数 |
| `--config` | 管线配置，默认 `configs/pipeline.yaml` |
| `--task` | `traffic_sign` 或 `traffic_light`，会覆盖配置中的 `enabled_tasks` |

### 2.3 脚本封装

```bash
./scripts/run_replay.sh              # 默认 traffic_sign
./scripts/run_replay.sh traffic_light
```

脚本会设置 `PYTHONPATH`、清理并准备 `logs/overlay`、`logs/metrics`，运行后检查是否生成 overlay 与 metrics。可通过环境变量指定解释器：

```bash
PYTHON_BIN=/path/to/python ./scripts/run_replay.sh
```

---

## 3. 车端/本机实时（`--mode live`）

从摄像头（或 V4L2 设备）持续取流：采集在**独立线程**，推理在**主线程**，通过有界队列与 `drop_policy` 控制背压，避免采集被推理阻塞。

### 3.1 前置条件

- 设备可用：如 `/dev/video0` 或索引 `0`（Linux 下需相应权限）。
- 模型与 `configs/pipeline.yaml` 中任务、设备（如 `cuda`）与车端一致。

### 3.2 命令行

```bash
python -m perception_stack.main \
  --mode live \
  --config configs/pipeline.yaml \
  --task traffic_sign \
  --camera 0
```

| 参数 | 含义 |
|------|------|
| `--camera` | 可选。设备索引（如 `0`）或路径（如 `/dev/video0`）。**省略时**使用 `configs/pipeline.yaml` 里 `capture.device` |
| `--max_frames` | 可选。仅处理前 N 帧后退出，用于调试；默认不限制，需 `Ctrl+C` 结束 |

### 3.3 脚本封装

```bash
chmod +x scripts/run_live.sh   # 仅需首次
./scripts/run_live.sh                           # 默认 traffic_sign，设备用配置中的 capture.device
./scripts/run_live.sh traffic_sign 0            # 指定任务与设备索引
./scripts/run_live.sh traffic_sign /dev/video0  # 指定设备路径
```

脚本同样会设置 `PYTHONPATH` 并在仓库根目录执行。

### 3.4 采集配置（`configs/pipeline.yaml` 中的 `capture`）

仅在 **`live`** 模式下使用；**replay** 可忽略。

| 字段 | 说明 |
|------|------|
| `device` | 默认设备：整数索引或 `"/dev/video0"` 等路径 |
| `width` / `height` | 请求的分辨率（具体以驱动为准） |
| `fps` | 请求的帧率 |
| `queue_size` | `fifo` 策略下的队列长度 |
| `drop_policy` | `latest`：只保留最新一帧，推理慢时丢中间帧，优先低延迟；`fifo`：有界队列，满时丢最旧帧 |
| `frame_id` | 写入 `CameraFrame.header.frame_id` |

命令行 `--camera` 会覆盖配置中的 `device`。

### 3.5 运行中输出与指标

- 终端会打印每帧的 `latency_ms`（采集时间戳到当前处理完成的大致端到端延迟）、`infer_ms`。
- 写入 `logs/metrics/` 的 JSON 中，`status` 字段包含 `fps`、`latency_ms_e2e`、`infer_ms`、`capture`（采集线程统计：抓取数、丢帧、latest 模式下的覆盖次数等）。

时间戳当前为帧到达时刻（毫秒）；若需与整车时钟或 PTP 对齐，应在采集模块中替换为相机或统一时间源（见 `OpenCVThreadedCapture` 实现注释）。

---

## 4. 输出文件位置

| 类型 | 路径 |
|------|------|
| 语义结果 JSON | `logs/metrics/semantic_<stamp_ms>.json` |
| 可视化叠加图 | `logs/overlay/overlay_<stamp_ms>.jpg`（工作目录为仓库根目录时） |

`Visualizer` 的基础目录可通过环境变量配置，默认在 `logs/overlay/`（见 `visualizer.py`）。

---

## 5. 常见问题

- **`ModuleNotFoundError: perception_stack`**：未设置 `PYTHONPATH=.../src`，或未在仓库根目录运行。
- **`Cannot open camera device`**：设备不存在、被占用或权限不足；检查 `--camera` 与 `ls /dev/video*`。
- **回放脚本报错无 overlay**：确认 `cam_test` 下有图片，且 `--frames` 不超过图片数量。

更多模型接入与 detector 职责边界见同目录下的 [TL_TS_MODEL_INTEGRATION_GUIDE.md](./TL_TS_MODEL_INTEGRATION_GUIDE.md)。

通过 ROS 2 发布检测结果（`vision_msgs`）见 [ROS2_INTEGRATION.md](./ROS2_INTEGRATION.md)。
