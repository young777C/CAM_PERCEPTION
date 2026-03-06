import torch
import torch.onnx
import numpy as np
from perception_stack.common.types import CameraFrame, Detection2D
from perception_stack.infer.detectors.traffic_light import TrafficLightDetector
from perception_stack.infer.detectors.traffic_sign import TrafficSignDetector

TASK_REGISTRY = {
    "traffic_light": TrafficLightDetector,
    "traffic_sign": TrafficSignDetector,
}

from ultralytics import YOLO

class InferEngine:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.model_path = cfg.get("model_path", "models/yolo11s.pt")
        self.device = cfg.get("device", "cuda" if torch.cuda.is_available() else "cpu")                                                                                                                                                                                                                                                                                 
        # self.model = self.load_model(self.model_path)
        self.model = YOLO(cfg['task']['traffic_sign']['model_path'])
        print(f"Model loaded: {self.model.__class__.__name__}")
        self.threshold = float(cfg.get("threshold", 0.25))
        self.nms_iou = float(cfg.get("nms_iou", 0.5))
        self.enabled_tasks = cfg.get("enabled_tasks", ["traffic_light", "traffic_sign"])
        task_cfgs = cfg.get("task", {})
        self.detectors = {}
        for task in self.enabled_tasks:
            detector_cls = TASK_REGISTRY[task]
            self.detectors[task] = detector_cls(task_cfgs.get(task, {}))

    def load_model(self, model_path: str):
        """
        加载 YOLOv5 模型并将其放置到正确的设备上
        """
        # 使用 ultralytics 加载 YOLOv5 模型
        model = YOLO(model_path)  # 加载训练好的模型
        model.to(self.device)  # 将模型放到指定设备（GPU 或 CPU）
        return model

    def run(self, frame: CameraFrame) -> dict[str, list[Detection2D]]:
        """
        对输入的图像进行推理
        """
        outputs = {}
        for task, detector in self.detectors.items():
            outputs[task] = detector.detect(frame)
        return outputs

    def run_flat(self, frame: CameraFrame) -> list[Detection2D]:
        """
        对输入的图像进行推理并返回所有任务的合并检测结果。
        """
        merged = []
        for detector in self.detectors.values():
            merged.extend(detector.detect(frame))
        return merged