#!/usr/bin/env python3
"""Shared MOT helpers: parsing, IoU, Hungarian matching, HOTA/CLEAR/Identity metrics.

Chỉ dùng thư viện chuẩn của Python — sinh viên không cần cài thêm gì để chạy
`check_mot_labels.py` và `evaluate_tracking.py` trên máy cá nhân.

Công thức bám theo TrackEval (Luiten et al., HOTA, IJCV 2021) và MOTChallenge:
  - HOTA / DetA / AssA / LocA : trung bình trên 19 ngưỡng alpha 0.05..0.95
  - CLEAR                     : MOTA, MOTP, IDSW tại IoU 0.5
  - Identity                  : IDF1, IDTP, IDFP, IDFN tại IoU 0.5
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path


ALPHAS = [round(0.05 + 0.05 * i, 2) for i in range(19)]  # 0.05 .. 0.95
EPS = 1e-10
DEFAULT_IOU = 0.5


# --------------------------------------------------------------------------- #
# Định dạng MOT 1.1
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class Det:
    """Một bbox trong một frame. Toạ độ pixel, gốc ở góc trên trái."""

    frame: int
    track_id: int
    x: float
    y: float
    w: float
    h: float
    conf: float = 1.0

    @property
    def corners(self) -> tuple[float, float, float, float]:
        return (self.x, self.y, self.x + self.w, self.y + self.h)


class MotFormatError(ValueError):
    """Dòng gt.txt sai định dạng — thông báo kèm đường dẫn và số dòng."""


def parse_mot(path: Path | str, *, min_conf: float = 0.0, drop_ignored: bool = True) -> list[Det]:
    """Đọc một file MOT 1.1 / MOTChallenge.

    Mỗi dòng: frame, track_id, bb_left, bb_top, bb_width, bb_height[, conf[, class[, visibility]]]
    Dòng trống và dòng bắt đầu bằng '#' được bỏ qua.
    `drop_ignored` bỏ các dòng có cột conf = 0 (MOTChallenge dùng 0 = ignored).
    """
    path = Path(path)
    if not path.exists():
        raise MotFormatError(f"không tìm thấy {path}")

    dets: list[Det] = []
    for line_number, raw in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p for p in line.replace(";", ",").split(",") if p.strip() != ""]
        if len(parts) < 6:
            raise MotFormatError(
                f"{path}:{line_number}: cần ít nhất 6 cột "
                f"(frame, track_id, x, y, w, h), đang có {len(parts)}"
            )
        try:
            frame = int(float(parts[0]))
            track_id = int(float(parts[1]))
            x, y, w, h = (float(p) for p in parts[2:6])
            conf = float(parts[6]) if len(parts) > 6 else 1.0
        except ValueError as exc:
            raise MotFormatError(f"{path}:{line_number}: cột không phải số ({exc})") from exc

        if drop_ignored and conf == 0:
            continue
        if conf < min_conf:
            continue
        dets.append(Det(frame, track_id, x, y, w, h, conf))
    return dets


def by_frame(dets: list[Det]) -> dict[int, list[Det]]:
    frames: dict[int, list[Det]] = {}
    for det in dets:
        frames.setdefault(det.frame, []).append(det)
    return frames


def by_track(dets: list[Det]) -> dict[int, list[Det]]:
    tracks: dict[int, list[Det]] = {}
    for det in dets:
        tracks.setdefault(det.track_id, []).append(det)
    for track in tracks.values():
        track.sort(key=lambda d: d.frame)
    return tracks


# --------------------------------------------------------------------------- #
# Hình học
# --------------------------------------------------------------------------- #

def iou(first: Det, second: Det) -> float:
    ax1, ay1, ax2, ay2 = first.corners
    bx1, by1, bx2, by2 = second.corners
    inter_w = min(ax2, bx2) - max(ax1, bx1)
    inter_h = min(ay2, by2) - max(ay1, by1)
    if inter_w <= 0 or inter_h <= 0:
        return 0.0
    intersection = inter_w * inter_h
    union = first.w * first.h + second.w * second.h - intersection
    return intersection / union if union > 0 else 0.0


def iou_matrix(gt: list[Det], pred: list[Det]) -> list[list[float]]:
    return [[iou(g, p) for p in pred] for g in gt]


# --------------------------------------------------------------------------- #
# Hungarian (Jonker-Volgenant, O(n^3)), tối thiểu hoá tổng chi phí
# --------------------------------------------------------------------------- #

def linear_sum_assignment(cost: list[list[float]]) -> list[tuple[int, int]]:
    """Ghép cặp một-một tối ưu. Trả về danh sách (row, col).

    Chấp nhận ma trận chữ nhật; tự chuyển vị khi số hàng > số cột.
    """
    if not cost or not cost[0]:
        return []
    n_rows, n_cols = len(cost), len(cost[0])
    if n_rows > n_cols:
        transposed = [[cost[r][c] for r in range(n_rows)] for c in range(n_cols)]
        return [(r, c) for c, r in linear_sum_assignment(transposed)]

    inf = float("inf")
    n, m = n_rows, n_cols
    u = [0.0] * (n + 1)
    v = [0.0] * (m + 1)
    parent = [0] * (m + 1)   # parent[j] = hàng đang giữ cột j (1-indexed)
    way = [0] * (m + 1)

    for i in range(1, n + 1):
        parent[0] = i
        j0 = 0
        min_value = [inf] * (m + 1)
        used = [False] * (m + 1)
        while True:
            used[j0] = True
            i0 = parent[j0]
            delta = inf
            j1 = 0
            for j in range(1, m + 1):
                if used[j]:
                    continue
                current = cost[i0 - 1][j - 1] - u[i0] - v[j]
                if current < min_value[j]:
                    min_value[j] = current
                    way[j] = j0
                if min_value[j] < delta:
                    delta = min_value[j]
                    j1 = j
            for j in range(m + 1):
                if used[j]:
                    u[parent[j]] += delta
                    v[j] -= delta
                else:
                    min_value[j] -= delta
            j0 = j1
            if parent[j0] == 0:
                break
        while j0:
            j1 = way[j0]
            parent[j0] = parent[j1]
            j0 = j1

    return [(parent[j] - 1, j - 1) for j in range(1, m + 1) if parent[j] != 0]


def maximise(score: list[list[float]]) -> list[tuple[int, int]]:
    """Ghép cặp tối đa hoá tổng điểm."""
    return linear_sum_assignment([[-value for value in row] for row in score])


# --------------------------------------------------------------------------- #
# Chỉ số tracking
# --------------------------------------------------------------------------- #

def _frame_range(gt: list[Det], pred: list[Det]) -> list[int]:
    frames = {d.frame for d in gt} | {d.frame for d in pred}
    return sorted(frames)


def _index_ids(dets: list[Det]) -> dict[int, int]:
    """track_id -> chỉ số 0..n-1, theo thứ tự tăng dần của id."""
    return {track_id: i for i, track_id in enumerate(sorted({d.track_id for d in dets}))}


def hota(gt: list[Det], pred: list[Det]) -> dict[str, float]:
    """HOTA, DetA, AssA, LocA — trung bình trên 19 ngưỡng alpha 0.05..0.95.

    Bám theo TrackEval (Luiten et al. 2021):
      - DetA trả lời "có tìm ra vật thể không" (giống precision/recall của Ngày 2);
      - AssA trả lời "có giữ đúng ID không" — đây mới là phần riêng của tracking;
      - HOTA = sqrt(DetA * AssA): hỏng một trong hai thì HOTA tụt.
    """
    gt_index, pred_index = _index_ids(gt), _index_ids(pred)
    n_gt, n_pred = len(gt_index), len(pred_index)
    if n_gt == 0 or n_pred == 0:
        return dict(HOTA=0.0, DetA=0.0, AssA=0.0, LocA=0.0)

    gt_frames, pred_frames = by_frame(gt), by_frame(pred)
    frames = _frame_range(gt, pred)

    # Bước 1: điểm "khớp toàn cục" giữa từng cặp (track gold, track dự đoán).
    potential = [[0.0] * n_pred for _ in range(n_gt)]
    gt_count = [0] * n_gt
    pred_count = [0] * n_pred
    similarity_cache: dict[int, list[list[float]]] = {}

    for frame in frames:
        gt_dets = gt_frames.get(frame, [])
        pred_dets = pred_frames.get(frame, [])
        sim = iou_matrix(gt_dets, pred_dets)
        similarity_cache[frame] = sim
        for g in gt_dets:
            gt_count[gt_index[g.track_id]] += 1
        for p in pred_dets:
            pred_count[pred_index[p.track_id]] += 1
        for i, g in enumerate(gt_dets):
            row_sum = sum(sim[i])
            for j, p in enumerate(pred_dets):
                col_sum = sum(sim[r][j] for r in range(len(gt_dets)))
                denominator = row_sum + col_sum - sim[i][j]
                if denominator > EPS:
                    potential[gt_index[g.track_id]][pred_index[p.track_id]] += sim[i][j] / denominator

    alignment = [
        [
            potential[i][j] / max(EPS, gt_count[i] + pred_count[j] - potential[i][j])
            for j in range(n_pred)
        ]
        for i in range(n_gt)
    ]

    # Bước 2: ghép cặp từng frame bằng điểm đã "ưu tiên cặp track hay đi cùng nhau".
    tp = [0] * len(ALPHAS)
    fn = [0] * len(ALPHAS)
    fp = [0] * len(ALPHAS)
    loc = [0.0] * len(ALPHAS)
    matches = [[[0] * n_pred for _ in range(n_gt)] for _ in ALPHAS]

    for frame in frames:
        gt_dets = gt_frames.get(frame, [])
        pred_dets = pred_frames.get(frame, [])
        sim = similarity_cache[frame]
        if gt_dets and pred_dets:
            score = [
                [alignment[gt_index[g.track_id]][pred_index[p.track_id]] * sim[i][j]
                 for j, p in enumerate(pred_dets)]
                for i, g in enumerate(gt_dets)
            ]
            pairs = maximise(score)
        else:
            pairs = []
        for a, alpha in enumerate(ALPHAS):
            kept = [(i, j) for i, j in pairs if sim[i][j] >= alpha - EPS]
            tp[a] += len(kept)
            fn[a] += len(gt_dets) - len(kept)
            fp[a] += len(pred_dets) - len(kept)
            for i, j in kept:
                loc[a] += sim[i][j]
                matches[a][gt_index[gt_dets[i].track_id]][pred_index[pred_dets[j].track_id]] += 1

    hota_values, det_values, ass_values, loc_values = [], [], [], []
    for a in range(len(ALPHAS)):
        det_a = tp[a] / max(EPS, tp[a] + fn[a] + fp[a])
        total = 0.0
        for i in range(n_gt):
            for j in range(n_pred):
                count = matches[a][i][j]
                if count:
                    total += count * count / max(1, gt_count[i] + pred_count[j] - count)
        ass_a = total / max(1, tp[a])
        det_values.append(det_a)
        ass_values.append(ass_a)
        hota_values.append(math.sqrt(det_a * ass_a))
        # Không có TP ở alpha cao thì LocA không xác định; TrackEval quy ước là 1.0.
        loc_values.append(loc[a] / tp[a] if tp[a] else 1.0)

    n = len(ALPHAS)
    return dict(
        HOTA=sum(hota_values) / n,
        DetA=sum(det_values) / n,
        AssA=sum(ass_values) / n,
        LocA=sum(loc_values) / n,
    )


def clear_mot(gt: list[Det], pred: list[Det], threshold: float = DEFAULT_IOU) -> dict:
    """MOTA, MOTP, IDSW, FP, FN — và danh sách ID switch để sinh viên đi sửa.

    Ghép cặp mỗi frame có ưu tiên giữ lại cặp của frame trước (đúng như TrackEval),
    nên một ID switch chỉ bị đếm khi tracker/người gán thực sự đổi ID.
    """
    gt_frames, pred_frames = by_frame(gt), by_frame(pred)
    frames = _frame_range(gt, pred)

    previous: dict[int, int] = {}        # gt track_id -> pred track_id đã khớp gần nhất
    previous_frame: dict[int, int] = {}  # gt track_id -> pred track_id ở frame liền trước
    false_positives = false_negatives = switches = 0
    matched_similarity = 0.0
    matched_count = 0
    switch_log: list[dict] = []
    matched_gt_frames: dict[int, int] = {}

    for frame in frames:
        gt_dets = gt_frames.get(frame, [])
        pred_dets = pred_frames.get(frame, [])
        sim = iou_matrix(gt_dets, pred_dets)

        pairs: list[tuple[int, int]] = []
        if gt_dets and pred_dets:
            score = [
                [
                    (1000.0 if previous_frame.get(g.track_id) == p.track_id else 0.0) + sim[i][j]
                    if sim[i][j] >= threshold - EPS else 0.0
                    for j, p in enumerate(pred_dets)
                ]
                for i, g in enumerate(gt_dets)
            ]
            pairs = [(i, j) for i, j in maximise(score) if score[i][j] > EPS]

        current_frame: dict[int, int] = {}
        for i, j in pairs:
            gt_id = gt_dets[i].track_id
            pred_id = pred_dets[j].track_id
            earlier = previous.get(gt_id)
            if earlier is not None and earlier != pred_id:
                switches += 1
                switch_log.append(dict(frame=frame, gt_track=gt_id, from_track=earlier, to_track=pred_id))
            previous[gt_id] = pred_id
            current_frame[gt_id] = pred_id
            matched_similarity += sim[i][j]
            matched_count += 1
            matched_gt_frames[gt_id] = matched_gt_frames.get(gt_id, 0) + 1

        previous_frame = current_frame
        false_negatives += len(gt_dets) - len(pairs)
        false_positives += len(pred_dets) - len(pairs)

    gt_total = len(gt)
    mota = 1.0 - (false_negatives + false_positives + switches) / max(1, gt_total)
    return dict(
        MOTA=mota,
        MOTP=matched_similarity / max(1, matched_count),
        IDSW=switches,
        FP=false_positives,
        FN=false_negatives,
        GT_boxes=gt_total,
        PRED_boxes=len(pred),
        switches=switch_log,
        matched_per_gt_track=matched_gt_frames,
    )


def identity(gt: list[Det], pred: list[Det], threshold: float = DEFAULT_IOU) -> dict[str, float]:
    """IDF1, IDTP, IDFP, IDFN — ghép ID một-một trên toàn clip.

    IDF1 phạt đúng cái mà MOTA bỏ sót: một vật thể bị cắt thành hai ID chỉ tốn
    1 IDSW trong MOTA, nhưng làm hỏng một nửa quãng đời của track trong IDF1.
    """
    gt_index, pred_index = _index_ids(gt), _index_ids(pred)
    n_gt, n_pred = len(gt_index), len(pred_index)
    if n_gt == 0 and n_pred == 0:
        return dict(IDF1=1.0, IDTP=0, IDFP=0, IDFN=0)
    if n_gt == 0 or n_pred == 0:
        return dict(IDF1=0.0, IDTP=0, IDFP=len(pred), IDFN=len(gt))

    gt_frames, pred_frames = by_frame(gt), by_frame(pred)
    potential = [[0] * n_pred for _ in range(n_gt)]
    for frame in _frame_range(gt, pred):
        gt_dets = gt_frames.get(frame, [])
        pred_dets = pred_frames.get(frame, [])
        sim = iou_matrix(gt_dets, pred_dets)
        for i, g in enumerate(gt_dets):
            for j, p in enumerate(pred_dets):
                if sim[i][j] >= threshold - EPS:
                    potential[gt_index[g.track_id]][pred_index[p.track_id]] += 1

    gt_count = [0] * n_gt
    pred_count = [0] * n_pred
    for d in gt:
        gt_count[gt_index[d.track_id]] += 1
    for d in pred:
        pred_count[pred_index[d.track_id]] += 1

    # Ma trận vuông có phần "không ghép": track gold thứ i có thể ở lại một mình
    # (toàn bộ là IDFN), track dự đoán thứ j cũng vậy (toàn bộ là IDFP).
    size = n_gt + n_pred
    big = 1e10
    fn_mat = [[0.0] * size for _ in range(size)]
    fp_mat = [[0.0] * size for _ in range(size)]
    for i in range(n_gt):
        for j in range(n_pred):
            fn_mat[i][j] = gt_count[i] - potential[i][j]
            fp_mat[i][j] = pred_count[j] - potential[i][j]
        for j in range(n_pred, size):
            fn_mat[i][j] = big
        fn_mat[i][n_pred + i] = gt_count[i]
        fp_mat[i][n_pred + i] = 0.0
    for i in range(n_gt, size):
        for j in range(n_pred):
            fp_mat[i][j] = big
    for j in range(n_pred):
        fp_mat[n_gt + j][j] = pred_count[j]
        fn_mat[n_gt + j][j] = 0.0

    cost = [[fn_mat[i][j] + fp_mat[i][j] for j in range(size)] for i in range(size)]
    pairs = linear_sum_assignment(cost)
    id_fn = sum(fn_mat[i][j] for i, j in pairs)
    id_fp = sum(fp_mat[i][j] for i, j in pairs)
    id_tp = len(gt) - id_fn
    denominator = id_tp + 0.5 * id_fn + 0.5 * id_fp
    return dict(
        IDF1=id_tp / denominator if denominator > 0 else 0.0,
        IDTP=int(id_tp), IDFP=int(id_fp), IDFN=int(id_fn),
    )
