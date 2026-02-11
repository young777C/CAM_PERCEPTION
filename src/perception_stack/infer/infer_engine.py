from __future__ import annotations
from typing import Tuple
import numpy as np
import math


class InferEngine:
    """
    分类/检测推理（TensorRT/ONNXRuntime/NN加速）
    先给占位：输入 ROI patch，输出 (class_id, conf)
    """
    def __init__(self):
        self.classes = ["vehicle", "pedestrian", "bicycle", "cone", "barrier", "unknown"]

    def infer_roi(self, roi_bgr: np.ndarray) -> Tuple[str, float]:
        h, w = roi_bgr.shape[:2]
        # 占位逻辑：面积/长宽比做个假判断
        area = h * w
        ratio = w / max(1, h)
        if area > 70000:
            return "vehicle", 0.65
        if area < 6000:
            return "cone", 0.55
        if 0.3 < ratio < 0.8:
            return "pedestrian", 0.6
        return "unknown", 0.4
