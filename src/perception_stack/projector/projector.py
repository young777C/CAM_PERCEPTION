from __future__ import annotations
from typing import Optional
import numpy as np
from perception_stack.common.types import TrackedObject3D, ROI2D

class Projector:
    """
    标定加载、3D->2D 投影、ROI 生成
    先给简化版：假设相机朝前，X为前向深度，Y为左右，Z为高度
    """
    def __init__(self, img_w: int, img_h: int, fx: float = 700, fy: float = 700, cx: float = None, cy: float = None,
                 roi_pad_ratio: float = 0.15, roi_min_px: int = 24):
        self.img_w = img_w
        self.img_h = img_h
        self.fx = fx
        self.fy = fy
        self.cx = cx if cx is not None else img_w / 2.0
        self.cy = cy if cy is not None else img_h / 2.0
        self.roi_pad_ratio = roi_pad_ratio
        self.roi_min_px = roi_min_px

    def project_object_to_roi(self, obj: TrackedObject3D) -> Optional[ROI2D]:
        x, y, z = obj.position_ego_m
        if x <= 0.5:  # 太近或在后方
            return None

        # 简化：把中心点投影到像素
        u = int(self.fx * (y / x) + self.cx)
        v = int(self.fy * (-z / x) + self.cy)

        # 简化：根据 bbox 尺寸估一个像素框大小（越远越小）
        l, w, h = obj.bbox3d_size_m
        box_w = int(self.fx * (w / x))
        box_h = int(self.fy * (h / x))
        if box_w <= 0 or box_h <= 0:
            return None

        # padding
        pad_w = int(box_w * self.roi_pad_ratio)
        pad_h = int(box_h * self.roi_pad_ratio)
        x1 = u - box_w // 2 - pad_w
        y1 = v - box_h // 2 - pad_h
        x2 = u + box_w // 2 + pad_w
        y2 = v + box_h // 2 + pad_h

        # clip
        x1 = max(0, x1); y1 = max(0, y1)
        x2 = min(self.img_w - 1, x2); y2 = min(self.img_h - 1, y2)
        w2 = x2 - x1
        h2 = y2 - y1

        if min(w2, h2) < self.roi_min_px:
            return None
        return ROI2D(x=x1, y=y1, w=w2, h=h2)
