from __future__ import annotations
import json
from pathlib import Path
from dataclasses import is_dataclass, asdict
from typing import Any

def to_jsonable(x: Any) -> Any:
    """Convert python objects (dataclass/np/tuple) into JSON-serializable types."""
    # dataclass (e.g., ROI2D)
    if is_dataclass(x):
        return {k: to_jsonable(v) for k, v in asdict(x).items()}

    # dict
    if isinstance(x, dict):
        return {str(k): to_jsonable(v) for k, v in x.items()}

    # list/tuple/set
    if isinstance(x, (list, tuple, set)):
        return [to_jsonable(v) for v in x]

    # numpy types (optional)
    try:
        import numpy as np  # local import to avoid hard dependency in publisher
        if isinstance(x, np.ndarray):
            return x.tolist()
        if isinstance(x, (np.integer, np.floating)):
            return x.item()
    except Exception:
        pass

    # primitive
    if isinstance(x, (str, int, float, bool)) or x is None:
        return x

    # fallback: object -> __dict__ or str
    if hasattr(x, "__dict__"):
        return to_jsonable(vars(x))

    return str(x)

class Publisher:
    """
    '''功能：
    1）结构标准化：将pipeline内部生成的数据封装成结构化JSON
    2）落盘管理：输出统一到logs/metrics/
    3）输出分频道：通过group_by_task将TL/TS任务进行区分'''
    Demo阶段：写到 logs/ 里，后续可替换为 ROS2 发布/自研总线
    """
    def __init__(self, out_dir: str = "logs"):
        self.out_dir = Path(out_dir)
        self.metrics_dir = self.out_dir / "metrics"
        self.metrics_dir.mkdir(parents=True, exist_ok=True)

    def publish(self, stamp_ms: int, semantic_list, status: dict, frame_id: str = "cam_front"):
        # ✅ 统一输出文件位置
        json_path = self.metrics_dir / f"semantic_{stamp_ms}.json"

        payload = {
            "header": {"stamp_ms": stamp_ms, "frame_id": frame_id},
            "status": status,
            # ✅ 统一输出格式：results 按任务分频道（先兼容旧 list）
            "results": self._group_by_task(semantic_list),
        }

        json_path.write_text(json.dumps(to_jsonable(payload), ensure_ascii=False), encoding="utf-8")
        return str(json_path)
    
    def _group_by_task(self, semantic_list):
        """
        兼容策略：
        - 如果 semantic_list 是 list[dict] 且含 task 字段：按 task 分组
        - 否则：全部放到 'unknown'，保证不崩
        """
        out = {"traffic_light": [], "traffic_sign": [], "unknown": []}

        for s in semantic_list:
            if isinstance(s, dict):
                task = s.get("task", "unknown")
                if task not in out:
                    out["unknown"].append(s)
                else:
                    out[task].append(s)
            else:
                # 如果还是旧的 SemanticObject 类型，可以先转 dict 或塞 unknown
                out["unknown"].append(getattr(s, "__dict__", str(s)))

        # 可选：把空频道删掉，减少噪声
        return {k: v for k, v in out.items() if v}