from __future__ import annotations
from collections import deque
from typing import Deque, Optional, Tuple, List
from perception_stack.common.types import CameraFrame, TrackedObject3D

class SyncManager:
    """
    时间对齐与缓存（cam 帧队列、obj 队列）
    策略：最近邻匹配，dt 超阈值返回 None
    """
    def __init__(self, max_cam_cache: int = 30, max_obj_cache: int = 60, sync_max_dt_ms: int = 50):
        self.cam_q: Deque[CameraFrame] = deque(maxlen=max_cam_cache)
        self.obj_q: Deque[Tuple[int, List[TrackedObject3D]]] = deque(maxlen=max_obj_cache)  # (stamp_ms, objs)
        self.sync_max_dt_ms = sync_max_dt_ms

    def push_camera(self, frame: CameraFrame) -> None:
        self.cam_q.append(frame)

    def push_objects(self, stamp_ms: int, objs: list[TrackedObject3D]) -> None:
        self.obj_q.append((stamp_ms, objs))

    def match(self) -> Optional[Tuple[CameraFrame, int, list[TrackedObject3D], int]]:
        """
        返回 (cam_frame, obj_stamp_ms, objects, dt_ms)
        """
        if not self.cam_q or not self.obj_q:
            return None

        obj_stamp_ms, objs = self.obj_q[-1]
        # 在 cam_q 里找最接近 obj_stamp 的帧
        best = None
        best_dt = 10**18
        for f in self.cam_q:
            dt = abs(f.header.stamp_ms - obj_stamp_ms)
            if dt < best_dt:
                best_dt = dt
                best = f

        if best is None or best_dt > self.sync_max_dt_ms:
            return None
        return best, obj_stamp_ms, objs, int(best_dt)
