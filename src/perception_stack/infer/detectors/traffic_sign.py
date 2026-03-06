from typing import List, Dict, Any, Tuple
import numpy as np
import cv2
import onnxruntime as ort
from perception_stack.common.types import CameraFrame, Detection2D, ROI2D
from .base import DetectorBase
from ultralytics import YOLO


def letterbox(img_bgr, new_shape=(640, 640), color=(114, 114, 114)):
    """
    Resize and pad the image to the target shape while maintaining aspect ratio.
    """
    h, w = img_bgr.shape[:2]
    nh, nw = new_shape
    r = min(nw / w, nh / h)
    new_unpad = (int(round(w * r)), int(round(h * r)))
    dw, dh = nw - new_unpad[0], nh - new_unpad[1]
    dw /= 2
    dh /= 2
    resized = cv2.resize(img_bgr, new_unpad, interpolation=cv2.INTER_LINEAR)
    top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
    left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
    out = cv2.copyMakeBorder(resized, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color)
    return out, r, (left, top)

def nms_xyxy(boxes, scores, iou_thres=0.5):
    """
    Non-maximum suppression to eliminate redundant bounding boxes.
    """
    x1, y1, x2, y2 = boxes.T
    areas = (x2 - x1 + 1e-6) * (y2 - y1 + 1e-6)
    order = scores.argsort()[::-1]

    keep = []
    while order.size > 0:
        i = order[0]
        keep.append(i)
        if order.size == 1:
            break
        xx1 = np.maximum(x1[i], x1[order[1:]])
        yy1 = np.maximum(y1[i], y1[order[1:]])
        xx2 = np.minimum(x2[i], x2[order[1:]])
        yy2 = np.minimum(y2[i], y2[order[1:]])

        w = np.maximum(0.0, xx2 - xx1)
        h = np.maximum(0.0, yy2 - yy1)
        inter = w * h
        iou = inter / (areas[i] + areas[order[1:]] - inter + 1e-6)

        inds = np.where(iou <= iou_thres)[0]
        order = order[inds + 1]
    return keep

class TrafficSignDetector:
    def __init__(self, cfg):
        self.model = YOLO(cfg['model_path'])
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