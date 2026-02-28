from typing import Dict, Any, List
from perception_stack.common.types import CameraFrame, Detection2D
from perception_stack.infer.detectors.traffic_light import TrafficLightDetector
from perception_stack.infer.detectors.traffic_sign import TrafficSignDetector


TASK_REGISTRY = {
    "traffic_light": TrafficLightDetector,
    "traffic_sign": TrafficSignDetector,
}


class InferEngine:
    def __init__(self, cfg: Dict[str, Any] | None = None):
        if cfg is None:
            cfg = {
                "enabled_tasks": ["traffic_light", "traffic_sign"],
                "tasks": {}
            }

        self.enabled_tasks = cfg.get("enabled_tasks", [])
        self.detectors = {}

        for task in self.enabled_tasks:
            detector_cls = TASK_REGISTRY[task]
            self.detectors[task] = detector_cls(
                cfg.get("tasks", {}).get(task, {})
            )

    def run(self, frame: CameraFrame) -> Dict[str, List[Detection2D]]:
        outputs = {}
        for task, detector in self.detectors.items():
            outputs[task] = detector.detect(frame)
        return outputs

    def run_flat(self, frame: CameraFrame) -> List[Detection2D]:
        merged = []
        for detector in self.detectors.values():
            merged.extend(detector.detect(frame))
        return merged