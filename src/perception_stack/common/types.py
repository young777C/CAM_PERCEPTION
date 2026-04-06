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

@dataclass(kw_only=True)
class SemanticObjectBase:
    '''语义基类（协议层）'''
    track_id: int
    class_id: str
    class_conf: float

    stable_class_id: Optional[str] = None
    stable_conf: Optional[float] = None

    attributes: Optional[Dict[str, Any]] = None
@dataclass
class SemanticObject2D(SemanticObjectBase):
    '''纯相机感知阶段足够'''
    cam_id: str
    roi2d: ROI2D
@dataclass
class SemanticObject3D(SemanticObjectBase):
    '''融合感知时
    TrackObject2D
    +
    LidarObject3D
        ↓
    SemanticObject3D
    '''
    position_ego_m: Tuple[float, float, float]
    velocity_ego_mps: Tuple[float, float, float]
    bbox3d_size_m: Tuple[float, float, float]
    yaw_rad: float
    roi2d: Optional[ROI2D] = None