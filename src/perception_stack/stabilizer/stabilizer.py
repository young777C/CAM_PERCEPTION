from __future__ import annotations
from collections import deque, defaultdict
from typing import Deque, Dict, Tuple

class Stabilizer:
    """
    track_id 状态机、加权投票、切换抑制
    """
    def __init__(self, window_len: int = 10, switch_k: int = 3, min_stable_conf: float = 0.6):
        self.window_len = window_len
        self.switch_k = switch_k
        self.min_stable_conf = min_stable_conf
        self.hist: Dict[int, Deque[Tuple[str, float]]] = defaultdict(lambda: deque(maxlen=self.window_len))
        self.last_stable: Dict[int, Tuple[str, float]] = {}        # track_id -> (class, conf)
        self.cand_cnt: Dict[int, Tuple[str, int, float]] = {}      # track_id -> (cand_class, cnt, conf_sum)

    def update(self, track_id: int, cls: str, conf: float) -> Tuple[str, float, bool]:
        self.hist[track_id].append((cls, conf))

        # 加权投票
        score = defaultdict(float)
        for c, p in self.hist[track_id]:
            score[c] += p
        stable_cls = max(score.items(), key=lambda x: x[1])[0]
        stable_conf = score[stable_cls] / max(1e-6, sum(score.values()))

        # 切换抑制：从 last_stable 切到 stable_cls 需要连续 switch_k 帧
        suppressed = False
        last = self.last_stable.get(track_id, (stable_cls, stable_conf))
        last_cls, last_conf = last

        if stable_cls != last_cls:
            cand_cls, cnt, conf_sum = self.cand_cnt.get(track_id, (stable_cls, 0, 0.0))
            if cand_cls != stable_cls:
                cand_cls, cnt, conf_sum = stable_cls, 0, 0.0
            cnt += 1
            conf_sum += stable_conf
            self.cand_cnt[track_id] = (cand_cls, cnt, conf_sum)

            if cnt < self.switch_k or (conf_sum / cnt) < self.min_stable_conf:
                # 不允许切换
                suppressed = True
                return last_cls, last_conf, suppressed
            # 允许切换
            self.last_stable[track_id] = (stable_cls, stable_conf)
            self.cand_cnt.pop(track_id, None)
            return stable_cls, stable_conf, suppressed

        # 没切换
        self.last_stable[track_id] = (stable_cls, stable_conf)
        self.cand_cnt.pop(track_id, None)
        return stable_cls, stable_conf, suppressed
