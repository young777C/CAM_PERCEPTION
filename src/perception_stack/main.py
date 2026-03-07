from __future__ import annotations
import time
import numpy as np
import argparse
import yaml
import os
import cv2

from perception_stack.common.config import load_yaml
from perception_stack.common.types import Header, CameraFrame, Detection2D, ROI2D, SemanticObject2D
from perception_stack.tracker.tracker2d import Tracker2D
from perception_stack.stabilizer.stabilizer import Stabilizer
from perception_stack.publisher.publisher import Publisher
from perception_stack.visualizer.visualizer import Visualizer
from perception_stack.infer.infer_engine import InferEngine

# 读取图像（实际图像）
def real_frame(image_path: str) -> CameraFrame:
    img = cv2.imread(image_path)  # 读取图像
    if img is None:
        raise FileNotFoundError(f"Image not found: {image_path}")
    stamp_ms = int(time.time() * 1000)  # 获取时间戳
    return CameraFrame(header=Header(stamp_ms=stamp_ms, frame_id="cam_front"), image_bgr=img)

def load_cfg(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    return cfg

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="replay", choices=["replay", "fake"])
    ap.add_argument("--replay_root", default="data/samples/replay_min")
    ap.add_argument("--task", default="traffic_sign", choices=["traffic_light", "traffic_sign"])
    ap.add_argument("--frames", type=int, default=4)
    ap.add_argument("--config", default="configs/pipeline.yaml")
    args = ap.parse_args()

    # 加载配置文件
    cfg = load_cfg(args.config)
    
    # 根据任务选择对应的检测器
    if args.task == "traffic_light":
        cfg["enabled_tasks"] = ["traffic_light"]
    elif args.task == "traffic_sign":
        cfg["enabled_tasks"] = ["traffic_sign"]

    infer = InferEngine(cfg)

    tracker = Tracker2D()
    stab = Stabilizer(window_len=10, switch_k=3, min_stable_conf=0.6)
    pub = Publisher()
    vis = Visualizer()

    test_dir = os.path.join(args.replay_root, "cam_test")  # 你可以修改此路径为你的图片文件夹
    image_files = [f for f in os.listdir(test_dir) if f.endswith('.png') or f.endswith('.jpg')]

    for i in range(args.frames):
        if i >= len(image_files):
            break  # 超过文件数量时退出

        image_path = os.path.join(test_dir, image_files[i])
        cam = real_frame(image_path)  # 读取实际图像

        # 使用推理引擎检测
        detections = infer.run_flat(cam)  # 执行推理
        tracks = tracker.update(detections, int(time.time() * 1000))

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

        # 发布推理结果
        status = {"fps": 30}
        json_path = pub.publish(cam.header.stamp_ms, semantic_list, status)
        overlay_path = vis.draw(cam, semantic_list, 0)

        print("wrote:", json_path, overlay_path)
        time.sleep(0.2)

if __name__ == "__main__":
    main()