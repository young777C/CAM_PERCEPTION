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
