from __future__ import annotations
import time
import numpy as np

from perception_stack.common.types import Header, CameraFrame, Detection2D, ROI2D, SemanticObject2D
from perception_stack.tracker.tracker2d import Tracker2D
from perception_stack.stabilizer.stabilizer import Stabilizer
from perception_stack.publisher.publisher import Publisher
from perception_stack.visualizer.visualizer import Visualizer


def fake_frame(stamp_ms: int, w=1280, h=720) -> CameraFrame:
    img = np.zeros((h, w, 3), dtype=np.uint8)
    return CameraFrame(header=Header(stamp_ms=stamp_ms, frame_id="cam_front"), image_bgr=img)


def fake_detections(cam_id: str):
    return [
        Detection2D(cam_id, ROI2D(200, 150, 80, 80), "traffic_light_red", 0.9),
        Detection2D(cam_id, ROI2D(500, 200, 100, 60), "speed_limit_80", 0.85),
    ]


def main():
    tracker = Tracker2D()
    stab = Stabilizer(window_len=10, switch_k=3, min_stable_conf=0.6)
    pub = Publisher()
    vis = Visualizer()

    for i in range(5):
        now = int(time.time() * 1000)
        cam = fake_frame(now)

        detections = fake_detections(cam.header.frame_id)
        tracks = tracker.update(detections, now)

        semantic_list = []

        for t in tracks:
            stable_cls, stable_conf, suppressed = stab.update(t.track_id, t.class_id, t.score)

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

        status = {"fps": 30}
        json_path = pub.publish(cam.header.stamp_ms, semantic_list, status)
        overlay_path = vis.draw(cam, semantic_list, 0)

        print("wrote:", json_path, overlay_path)
        time.sleep(0.2)


if __name__ == "__main__":
    main()