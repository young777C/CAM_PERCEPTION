from __future__ import annotations
import os
import cv2
import numpy as np
from typing import List
from perception_stack.common.types import CameraFrame, SemanticObject

class Visualizer:
    """
    overlay 与日志落盘
    """
    def __init__(self, out_dir: str = "/workspace/perception_stack/logs/overlay"):
        self.out_dir = out_dir
        os.makedirs(self.out_dir, exist_ok=True)

    def draw(self, frame: CameraFrame, objects: List[SemanticObject], dt_ms: int) -> str:
        img = frame.image_bgr.copy()
        cv2.putText(img, f"stamp={frame.header.stamp_ms} dt={dt_ms}ms", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)

        for o in objects:
            if o.roi2d is None:
                continue
            x, y, w, h = o.roi2d.x, o.roi2d.y, o.roi2d.w, o.roi2d.h
            cv2.rectangle(img, (x,y), (x+w, y+h), (255, 255, 0), 2)
            label = f"id={o.track_id} {o.stable_class_id or o.class_id}:{(o.stable_conf or o.class_conf):.2f}"
            cv2.putText(img, label, (x, max(20, y-5)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,0), 2)

        path = os.path.join(self.out_dir, f"overlay_{frame.header.stamp_ms}.jpg")
        cv2.imwrite(path, img)
        return path
