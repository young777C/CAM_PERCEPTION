#!/usr/bin/env python3
"""
export_onnx.py

离线将本地 YOLOv5/YOLO11s PyTorch 模型导出为 ONNX，适用于 InferEngine 或 TrafficSignDetector。
"""

import sys
import torch
import numpy as np
from pathlib import Path

# -----------------------------
# 配置区域
# -----------------------------
# 模型路径（训练完成的 PT 文件）
pt_path = "runs/detect/train2/weights/best.pt"

# 导出后的 ONNX 文件路径
onnx_path = "models/yolo11s.onnx"

# 输入图像大小（HxW）
img_size = 640

# batch size
batch_size = 1

# -----------------------------
# 将本地 YOLOv5 加入路径（离线）
# -----------------------------
yolov5_dir = Path(__file__).parent.parent / "yolov5"
if not yolov5_dir.exists():
    raise FileNotFoundError(f"YOLOv5 local repo not found at {yolov5_dir}")
sys.path.insert(0, str(yolov5_dir))

# -----------------------------
# 导入模型加载接口
# -----------------------------
from models.common import DetectMultiBackend

# -----------------------------
# 加载模型
# -----------------------------
device = "cuda" if torch.cuda.is_available() else "cpu"
model = DetectMultiBackend(pt_path, device=device)
model.eval()
print(f"✅ Loaded model: {pt_path}")

# -----------------------------
# 构造虚拟输入
# -----------------------------
dummy_input = torch.zeros(batch_size, 3, img_size, img_size).to(device)

# -----------------------------
# 导出 ONNX
# -----------------------------
torch.onnx.export(
    model.model,            # 注意 DetectMultiBackend 包装了一层 model
    dummy_input,
    onnx_path,
    opset_version=12,
    input_names=['images'],
    output_names=['output'],
    dynamic_axes={'images': {0: 'batch'}, 'output': {0: 'batch'}},
    verbose=True,
)

print(f"✅ ONNX model exported: {onnx_path}")

# -----------------------------
# ONNX 验证（可选）
# -----------------------------
try:
    import onnxruntime as ort
    sess = ort.InferenceSession(onnx_path)
    dummy_np = np.zeros((batch_size, 3, img_size, img_size), dtype=np.float32)
    outputs = sess.run(None, {"images": dummy_np})
    print(f"✅ ONNX Runtime test output shape: {outputs[0].shape}")
except Exception as e:
    print(f"⚠️ ONNX Runtime test failed: {e}")