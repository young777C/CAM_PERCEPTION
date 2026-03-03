from typing import List
import numpy as np
from ultralytics import YOLO

from perception_stack.common.types import CameraFrame, Detection2D, ROI2D
from .base import DetectorBase


class TrafficLightDetector(DetectorBase):
    task_name = "traffic_light"

    def __init__(self, cfg):
        super().__init__(cfg)
        # 从配置中读取参数
        self.task = str(cfg.get("task", "detect"))
        self.model_path = cfg.get("model_path")
        if not self.model_path:
            raise ValueError("traffic_light.model_path is required in config")
        self.threshold = float(cfg.get("threshold", 0.3))
        self.iou = float(cfg.get("iou", 0.7))
        self.input_size = tuple(cfg.get("input_size", [640, 640]))
        self.device = str(cfg.get("device", "cpu"))
        self.save = bool(cfg.get("save", False))
        self.verbose = bool(cfg.get("verbose", False))

        # 加载 YOLO 模型（只在初始化时加载一次）
        self.model = YOLO(self.model_path, task=self.task)

    def detect(self, frame: CameraFrame) -> List[Detection2D]:
        """
        对输入帧进行交通灯检测，返回 Detection2D 列表。
        """

        # 获取图像数据（假设 frame.image_bgr 为 BGR numpy 数组，形状 HWC）
        img = frame.image_bgr

        # 使用 YOLO 推理
        results = self.model.predict(
            source=img,
            conf=self.threshold,            # 置信度阈值
            iou=self.iou,                   # 交并比
            device=self.device,             # 推理设备
            imgsz=self.input_size[0],       # 输入尺寸（若 input_size 为 [640,640] 则取 640）
            verbose=self.verbose,           # 关闭详细输出
            save=self.save,                 # 关闭保存
        )

        detections = []
        if not results or len(results) == 0:
            return detections

        # 取第一张图的结果（因为输入单张图）
        result = results[0]
        if result.boxes is None:
            return detections

        # 类别名称映射
        names = result.names  # 例如 {0: 'red', 1: 'yellow', 2: 'green', ...}

        # 遍历每个检测框
        for box in result.boxes:
            # 获取坐标（xyxy 格式）并转换为整数
            xyxy = box.xyxy[0].cpu().numpy()   # [x1, y1, x2, y2]
            conf = float(box.conf[0].cpu())    # 置信度
            cls_id = int(box.cls[0].cpu())     # 类别 ID

            # 再次过滤（冗余保护）
            if conf < self.threshold:
                continue

            # 转换为 ROI2D 所需的 xywh
            x1, y1, x2, y2 = map(int, xyxy)
            w = x2 - x1
            h = y2 - y1
            roi = ROI2D(x=x1, y=y1, w=w, h=h)

            # 获取类别名称作为交通灯状态
            class_name = names[cls_id]   # 假设名称就是 'red'/'yellow'/'green'
            attrs = {"state": class_name}

            # 构建 Detection2D 对象
            detection = Detection2D(
                cam_id=frame.header.frame_id,
                roi=roi,
                class_id=self.task_name,  # 固定为 "traffic_light"
                score=conf,
                attrs=attrs
            )
            detections.append(detection)

        return detections