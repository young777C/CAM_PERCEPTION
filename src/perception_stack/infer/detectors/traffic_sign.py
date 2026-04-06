from perception_stack.common.config import resolve_model_path
from perception_stack.common.types import Detection2D, ROI2D
from .base import DetectorBase
from ultralytics import YOLO

class TrafficSignDetector_PT:
    def __init__(self, cfg):
        mp = resolve_model_path(cfg.get("model_path"))
        if not mp:
            raise ValueError("traffic_sign.model_path is required in config")
        self.model = YOLO(mp)
        self.conf_thres = cfg.get('threshold', 0.25)
    
    def detect(self, frame):
        results = self.model.predict(frame.image_bgr, conf=self.conf_thres)
        dets = []
        for r in results:
            for xyxy, conf, cls in zip(r.boxes.xyxy, r.boxes.conf, r.boxes.cls):
                x1, y1, x2, y2 = xyxy
                roi = ROI2D(x1, y1, x2-x1, y2-y1)
                dets.append(Detection2D(frame.header.frame_id, roi, str(int(cls)), conf.item()))
        return dets
    
class TrafficSignDetector_ONNX:
    def __init__(self, cfg):
        mp = resolve_model_path(cfg.get("model_path"))
        if not mp:
            raise ValueError("traffic_sign.model_path is required in config")
        self.model = YOLO(mp)
        self.conf = float(cfg.get("threshold", 0.25))
        self.imgsz = cfg.get("imgsz", 640)

    def detect(self, frame):
        rs = self.model.predict(frame.image_bgr, imgsz=self.imgsz, conf=self.conf, verbose=False)
        dets = []
        for r in rs:
            for b in r.boxes:
                x1, y1, x2, y2 = b.xyxy[0].tolist()
                dets.append(Detection2D(
                    cam_id=frame.header.frame_id,
                    roi=ROI2D(int(x1), int(y1), int(x2-x1), int(y2-y1)),
                    class_id=str(int(b.cls.item())),
                    score=float(b.conf.item()),
                    attrs={}
                ))
        return dets