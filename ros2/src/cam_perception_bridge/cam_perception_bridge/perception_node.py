"""ROS2 节点：发布 vision_msgs/Detection2DArray，与 perception_stack 管线一致。"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import rclpy
from rclpy.node import Node

from builtin_interfaces.msg import Time
from geometry_msgs.msg import Pose, PoseWithCovariance, Quaternion
from std_msgs.msg import Header
from vision_msgs.msg import (
    BoundingBox2D,
    Detection2DArray,
    Detection2D,
    ObjectHypothesis,
    ObjectHypothesisWithPose,
    Pose2D,
    Point2D,
)


def _repo_root_from_node_file() -> Path:
    # .../CAM_PERCEPTION/ros2/src/cam_perception_bridge/cam_perception_bridge/perception_node.py
    return Path(__file__).resolve().parents[4]


def _resolve_repo_root(param_from_user: str) -> Path:
    """Locate repo root so ``src/perception_stack`` can be added to ``sys.path``."""
    if param_from_user.strip():
        return Path(param_from_user).resolve()
    env = os.environ.get("CAM_PERCEPTION_ROOT", "").strip()
    if env:
        return Path(env).resolve()
    candidate = _repo_root_from_node_file()
    if (candidate / "src" / "perception_stack").is_dir():
        return candidate
    raise RuntimeError(
        "Cannot find CAM_PERCEPTION repo (no src/perception_stack). "
        "Set environment CAM_PERCEPTION_ROOT or ROS parameter cam_perception_root."
    )


def _ensure_perception_stack_on_path(repo_root: Path) -> None:
    src = str(repo_root / "src")
    if src not in sys.path:
        sys.path.insert(0, src)


def _stamp_from_stamp_ms(stamp_ms: int) -> Time:
    t = Time()
    t.sec = int(stamp_ms // 1000)
    t.nanosec = int((stamp_ms % 1000) * 1_000_000)
    return t


def _identity_pose_with_covariance() -> PoseWithCovariance:
    pwc = PoseWithCovariance()
    pwc.pose.pose = Pose()
    pwc.pose.pose.orientation = Quaternion(w=1.0)
    return pwc


def semantic_list_to_detection2d_array(
    semantic_list,
    stamp_ms: int,
    frame_id: str,
) -> Detection2DArray:
    out = Detection2DArray()
    out.header = Header()
    out.header.stamp = _stamp_from_stamp_ms(stamp_ms)
    out.header.frame_id = frame_id

    for semantic in semantic_list:
        cls_id = semantic.stable_class_id if semantic.stable_class_id else semantic.class_id
        score = float(
            semantic.stable_conf if semantic.stable_conf is not None else semantic.class_conf
        )

        roi = semantic.roi2d
        cx = float(roi.x) + float(roi.w) * 0.5
        cy = float(roi.y) + float(roi.h) * 0.5

        det = Detection2D()
        det.header = Header()
        det.header.stamp = out.header.stamp
        det.header.frame_id = frame_id

        bbox = BoundingBox2D()
        bbox.center = Pose2D()
        bbox.center.position = Point2D()
        bbox.center.position.x = cx
        bbox.center.position.y = cy
        bbox.center.theta = 0.0
        bbox.size_x = float(roi.w)
        bbox.size_y = float(roi.h)
        det.bbox = bbox

        hyp = ObjectHypothesisWithPose()
        hyp.hypothesis = ObjectHypothesis()
        hyp.hypothesis.class_id = str(cls_id)
        hyp.hypothesis.score = score
        hyp.pose = _identity_pose_with_covariance()
        det.results.append(hyp)

        det.id = str(semantic.track_id)
        out.detections.append(det)

    return out


class CamPerceptionBridgeNode(Node):
    def __init__(self) -> None:
        super().__init__("cam_perception_bridge")

        self.declare_parameter("cam_perception_root", "")
        self.declare_parameter("pipeline_config", "configs/pipeline.yaml")
        self.declare_parameter("task", "traffic_sign")
        self.declare_parameter("source", "replay")
        self.declare_parameter("replay_root", "data/samples/replay_min")
        self.declare_parameter("camera", "")
        self.declare_parameter("publish_topic", "/camera_perception/detections")
        self.declare_parameter("timer_period_s", 0.1)
        self.declare_parameter("max_frames", 0)

        root = self.get_parameter("cam_perception_root").get_parameter_value().string_value
        self._repo_root = _resolve_repo_root(root)
        _ensure_perception_stack_on_path(self._repo_root)

        import cv2

        from perception_stack.capture.opencv_source import OpenCVThreadedCapture
        from perception_stack.infer.infer_engine import InferEngine
        from perception_stack.pipeline import apply_task_flag, load_cfg, run_infer_pipeline
        from perception_stack.stabilizer.stabilizer import Stabilizer
        from perception_stack.tracker.tracker2d import Tracker2D
        from perception_stack.common.types import CameraFrame, Header as CamHeader

        self._cv2 = cv2
        self._run_infer_pipeline = run_infer_pipeline
        self._CameraFrame = CameraFrame
        self._CamHeader = CamHeader

        cfg_path = self.get_parameter("pipeline_config").get_parameter_value().string_value
        task = self.get_parameter("task").get_parameter_value().string_value
        source = self.get_parameter("source").get_parameter_value().string_value
        replay_root = self.get_parameter("replay_root").get_parameter_value().string_value
        camera = self.get_parameter("camera").get_parameter_value().string_value
        topic = self.get_parameter("publish_topic").get_parameter_value().string_value
        period = self.get_parameter("timer_period_s").get_parameter_value().double_value
        max_frames = self.get_parameter("max_frames").get_parameter_value().integer_value

        abs_cfg = self._repo_root / cfg_path
        if not abs_cfg.is_file():
            self.get_logger().fatal(f"Config not found: {abs_cfg}")
            raise RuntimeError(f"Config not found: {abs_cfg}")

        cfg = load_cfg(str(abs_cfg))
        apply_task_flag(cfg, task)

        self._infer = InferEngine(cfg)
        self._tracker = Tracker2D()
        self._stab = Stabilizer(window_len=10, switch_k=3, min_stable_conf=0.6)

        self._source = source
        self._frame_id = str((cfg.get("capture") or {}).get("frame_id") or "cam_front")
        self._replay_dir = self._repo_root / replay_root / "cam_test"
        self._replay_files: list[str] = []
        self._replay_idx = 0
        self._src = None
        self._frame_count = 0
        self._max_frames = max_frames if max_frames > 0 else None

        if source == "replay":
            if self._replay_dir.is_dir():
                self._replay_files = sorted(
                    f
                    for f in os.listdir(self._replay_dir)
                    if f.endswith(".png") or f.endswith(".jpg")
                )
            if not self._replay_files:
                self.get_logger().error(
                    f"No images under {self._replay_dir}; replay will publish empty detections."
                )
        elif source == "live":
            cap_cfg = cfg.get("capture") or {}
            dev = camera
            if not dev:
                dev = cap_cfg.get("device", 0)
            if isinstance(dev, str) and dev.isdigit():
                dev = int(dev)
            self._src = OpenCVThreadedCapture(
                device=dev,
                width=int(cap_cfg.get("width", 1920)),
                height=int(cap_cfg.get("height", 1080)),
                fps=float(cap_cfg.get("fps", 30)),
                queue_size=int(cap_cfg.get("queue_size", 2)),
                frame_id=self._frame_id,
                drop_policy=str(cap_cfg.get("drop_policy") or "latest"),
            )
            self._src.start()
        else:
            raise ValueError(f"Unknown source: {source}")

        self._pub = self.create_publisher(Detection2DArray, topic, 10)
        self.get_logger().info(
            f"cam_perception_bridge: topic={topic} source={source} repo={self._repo_root}"
        )

        if period <= 0.0:
            period = 0.05
        self._timer = self.create_timer(period, self._on_timer)

    def _on_timer(self) -> None:
        if self._max_frames is not None and self._frame_count >= self._max_frames:
            return

        cam = None
        if self._source == "replay":
            if not self._replay_files:
                return
            path = self._replay_dir / self._replay_files[self._replay_idx]
            self._replay_idx = (self._replay_idx + 1) % len(self._replay_files)
            img = self._cv2.imread(str(path))
            if img is None:
                self.get_logger().warn(f"Failed to read {path}")
                return
            stamp_ms = int(time.time() * 1000)
            cam = self._CameraFrame(
                header=self._CamHeader(stamp_ms=stamp_ms, frame_id=self._frame_id),
                image_bgr=img,
            )
        else:
            cam = self._src.read(timeout=0.05)
            if cam is None:
                return

        semantic_list = self._run_infer_pipeline(
            cam, self._infer, self._tracker, self._stab
        )
        msg = semantic_list_to_detection2d_array(
            semantic_list, cam.header.stamp_ms, self._frame_id
        )
        self._pub.publish(msg)
        self._frame_count += 1
        if self._frame_count % 30 == 0:
            self.get_logger().info(
                f"Published detections={len(msg.detections)} stamp_ms={cam.header.stamp_ms}"
            )

    def destroy_node(self) -> None:
        if self._src is not None:
            self._src.stop()
        super().destroy_node()


def main(args=None) -> None:
    rclpy.init(args=args)
    node = CamPerceptionBridgeNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
