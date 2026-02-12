from __future__ import annotations
import json
import os
from dataclasses import asdict
from typing import List, Dict, Any
from perception_stack.common.types import SemanticObject

class Publisher:
    """
    semantic 输出 + status 输出
    Demo阶段：写到 logs/ 里，后续可替换为 ROS2 发布/自研总线
    """
    def __init__(self, out_dir: str = "/workspace/perception_stack/logs"):
        self.out_dir = (
            out_dir
            or os.getenv("PERCEPTION_OUT_DIR")
            or os.path.join(os.getcwd(), "logs")
        )
        os.makedirs(self.out_dir, exist_ok=True)
        

    def publish(self, stamp_ms: int, objects: List[SemanticObject], status: Dict[str, Any]) -> str:
        payload = {
            "stamp_ms": stamp_ms,
            "objects": [asdict(o) for o in objects],
            "status": status
        }
        path = os.path.join(self.out_dir, f"semantic_{stamp_ms}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        return path
