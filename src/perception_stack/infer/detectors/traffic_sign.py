from __future__ import annotations
from typing import List, Dict, Any, Tuple
import numpy as np
import cv2

from perception_stack.common.types import CameraFrame, Detection2D, ROI2D
from .base import DetectorBase

def letterbox(img_bgr, new_shape=(640, 640), color=(114,114,114)):
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
    # boxes: [N,4] xyxy
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

class TrafficSignDetector(DetectorBase):
    task_name = "traffic_sign"

    def __init__(self, cfg: Dict[str, Any]):
        super().__init__(cfg)
        self.model_path = cfg.get("model_path")
        self.input_size = tuple(cfg.get("input_size", [640, 640]))
        self.threshold = float(cfg.get("threshold", cfg.get("conf_thres", 0.3)))
        self.nms_iou = float(cfg.get("nms_iou", 0.5))
        self.device = str(cfg.get("device", "cpu"))

        if not self.model_path:
            raise ValueError("traffic_sign.model_path is required in config")

        import onnxruntime as ort
        available = ort.get_available_providers()
        providers = ["CPUExecutionProvider"]
        if self.device.lower() in ["cuda", "gpu"] and "CUDAExecutionProvider" in available:
            providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
        self.sess = ort.InferenceSession(self.model_path, providers=providers)
        self.in_name = self.sess.get_inputs()[0].name
        self.out_names = [o.name for o in self.sess.get_outputs()]

        # TODO：你需要填：class_id -> (type, value)
        # value 没有就填 -1
        self.id2attr: Dict[int, Tuple[str, int]] = {
            0: ("warning", -1),
            1: ("prohibitory", -1),
            2: ("mandatory", -1),
        }

    def _decode_ultralytics(self, out: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        return:
          boxes_xywh: [N,4] (x,y,w,h) in input image pixel
          conf: [N]
          cls_id: [N]
        """
        pred = out
        # 兼容 (1, C, N) / (1, N, C)
        if pred.ndim == 3:
            if pred.shape[1] < pred.shape[2]:
                pred = np.transpose(pred, (0, 2, 1))  # (1,N,C)
            pred = pred[0]
        else:
            raise ValueError(f"unexpected output shape: {pred.shape}")

        C = pred.shape[1]
        # 两种常见： [x,y,w,h,cls...](4+nc) 或 [x,y,w,h,obj,cls...](5+nc)
        if C < 6:
            raise ValueError(f"too few channels: {C}")

        boxes = pred[:, :4]
        rest = pred[:, 4:]
        if rest.shape[1] >= 2:  # 可能含 obj，也可能不含
            # 尝试判断是否有 obj：如果 rest 第一维像 obj（0~1），效果上也能工作
            # 这里用通用策略：假设第一列为 obj，再乘 cls_prob
            obj = rest[:, 0]
            cls_prob = rest[:, 1:]
            cls_id = np.argmax(cls_prob, axis=1)
            cls_score = cls_prob[np.arange(cls_prob.shape[0]), cls_id]
            conf = obj * cls_score
        else:
            cls_id = np.zeros((boxes.shape[0],), dtype=np.int64)
            conf = rest[:, 0]

        return boxes, conf, cls_id.astype(np.int64)

    def detect(self, frame: CameraFrame) -> List[Detection2D]:
        img0 = frame.image_bgr
        ih, iw = img0.shape[:2]

        # 1) preprocess (letterbox + BGR->RGB + CHW + float)
        img, r, (padw, padh) = letterbox(img0, self.input_size)
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        x = img_rgb.astype(np.float32) / 255.0
        x = np.transpose(x, (2, 0, 1))[None, ...]  # 1x3xH xW

        # 2) infer
        outs = self.sess.run(self.out_names, {self.in_name: x})
        out0 = outs[0]

        # 3) decode + threshold
        boxes_xywh, conf, cls_id = self._decode_ultralytics(out0)
        m = conf >= self.threshold
        boxes_xywh, conf, cls_id = boxes_xywh[m], conf[m], cls_id[m]
        if boxes_xywh.shape[0] == 0:
            return []

        # xywh -> xyxy (in letterbox image space)
        xy = boxes_xywh[:, :2]
        wh = boxes_xywh[:, 2:4]
        x1y1 = xy - wh / 2
        x2y2 = xy + wh / 2
        boxes = np.concatenate([x1y1, x2y2], axis=1)

        # NMS
        keep = nms_xyxy(boxes, conf, iou_thres=self.nms_iou)
        boxes, conf, cls_id = boxes[keep], conf[keep], cls_id[keep]

        # 4) map back to original image
        dets: List[Detection2D] = []
        for b, s, c in zip(boxes, conf, cls_id):
            x1, y1, x2, y2 = b
            # undo padding + scale
            x1 = (x1 - padw) / r
            y1 = (y1 - padh) / r
            x2 = (x2 - padw) / r
            y2 = (y2 - padh) / r

            x1 = int(max(0, min(x1, iw - 1)))
            y1 = int(max(0, min(y1, ih - 1)))
            x2 = int(max(0, min(x2, iw - 1)))
            y2 = int(max(0, min(y2, ih - 1)))
            if x2 <= x1 or y2 <= y1:
                continue

            ts_type, ts_value = self.id2attr.get(int(c), ("unknown", -1))
            # 让 stabilizer 更好稳定：把识别结果放进 class_id
            cls_name = ts_type if ts_value < 0 else f"{ts_type}_{ts_value}"

            dets.append(
                Detection2D(
                    cam_id = getattr(frame, "cam_id", None) or getattr(frame.header, "frame_id", "camera"),
                    roi=ROI2D(x=x1, y=y1, w=x2 - x1, h=y2 - y1),
                    class_id=cls_name,
                    score=float(s),
                    attrs={"type": ts_type, "value": int(ts_value)},
                )
            )
        return dets