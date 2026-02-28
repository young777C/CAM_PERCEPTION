from typing import List
from perception_stack.common.types import CameraFrame, Detection2D, ROI2D
from .base import DetectorBase


class TrafficLightDetector(DetectorBase):
    task_name = "traffic_light"

    def detect(self, frame: CameraFrame) -> List[Detection2D]:
        roi = ROI2D(200, 120, 60, 60)
        return [
            Detection2D(
                cam_id=frame.header.frame_id,
                roi=roi,
                class_id="traffic_light",
                score=0.9,
                attrs={"state": "red"},
            )
        ]