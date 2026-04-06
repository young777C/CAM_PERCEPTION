from __future__ import annotations

import queue
import threading
import time
from typing import Literal, Optional

import cv2

from perception_stack.common.types import CameraFrame, Header


class OpenCVThreadedCapture:
    """
    独立线程从 V4L2/USB 等设备取流，与推理线程解耦。
    - latest: 只保留最新一帧，推理慢时自动丢中间帧（低延迟优先）
    - fifo: 有界队列，满时丢弃最旧帧（可追溯短历史）
    时间戳默认使用到达时刻（毫秒）；车端量产应替换为相机/SDK 或 PTP 同步时间。
    """

    def __init__(
        self,
        device: int | str = 0,
        width: int = 1920,
        height: int = 1080,
        fps: float = 30.0,
        queue_size: int = 2,
        frame_id: str = "cam_front",
        drop_policy: Literal["latest", "fifo"] = "latest",
    ) -> None:
        self._device = device
        self._width = int(width)
        self._height = int(height)
        self._fps = float(fps)
        self._queue_size = max(1, int(queue_size))
        self._frame_id = frame_id
        if drop_policy not in ("latest", "fifo"):
            raise ValueError(f"drop_policy must be 'latest' or 'fifo', got {drop_policy!r}")
        self._drop_policy = drop_policy

        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

        self._lock = threading.Lock()
        self._latest: Optional[CameraFrame] = None
        self._fifo: Optional[queue.Queue[CameraFrame]] = None
        if drop_policy == "fifo":
            self._fifo = queue.Queue(maxsize=self._queue_size)

        self._seq = 0
        self._frames_grabbed = 0
        self._frames_dropped = 0
        self._overwrites = 0

    def start(self) -> None:
        if self._thread is not None:
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._capture_loop, name="OpenCVThreadedCapture", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=3.0)
            self._thread = None

    def _capture_loop(self) -> None:
        cap = cv2.VideoCapture(self._device)
        if not cap.isOpened():
            raise RuntimeError(f"Cannot open camera device: {self._device!r}")

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self._width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self._height)
        cap.set(cv2.CAP_PROP_FPS, self._fps)

        while not self._stop.is_set():
            ok, img = cap.read()
            if not ok or img is None:
                time.sleep(0.002)
                continue

            self._frames_grabbed += 1
            self._seq += 1
            stamp_ms = int(time.time() * 1000)
            frame = CameraFrame(
                header=Header(stamp_ms=stamp_ms, frame_id=self._frame_id, seq=self._seq),
                image_bgr=img,
            )

            if self._drop_policy == "latest":
                with self._lock:
                    if self._latest is not None:
                        self._overwrites += 1
                        self._frames_dropped += 1
                    self._latest = frame
            else:
                assert self._fifo is not None
                self._push_fifo(frame)

        cap.release()

    def _push_fifo(self, frame: CameraFrame) -> None:
        assert self._fifo is not None
        try:
            self._fifo.put_nowait(frame)
        except queue.Full:
            try:
                self._fifo.get_nowait()
                self._frames_dropped += 1
            except queue.Empty:
                pass
            try:
                self._fifo.put_nowait(frame)
            except queue.Full:
                self._frames_dropped += 1

    def read(self, timeout: float = 1.0) -> Optional[CameraFrame]:
        """推理线程调用：阻塞直到拿到一帧或超时。"""
        if self._drop_policy == "latest":
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                with self._lock:
                    if self._latest is not None:
                        f = self._latest
                        self._latest = None
                        return f
                time.sleep(0.001)
            return None

        assert self._fifo is not None
        try:
            return self._fifo.get(timeout=timeout)
        except queue.Empty:
            return None

    def stats_snapshot(self) -> dict:
        return {
            "frames_grabbed": self._frames_grabbed,
            "frames_dropped": self._frames_dropped,
            "overwrites_latest": self._overwrites,
            "drop_policy": self._drop_policy,
            "queue_size_config": self._queue_size,
        }
