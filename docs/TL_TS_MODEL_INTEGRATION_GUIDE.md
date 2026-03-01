# TL / TS 模型接入规范

> 适用于 Traffic Light（TL）与 Traffic Sign（TS）负责人
> 目标：在不破坏主线的前提下，将模型接入多任务相机感知框架

---

# 1. 总体目标

本规范用于指导：

* TL 负责人接入交通灯模型
* TS 负责人接入交通标志模型

并保证：

* 主线 `main` 随时可跑
* `run_replay.sh` 冒烟测试通过
* 输出格式稳定
* 不修改核心框架代码

---

# 2. 当前工程架构

```
configs/models.yaml
        ↓
InferEngine（任务路由器）
        ↓
detectors/traffic_light.py
detectors/traffic_sign.py
        ↓
Detection2D
        ↓
Tracker2D → Stabilizer → Publisher
        ↓
overlay + metrics
```

---

# 3. 职责边界（必须遵守）

## ✅ TL / TS 负责人只允许修改：

```
src/perception_stack/infer/detectors/traffic_light.py
src/perception_stack/infer/detectors/traffic_sign.py
configs/models.yaml
```

---

## ❌ 不允许修改：

* run_replay.sh
* publisher
* tracker
* stabilizer
* main 主流程
* InferEngine 路由逻辑

如需修改接口，必须与 CORE 协调。

---

# 4. models.yaml 应填写内容

路径：

```
configs/models.yaml
```

示例：

```yaml
traffic_light:
  model_path: models/tl.onnx
  input_size: [640, 640]
  threshold: 0.3
  device: cpu

traffic_sign:
  model_path: models/ts.onnx
  input_size: [640, 640]
  threshold: 0.4
  device: cpu
```

---

## 字段说明

| 字段         | 含义               |
| ---------- | ---------------- |
| model_path | 模型文件路径           |
| input_size | 推理输入尺寸           |
| threshold  | 置信度过滤阈值          |
| device     | 推理设备（cpu / cuda） |

---

# 5. Detector 文件必须实现内容

文件路径：

```
infer/detectors/traffic_light.py
infer/detectors/traffic_sign.py
```

必须实现：

```python
def detect(self, frame: CameraFrame) -> List[Detection2D]
```

---

# 6. detect() 的职责

detect() 必须完成：

1. 图像前处理（resize / normalize）
2. 模型推理
3. 后处理（NMS / threshold 过滤）
4. 转换为 `Detection2D` 列表

---

# 7. Detection2D 输出规范

必须返回：

```python
Detection2D(
    cam_id=frame.header.frame_id,
    roi=ROI2D(x, y, w, h),
    class_id="traffic_light",  # 任务名
    score=0.91,
    attrs={...}
)
```

---

## TL 输出规范

```python
attrs = {
    "state": "red",      # red / yellow / green
    "arrow": "left"      # 可选
}
```

---

## TS 输出规范

```python
attrs = {
    "type": "speed_limit",
    "value": 80
}
```

---

# 8. 禁止行为

❌ 不要在 detector 中写死模型路径
❌ 不要在 detector 中读取 yaml 文件
❌ 不要修改 Publisher 输出结构
❌ 不要返回自定义对象（必须返回 Detection2D）
❌ 不要修改主流程代码

---

# 9. 正确读取配置方式

在 detector 初始化中：

```python
def __init__(self, cfg):
    self.model_path = cfg.get("model_path")
    self.input_size = tuple(cfg.get("input_size", [640, 640]))
    self.threshold = cfg.get("threshold", 0.3)
    self.device = cfg.get("device", "cpu")
```

InferEngine 会自动传入对应配置。

---

# 10. PR 提交要求

每个任务 PR 必须满足：

1. `bash scripts/run_replay.sh` 通过
2. logs/overlay 有图片输出
3. logs/metrics 有 JSON 输出
4. 不修改核心框架代码
5. 输出符合 Detection2D 规范

---

## PR 标题示例

```
feat(tl): integrate traffic light detector
feat(ts): integrate traffic sign detector
```

---

# 11. 验证方法

运行：

```bash
bash scripts/run_replay.sh
```

必须看到：

```
overlay_count >= 1
metrics_count >= 1
```

否则视为接入失败。

---

# 12. 未来扩展方向

当前阶段只要求：

* 单帧检测
* 基础阈值过滤

未来可能增加：

* 多尺度推理
* 属性二阶段模型
* 多模型 ensemble
* TensorRT 加速
* 任务级稳定器增强

---

# 13. 核心原则总结

* 模型参数在 config
* 推理逻辑在 detector
* 路由在 InferEngine
* 输出协议由 Publisher 统一
* 主线稳定优先于模型复杂度

---



