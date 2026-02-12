from __future__ import annotations
import time
import numpy as np

from perception_stack.common.types import Header, CameraFrame, TrackedObject3D, SemanticObject
from perception_stack.sync.sync_manager import SyncManager
from perception_stack.projector.projector import Projector
from perception_stack.infer.infer_engine import InferEngine
from perception_stack.stabilizer.stabilizer import Stabilizer
from perception_stack.publisher.publisher import Publisher
from perception_stack.visualizer.visualizer import Visualizer

def fake_frame(stamp_ms: int, w=1280, h=720) -> CameraFrame:
    img = np.zeros((h, w, 3), dtype=np.uint8)
    return CameraFrame(header=Header(stamp_ms=stamp_ms, frame_id="cam_front"), image_bgr=img)

def fake_objects() -> list[TrackedObject3D]:
    return [
        TrackedObject3D(track_id=17, position_ego_m=(12.0, -1.0, 0.0), velocity_ego_mps=(1.2,0,0), bbox3d_size_m=(4.2,1.8,1.6)),
        TrackedObject3D(track_id=23, position_ego_m=(8.0,  0.6, 0.0), velocity_ego_mps=(0.0,0,0), bbox3d_size_m=(0.5,0.5,1.0)),
        TrackedObject3D(track_id=31, position_ego_m=(15.0, 1.5, 0.0), velocity_ego_mps=(0.2,0,0), bbox3d_size_m=(1.8,0.6,1.5)),
    ]

def main():
    sync = SyncManager(sync_max_dt_ms=50)
    projector = Projector(img_w=1280, img_h=720)
    infer = InferEngine()
    stab = Stabilizer(window_len=10, switch_k=3, min_stable_conf=0.6)
    pub = Publisher()
    vis = Visualizer()

    for i in range(5):
        now = int(time.time() * 1000)
        frame = fake_frame(now)
        objs = fake_objects()

        sync.push_camera(frame)
        sync.push_objects(now - 10, objs)  # 模拟 10ms 时间差

        matched = sync.match()
        if matched is None:
            print("no match")
            continue

        cam, obj_ts, obj_list, dt_ms = matched
        semantic_list = []

        for o in obj_list:
            roi = projector.project_object_to_roi(o)
            if roi is None:
                cls, conf = "unknown", 0.0
                stable_cls, stable_conf, suppressed = "unknown", 0.0, False
            else:
                patch = cam.image_bgr[roi.y:roi.y+roi.h, roi.x:roi.x+roi.w]
                cls, conf = infer.infer_roi(patch)
                stable_cls, stable_conf, suppressed = stab.update(o.track_id, cls, conf)

            semantic = SemanticObject(
                track_id=o.track_id,
                class_id=cls,
                class_conf=float(conf),
                position_ego_m=o.position_ego_m,
                velocity_ego_mps=o.velocity_ego_mps,
                bbox3d_size_m=o.bbox3d_size_m,
                yaw_rad=o.yaw_rad,
                roi2d=roi,
                stable_class_id=stable_cls,
                stable_conf=float(stable_conf)
            )
            semantic_list.append(semantic)

        status = {"fps": 30, "sync_dt_ms": dt_ms}
        json_path = pub.publish(cam.header.stamp_ms, semantic_list, status)
        overlay_path = vis.draw(cam, semantic_list, dt_ms)
        print("wrote:", json_path, overlay_path)

        time.sleep(0.2)

if __name__ == "__main__":
    main()
