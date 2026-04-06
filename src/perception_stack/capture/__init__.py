"""车端/实时采集：与推理解耦的帧源抽象与 OpenCV 实现。"""

from perception_stack.capture.opencv_source import OpenCVThreadedCapture

__all__ = ["OpenCVThreadedCapture"]
