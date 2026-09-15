#!/usr/bin/env python3
"""Kiểm tra file nhãn tracking TRƯỚC khi nộp — chạy được mà không cần ground truth.

    python3 tools/check_mot_labels.py --clip data/clips/clip_01 \
        --tracks annotations/clip_01/gt.txt

Bắt được các lỗi định dạng và các lỗi "nhìn là biết sai" mà không cần đáp án:
frame ngoài khoảng, bbox lòi khỏi ảnh, một ID xuất hiện hai lần trong cùng frame,
track đứng im hàng chục frame (dấu hiệu quên bấm outside), track quá ngắn.

LỖI  = phải sửa, nộp vào là hỏng.
CẢNH BÁO = có thể đúng, nhưng phải tự kiểm lại một lượt rồi mới nộp.

Chạy đạt KHÔNG chứng minh nhãn đúng — nó chỉ chứng minh nhãn hợp lệ.
Bbox khít hay không, ID có nhảy hay không thì vẫn phải tự xem bằng mắt
(`tools/visualize_tracks.py`) và đợi chấm với gold.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from motlib import MotFormatError, by_frame, by_track, parse_mot  # noqa: E402

SHORT_TRACK = 5       # track ngắn hơn ngần này frame thì đáng ngờ
STATIC_RUN = 15       # bbox gần như không đổi suốt ngần này frame -> nghi quên outside
STATIC_PIXELS = 1.5   # ngưỡng "gần như không đổi", tính bằng pixel


def read_seqinfo(clip: Path) -> dict[str, str]:
    path = clip / "seqinfo.ini"
    if not path.exists():
        return {}
    info: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.startswith("["):
            key, _, value = line.partition("=")
            info[key.strip()] = value.strip()
    return info


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--clip", type=Path, required=True, help="data/clips/<clip>")
    parser.add_argument("--tracks", type=Path, required=True, help="file MOT 1.1 cần kiểm")
    args = parser.parse_args()

    info = read_seqinfo(args.clip)
    n_frames = int(info.get("seqLength", 0))
    width = int(info.get("imWidth", 0))
    height = int(info.get("imHeight", 0))

    try:
        dets = parse_mot(args.tracks, drop_ignored=False)
    except MotFormatError as exc:
        print(f"LỖI: {exc}")
        print("\nGợi ý: CVAT phải export ở định dạng 'MOT 1.1'. Nếu bạn export YOLO thì track_id bị mất.")
        return 1

    errors: list[str] = []
    warnings: list[str] = []

    if not dets:
        print(f"LỖI: {args.tracks} không có dòng nào.")
        return 1

    # --- frame đánh số từ 0 hay từ 1? ---
    # Một số công cụ export frame bắt đầu từ 0. Lệch một frame làm hỏng toàn bộ
    # điểm số, nên bắt riêng và chỉ ra cách sửa thay vì báo 190 lỗi "ngoài khoảng".
    observed = sorted({d.frame for d in dets})
    if n_frames and observed[0] == 0 and observed[-1] == n_frames - 1:
        print("=" * 70)
        print(f"  LỖI: frame trong file đánh số 0..{n_frames - 1}, nhưng MOT 1.1 đánh số 1..{n_frames}.")
        print("  Công cụ của bạn đã export lệch một frame. Sửa bằng:")
        print(f"      awk -F, 'BEGIN{{OFS=\",\"}}{{$1=$1+1; print}}' {args.tracks} > /tmp/fixed.txt")
        print(f"      mv /tmp/fixed.txt {args.tracks}")
        print("=" * 70)
        return 1

    # --- lỗi từng dòng ---
    seen: dict[tuple[int, int], int] = {}
    for det in dets:
        if n_frames and not (1 <= det.frame <= n_frames):
            errors.append(f"frame {det.frame} nằm ngoài khoảng 1..{n_frames} (track {det.track_id})")
        if det.track_id < 0:
            errors.append(f"frame {det.frame}: track_id phải >= 0, đang là {det.track_id}")
        if det.w <= 0 or det.h <= 0:
            errors.append(f"frame {det.frame} track {det.track_id}: width/height phải > 0")
        if width and height:
            x2, y2 = det.x + det.w, det.y + det.h
            if det.x < -1 or det.y < -1 or x2 > width + 1 or y2 > height + 1:
                errors.append(
                    f"frame {det.frame} track {det.track_id}: bbox ({det.x:.0f},{det.y:.0f},"
                    f"{x2:.0f},{y2:.0f}) lòi khỏi ảnh {width}x{height}"
                )
        key = (det.frame, det.track_id)
        seen[key] = seen.get(key, 0) + 1

    for (frame, track_id), count in sorted(seen.items()):
        if count > 1:
            errors.append(f"frame {frame}: ID {track_id} xuất hiện {count} lần trong cùng một frame")

    # --- cảnh báo mức track ---
    tracks = by_track(dets)
    frames = by_frame(dets)

    for track_id, track in sorted(tracks.items()):
        span = [d.frame for d in track]
        if len(track) < SHORT_TRACK:
            warnings.append(f"track {track_id} chỉ có {len(track)} frame ({span[0]}-{span[-1]}) — vẽ nhầm hay vật thể thật?")

        gaps = [(a, b) for a, b in zip(span, span[1:]) if b - a > 1]
        for a, b in gaps[:3]:
            warnings.append(
                f"track {track_id} đứt quãng frame {a} -> {b}: nếu vật thể bị che rồi hiện lại "
                f"thì giữ ID là ĐÚNG; nếu nó rời khung rồi quay lại thì xem lại luật trong GUIDELINE_MINI.md"
            )

        run = 1
        for previous, current in zip(track, track[1:]):
            moved = (abs(previous.x - current.x) + abs(previous.y - current.y)
                     + abs(previous.w - current.w) + abs(previous.h - current.h))
            run = run + 1 if (moved < STATIC_PIXELS and current.frame == previous.frame + 1) else 1
            if run == STATIC_RUN:
                warnings.append(
                    f"track {track_id}: bbox gần như đứng im từ frame {current.frame - STATIC_RUN + 1} "
                    f"đến {current.frame} — vật thể thật đứng yên, hay bạn quên bấm outside?"
                )

    labelled = sorted(frames)
    if n_frames:
        missing = [f for f in range(1, n_frames + 1) if f not in frames]
        if missing:
            warnings.append(
                f"{len(missing)} frame không có bbox nào (ví dụ {missing[:6]}) — "
                f"đúng nếu lúc đó đường trống, sai nếu bạn chưa gán hết clip"
            )

    # --- báo cáo ---
    counts = [len(v) for v in frames.values()]
    print("=" * 70)
    print(f"  {args.tracks}")
    print(f"  clip {info.get('name', args.clip.name)} · {n_frames or '?'} frame · {width}x{height}")
    print("-" * 70)
    print(f"  {len(dets)} bbox · {len(tracks)} track · frame có nhãn: {labelled[0]}..{labelled[-1]}")
    print(f"  bbox/frame: min {min(counts)} · max {max(counts)} · trung bình {sum(counts)/len(counts):.2f}")
    print(f"  ID đã dùng: {sorted(tracks)}")
    print("=" * 70)

    for message in errors[:40]:
        print(f"  LỖI       {message}")
    if len(errors) > 40:
        print(f"  ... còn {len(errors) - 40} lỗi nữa")
    for message in warnings[:25]:
        print(f"  CẢNH BÁO  {message}")
    if len(warnings) > 25:
        print(f"  ... còn {len(warnings) - 25} cảnh báo nữa")

    print("-" * 70)
    if errors:
        print(f"  KHÔNG ĐẠT: {len(errors)} lỗi, {len(warnings)} cảnh báo. Sửa hết LỖI rồi chạy lại.")
        return 1
    print(f"  ĐẠT phần định dạng: 0 lỗi, {len(warnings)} cảnh báo.")
    print("  Bước tiếp theo: xem lại bằng mắt (tools/visualize_tracks.py) theo ba lượt tua trong GUIDE.md.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
