from typing import List
from perception_stack.common.types import CameraFrame, Detection2D, ROI2D
from .base import DetectorBase


class TrafficSignDetector(DetectorBase):
    task_name = "traffic_sign"

    def detect(self, frame: CameraFrame) -> List[Detection2D]:
        roi = ROI2D(500, 220, 100, 80)
        return [
            Detection2D(
                cam_id=frame.header.frame_id,
                roi=roi,
                class_id="traffic_sign",
                score=0.85,
                attrs={"type": "speed_limit", "value": 80},
            )
        ]