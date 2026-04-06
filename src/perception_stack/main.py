from __future__ import annotations
import time
import argparse
import os
import cv2

from perception_stack.common.types import Header, CameraFrame
from perception_stack.tracker.tracker2d import Tracker2D
from perception_stack.stabilizer.stabilizer import Stabilizer
from perception_stack.publisher.publisher import Publisher
from perception_stack.visualizer.visualizer import Visualizer
from perception_stack.infer.infer_engine import InferEngine
from perception_stack.capture.opencv_source import OpenCVThreadedCapture
from perception_stack.pipeline import (
    apply_task_flag,
    infer_repo_root_from_config_path,
    load_cfg,
    resolve_repo_relative_model_paths,
    run_infer_pipeline,
)


def real_frame(image_path: str) -> CameraFrame:
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Image not found: {image_path}")
    stamp_ms = int(time.time() * 1000)
    return CameraFrame(header=Header(stamp_ms=stamp_ms, frame_id="cam_front"), image_bgr=img)


def _parse_camera_device(raw) -> int | str:
    if isinstance(raw, int):
        return raw
    s = str(raw).strip()
    if s.isdigit():
        return int(s)
    return s


def run_replay(args, cfg: dict) -> None:
    infer = InferEngine(cfg)
    tracker = Tracker2D()
    stab = Stabilizer(window_len=10, switch_k=3, min_stable_conf=0.6)
    pub = Publisher()
    vis = Visualizer()

    test_dir = os.path.join(args.replay_root, "cam_test")
    image_files = [f for f in os.listdir(test_dir) if f.endswith(".png") or f.endswith(".jpg")]

    for i in range(args.frames):
        if i >= len(image_files):
            break
        image_path = os.path.join(test_dir, image_files[i])
        cam = real_frame(image_path)
        semantic_list = run_infer_pipeline(cam, infer, tracker, stab)

        proc_ms = int(time.time() * 1000)
        latency_ms = proc_ms - cam.header.stamp_ms
        status = {
            "fps": 30,
            "mode": "replay",
            "latency_ms_e2e": latency_ms,
        }
        json_path = pub.publish(cam.header.stamp_ms, semantic_list, status)
        overlay_path = vis.draw(cam, semantic_list, 0)
        print("wrote:", json_path, overlay_path)
        time.sleep(0.2)


def run_live(args, cfg: dict) -> None:
    cap_cfg = cfg.get("capture") or {}
    device = args.camera if args.camera is not None else cap_cfg.get("device", 0)
    device = _parse_camera_device(device)

    src = OpenCVThreadedCapture(
        device=device,
        width=int(cap_cfg.get("width", 1920)),
        height=int(cap_cfg.get("height", 1080)),
        fps=float(cap_cfg.get("fps", 30)),
        queue_size=int(cap_cfg.get("queue_size", 2)),
        frame_id=str(cap_cfg.get("frame_id") or "cam_front"),
        drop_policy=str(cap_cfg.get("drop_policy") or "latest"),
    )

    infer = InferEngine(cfg)
    tracker = Tracker2D()
    stab = Stabilizer(window_len=10, switch_k=3, min_stable_conf=0.6)
    pub = Publisher()
    vis = Visualizer()

    src.start()
    frame_i = 0
    t_fps = time.perf_counter()
    fps_ema = 0.0

    try:
        while args.max_frames is None or frame_i < args.max_frames:
            cam = src.read(timeout=2.0)
            if cam is None:
                print("[live] no frame (timeout), retry...")
                continue

            t0 = time.perf_counter()
            semantic_list = run_infer_pipeline(cam, infer, tracker, stab)
            infer_ms = (time.perf_counter() - t0) * 1000.0

            now_ms = int(time.time() * 1000)
            latency_ms = now_ms - cam.header.stamp_ms

            frame_i += 1
            dt = time.perf_counter() - t_fps
            t_fps = time.perf_counter()
            if dt > 1e-6:
                inst_fps = 1.0 / dt
                fps_ema = inst_fps if fps_ema <= 0 else (0.9 * fps_ema + 0.1 * inst_fps)

            status = {
                "fps": round(fps_ema, 2),
                "mode": "live",
                "latency_ms_e2e": latency_ms,
                "infer_ms": round(infer_ms, 2),
                "capture": src.stats_snapshot(),
            }
            json_path = pub.publish(cam.header.stamp_ms, semantic_list, status)
            overlay_path = vis.draw(cam, semantic_list, frame_i)
            print(f"[live] frame={frame_i} wrote: {json_path} {overlay_path} latency_ms={latency_ms} infer_ms={infer_ms:.1f}")

    except KeyboardInterrupt:
        print("[live] stopped by user")
    finally:
        src.stop()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="replay", choices=["replay", "live"])
    ap.add_argument("--replay_root", default="data/samples/replay_min")
    ap.add_argument("--task", default="traffic_sign", choices=["traffic_light", "traffic_sign"])
    ap.add_argument("--frames", type=int, default=4)
    ap.add_argument("--config", default="configs/pipeline.yaml")
    ap.add_argument("--camera", default=None, help="车端设备：索引 0 或路径 /dev/video0（live）")
    ap.add_argument("--max_frames", type=int, default=None, help="live 下调试：最多处理帧数，默认无限")
    args = ap.parse_args()

    cfg = load_cfg(args.config)
    apply_task_flag(cfg, args.task)
    resolve_repo_relative_model_paths(cfg, infer_repo_root_from_config_path(args.config))

    if args.mode == "live":
        run_live(args, cfg)
    else:
        run_replay(args, cfg)


if __name__ == "__main__":
    main()
