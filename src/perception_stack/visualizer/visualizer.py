from __future__ import annotations
import os
from typing import Optional

class Visualizer:
    def __init__(self, out_dir: Optional[str] = None):
        # 优先：显式参数 > 环境变量（可单独配）> 默认（当前目录/logs/overlay）
        base = (
            out_dir
            or os.getenv("PERCEPTION_VIS_DIR")
            or os.getenv("PERCEPTION_OUT_DIR")
            or os.path.join(os.getcwd(), "logs")
        )
        self.out_dir = os.path.join(base, "overlay")
        os.makedirs(self.out_dir, exist_ok=True)
