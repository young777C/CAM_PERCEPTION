from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Tuple, List, Dict
# detector输出
TLDetections2D = {
  "cam_id": str,
  "timestamp": float,
  "boxes": List[[x1,y1,x2,y2]],     # 原图坐标
  "scores": List[float],           # det score
}
# classifier输出
TLClassifications = {
  "cam_id": str,
  "timestamp": float,
  "boxes": List[[x1,y1,x2,y2]],
  "det_scores": List[float],
  "states": List[str],             # red/yellow/green/unknown
  "cls_scores": List[float],       # 分类置信度
  "score": List[float],            # 综合分（见下）
}
# stablizer输出
StableTrafficLight = {
  "cam_id": str,
  "track_id": int,
  "bbox": [x1,y1,x2,y2],
  "state": str,          # 当前帧分类
  "stable_state": str,   # 稳定输出
  "confidence": float,   # 稳定输出置信度
  "timestamp": float,
  "last_change_time": float,
}

@dataclass
class Header:
    stamp_ms: int
    frame_id: str = "ego"
    seq: int = 0

@dataclass
class CameraFrame:
    header: Header
    image_bgr: "object"   # numpy ndarray

@dataclass
class TrackedObject3D:
    track_id: int
    position_ego_m: Tuple[float, float, float]
    velocity_ego_mps: Tuple[float, float, float]
    bbox3d_size_m: Tuple[float, float, float]  # (l,w,h)
    yaw_rad: float = 0.0
    state: str = "TRACKED"

@dataclass
class ROI2D:
    x: int
    y: int
    w: int
    h: int

@dataclass
class SemanticObject:
    track_id: int
    class_id: str
    class_conf: float
    position_ego_m: Tuple[float, float, float]
    velocity_ego_mps: Tuple[float, float, float]
    bbox3d_size_m: Tuple[float, float, float]
    yaw_rad: float
    roi2d: Optional[ROI2D] = None
    stable_class_id: Optional[str] = None
    stable_conf: Optional[float] = None
