'''最小功能
输入：detections: list[Detection2D]（每帧）

输出：tracks: list[TrackObject2D]（带 track_id）

关联策略：IoU + 贪心/Hungarian
'''
from typing import List
from perception_stack.common.types import Detection2D, TrackObject2D


def iou(a, b):
    ax1, ay1, ax2, ay2 = a.x, a.y, a.x + a.w, a.y + a.h
    bx1, by1, bx2, by2 = b.x, b.y, b.x + b.w, b.y + b.h

    inter_x1 = max(ax1, bx1)
    inter_y1 = max(ay1, by1)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)

    if inter_x2 <= inter_x1 or inter_y2 <= inter_y1:
        return 0.0

    inter_area = (inter_x2 - inter_x1) * (inter_y2 - inter_y1)
    area_a = a.w * a.h
    area_b = b.w * b.h
    union = area_a + area_b - inter_area
    return inter_area / union


class Tracker2D:
    def __init__(self, iou_thres=0.3, max_age=3):
        self.iou_thres = iou_thres
        self.max_age = max_age
        self.next_id = 1
        self.tracks: List[TrackObject2D] = []

    def update(self, detections: List[Detection2D], stamp_ms: int):
        updated_tracks = []
        used = set()

        # 匹配已有 track
        for t in self.tracks:
            best_iou = 0
            best_det = None
            best_idx = -1

            for i, d in enumerate(detections):
                if i in used:
                    continue
                score = iou(t.roi, d.roi)
                if score > best_iou:
                    best_iou = score
                    best_det = d
                    best_idx = i

            if best_iou >= self.iou_thres and best_det is not None:
                used.add(best_idx)
                t.roi = best_det.roi
                t.class_id = best_det.class_id
                t.score = best_det.score
                t.age += 1
                t.last_seen_ms = stamp_ms
                updated_tracks.append(t)

        # 新建未匹配 detection
        for i, d in enumerate(detections):
            if i in used:
                continue
            new_track = TrackObject2D(
                track_id=self.next_id,
                cam_id=d.cam_id,
                roi=d.roi,
                class_id=d.class_id,
                score=d.score,
                age=1,
                last_seen_ms=stamp_ms,
                attrs=d.attrs
            )
            self.next_id += 1
            updated_tracks.append(new_track)

        self.tracks = updated_tracks
        return self.tracks