"""感知管线核心步骤，供 main 与 ROS2 桥接节点复用。"""
from __future__ import annotations

import os
import re
import time
from pathlib import Path
from typing import Any

import yaml

from perception_stack.common.types import CameraFrame, SemanticObject2D
from perception_stack.stabilizer.stabilizer import Stabilizer
from perception_stack.tracker.tracker2d import Tracker2D
from perception_stack.infer.infer_engine import InferEngine

# pipeline.yaml 中形如 "${models.traffic_light.threshold}" 的占位符，从同目录 models.yaml 取值
_MODELS_PLACEHOLDER = re.compile(r"^\$\{models\.(.+)\}$")


def _resolve_models_placeholder(value: str, models: dict[str, Any]) -> Any:
    m = _MODELS_PLACEHOLDER.match(value.strip())
    if not m:
        return value
    cur: Any = models
    for key in m.group(1).split("."):
        if not isinstance(cur, dict) or key not in cur:
            raise KeyError(
                f"models.yaml 中不存在路径 '{'/'.join(m.group(1).split('.'))}' "
                f"(来自占位符 {value!r})"
            )
        cur = cur[key]
    return cur


def _apply_models_placeholders(obj: Any, models: dict[str, Any]) -> Any:
    if isinstance(obj, dict):
        return {k: _apply_models_placeholders(v, models) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_apply_models_placeholders(v, models) for v in obj]
    if isinstance(obj, str):
        return _resolve_models_placeholder(obj, models)
    return obj


def load_cfg(path: str) -> dict:
    path = os.path.abspath(path)
    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    models_path = os.path.join(os.path.dirname(path), "models.yaml")
    if os.path.isfile(models_path):
        with open(models_path, "r", encoding="utf-8") as f:
            models = yaml.safe_load(f) or {}
        cfg = _apply_models_placeholders(cfg, models)
    return cfg


def infer_repo_root_from_config_path(config_path: str) -> Path:
    """由 pipeline 配置路径推断仓库根（标准布局：.../configs/*.yaml）。"""
    p = Path(config_path).resolve()
    if p.parent.name == "configs":
        return p.parent.parent
    return Path.cwd()


def resolve_repo_relative_model_paths(cfg: dict, repo_root: Path | str) -> None:
    """将 task.*.model_path 的相对路径改为相对仓库根的绝对路径（原地修改 cfg）。"""
    root = Path(repo_root).resolve()
    tasks = cfg.get("task")
    if not isinstance(tasks, dict):
        return
    for _name, tcfg in tasks.items():
        if not isinstance(tcfg, dict):
            continue
        mp = tcfg.get("model_path")
        if isinstance(mp, str) and mp.strip() and not Path(mp).is_absolute():
            tcfg["model_path"] = str(root / mp)


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
