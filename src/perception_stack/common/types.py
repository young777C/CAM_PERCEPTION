from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Tuple, List, Dict

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
class Detection2D:
    cam_id: str
    roi: ROI2D
    class_id: str
    score: float
    attrs: Optional[Dict[str, Any]] = None  # TL: color/arrow; TS: value/speed etc.

@dataclass
class TrackObject2D:  # 纯相机感知阶段采用2d追踪
    track_id: int
    cam_id: str
    roi: ROI2D
    class_id: str
    score: float
    age: int                 # 已存在帧数
    last_seen_ms: int
    attrs: Optional[Dict[str, Any]] = None

from dataclasses import dataclass
from typing import Optional, Dict, Any, Tuple

# 如果你们已经有 ROI2D，就复用；没有就用你新增的 ROI2D

@dataclass
class SemanticObject2D:
    track_id: int
    cam_id: str
    class_id: str
    class_conf: float
    roi2d: ROI2D

    stable_class_id: str
    stable_conf: float

    # 可选属性：TL/TS 用（灯色、箭头、限速值等）
    attributes: Optional[Dict[str, Any]] = None
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
