from __future__ import annotations
from pathlib import Path
from typing import Dict, Any
import os
import yaml


def resolve_model_path(model_path: str | None) -> str | None:
    """将相对模型路径按 CAM_PERCEPTION_ROOT（若已设置）或当前工作目录解析为绝对路径。"""
    if model_path is None:
        return None
    s = str(model_path).strip()
    if not s:
        return model_path
    p = Path(s)
    if p.is_absolute():
        return str(p)
    root = os.environ.get("CAM_PERCEPTION_ROOT", "").strip()
    if root:
        return str(Path(root).resolve() / p)
    return str(Path.cwd() / p)


def load_yaml(path: str) -> Dict[str, Any]:
    if not path:
        return {}
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}
