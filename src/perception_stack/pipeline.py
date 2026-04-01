"""感知管线核心步骤，供 main 与 ROS2 桥接节点复用。"""
from __future__ import annotations

import time
import yaml

from perception_stack.common.types import CameraFrame, SemanticObject2D
from perception_stack.stabilizer.stabilizer import Stabilizer
from perception_stack.tracker.tracker2d import Tracker2D
from perception_stack.infer.infer_engine import InferEngine


def load_cfg(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def apply_task_flag(cfg: dict, task: str) -> None:
    if task == "traffic_light":
        cfg["enabled_tasks"] = ["traffic_light"]
    elif task == "traffic_sign":
        cfg["enabled_tasks"] = ["traffic_sign"]


def run_infer_pipeline(
    cam: CameraFrame,
    infer: InferEngine,
    tracker: Tracker2D,
    stab: Stabilizer,
) -> list:
    detections = infer.run_flat(cam)
    tracks = tracker.update(detections, int(time.time() * 1000))
    semantic_list = []
    for t in tracks:
        stable_cls, stable_conf, _suppressed = stab.update(t.track_id, t.class_id, t.score)
        semantic_list.append(
            SemanticObject2D(
                track_id=t.track_id,
                cam_id=t.cam_id,
                class_id=t.class_id,
                class_conf=float(t.score),
                roi2d=t.roi,
                stable_class_id=stable_cls,
                stable_conf=float(stable_conf),
                attributes=t.attrs,
            )
        )
    return semantic_list
