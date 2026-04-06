from abc import ABC, abstractmethod
from typing import List, Dict, Any
from perception_stack.common.types import CameraFrame, Detection2D


class DetectorBase(ABC):
    task_name: str

    def __init__(self, cfg: Dict[str, Any]):
        self.cfg = cfg

    @abstractmethod
    def detect(self, frame: CameraFrame) -> List[Detection2D]:
        pass