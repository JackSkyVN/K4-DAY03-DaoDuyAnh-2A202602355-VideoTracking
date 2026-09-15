#!/usr/bin/env python3
"""Chấm một file nhãn tracking (MOT 1.1) với ground truth.

Dùng cho cả ba phép so sánh của Ngày 3:

    # 1. nhãn của bạn  vs  gold      -> chất lượng annotation (cổng qua bài)
    python3 tools/evaluate_tracking.py --pred annotations/clip_01/gt.txt \
        --gt gold/clip_01/gt.txt --seqinfo data/clips/clip_01/seqinfo.ini

    # 2. model          vs  gold      -> model giỏi đến đâu
    python3 tools/evaluate_tracking.py --pred outputs/model_clip_01.txt \
        --gt gold/clip_01/gt.txt --seqinfo data/clips/clip_01/seqinfo.ini

    # 3. model          vs  nhãn của bạn -> chỗ bạn và model không đồng ý
    python3 tools/evaluate_tracking.py --pred outputs/model_clip_01.txt \
        --gt annotations/clip_01/gt.txt --seqinfo data/clips/clip_01/seqinfo.ini

Chỉ dùng thư viện chuẩn. Không cần cài gì thêm.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from motlib import (  # noqa: E402
    DEFAULT_IOU, Det, MotFormatError, by_frame, by_track, clear_mot, hota, identity,
    iou, parse_mot,
)

# Cổng qua bài cho annotation (nhãn của bạn vs gold). Xem RUBRIC.md.
GATE_IDF1 = 0.80
GATE_MOTA = 0.75
GATE_MOTP = 0.70


def read_seqinfo(path: Path | None) -> dict:
    if path is None or not path.exists():
        return {}
    info: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.startswith("["):
            key, _, value = line.partition("=")
            info[key.strip()] = value.strip()
    return info


def diagnose(gt: list[Det], pred: list[Det], clear: dict, threshold: float) -> dict:
    """Biến điểm số thành danh sách việc phải sửa — theo đúng 5 lỗi trong slide."""
    gt_tracks = by_track(gt)
    pred_tracks = by_track(pred)
    gt_frames, pred_frames = by_frame(gt), by_frame(pred)

    # Với mỗi track gold: những track dự đoán nào đã phủ lên nó, và phủ bao nhiêu frame.
    coverage: dict[int, dict[int, int]] = {tid: {} for tid in gt_tracks}
    drift: list[dict] = []
    for frame, gt_dets in gt_frames.items():
        pred_dets = pred_frames.get(frame, [])
        for g in gt_dets:
            best = max(((iou(g, p), p.track_id) for p in pred_dets), default=(0.0, None))
            if best[0] >= threshold:
                coverage[g.track_id][best[1]] = coverage[g.track_id].get(best[1], 0) + 1
                if best[0] < 0.60:
                    drift.append(dict(frame=frame, gt_track=g.track_id, pred_track=best[1],
                                      iou=round(best[0], 3)))

    missed_tracks = [tid for tid, c in coverage.items() if not c]
    fragmented = [
        dict(gt_track=tid, pred_tracks=sorted(c, key=lambda k: -c[k]),
             frames_each={k: c[k] for k in sorted(c, key=lambda k: -c[k])},
             gt_length=len(gt_tracks[tid]))
        for tid, c in coverage.items() if len(c) > 1
    ]
    partial = [
        dict(gt_track=tid, covered=sum(c.values()), gt_length=len(gt_tracks[tid]),
             ratio=round(sum(c.values()) / len(gt_tracks[tid]), 2))
        for tid, c in coverage.items()
        if c and sum(c.values()) < 0.8 * len(gt_tracks[tid])
    ]

    # "Bbox treo": track dự đoán còn bbox ở những frame mà không còn gold nào khớp,
    # và nằm ngoài khoảng sống của track gold mà nó phủ nhiều nhất.
    ghost: list[dict] = []
    for pred_id, dets in pred_tracks.items():
        owners = [tid for tid, c in coverage.items() if pred_id in c]
        if not owners:
            ghost.append(dict(pred_track=pred_id, reason="không khớp track tham chiếu nào",
                              frames=[dets[0].frame, dets[-1].frame], length=len(dets)))
            continue
        owner = max(owners, key=lambda tid: coverage[tid][pred_id])
        gt_first = gt_tracks[owner][0].frame
        gt_last = gt_tracks[owner][-1].frame
        after = [d.frame for d in dets if d.frame > gt_last]
        before = [d.frame for d in dets if d.frame < gt_first]
        if len(after) >= 3:
            ghost.append(dict(pred_track=pred_id, reason=f"còn bbox sau khi track tham chiếu {owner} đã rời khung",
                              frames=[after[0], after[-1]], length=len(after)))
        if len(before) >= 3:
            ghost.append(dict(pred_track=pred_id, reason=f"đã có bbox trước khi track tham chiếu {owner} xuất hiện",
                              frames=[before[0], before[-1]], length=len(before)))

    drift.sort(key=lambda d: d["iou"])
    return dict(
        missed_gt_tracks=sorted(missed_tracks),
        fragmented_gt_tracks=sorted(fragmented, key=lambda d: -len(d["pred_tracks"])),
        partially_covered_gt_tracks=sorted(partial, key=lambda d: d["ratio"]),
        ghost_pred_tracks=sorted(ghost, key=lambda d: -d["length"]),
        id_switches=clear["switches"][:30],
        loose_boxes=drift[:30],
        n_gt_tracks=len(gt_tracks),
        n_pred_tracks=len(pred_tracks),
    )


# Cùng một con số, ba cách đọc khác nhau — tuỳ bạn đang so cái gì với cái gì.
MODE_TITLES = {
    "annotation": (
        "1. ID SWITCH — track gold bị đổi sang ID khác giữa chừng",
        "2. TÁCH TRACK — một vật thể gold bị cắt thành nhiều ID",
        "3. BBOX TREO / BBOX THỪA — ID của bạn tồn tại ở nơi không có vật thể",
        "4. BBOX TRÔI — bbox lệch khỏi vật thể, thường ở giữa hai keyframe",
        "5. BỎ SÓT — track gold không có ID nào của bạn khớp",
        "6. THIẾU ĐOẠN — track có nhãn nhưng không phủ hết quãng đời",
    ),
    "model": (
        "1. ID SWITCH của model — tracker đổi ID giữa chừng",
        "2. TÁCH TRACK — tracker cắt một xe thành nhiều ID (thường sau lúc bị che)",
        "3. BBOX THỪA của model — ID không ứng với xe nào trong gold",
        "4. BBOX LỆCH — detector khoanh chưa khít",
        "5. MODEL BỎ SÓT — xe trong gold mà tracker không bắt được",
        "6. MODEL BẮT THIẾU ĐOẠN — bắt được xe nhưng mất dấu một phần quãng đời",
    ),
    "peer": (
        "1. HAI BẢN LỆCH ID — cùng một xe nhưng hai người theo hai ID khác nhau",
        "2. MỘT BÊN TÁCH TRACK — xe bị chia thành nhiều ID ở một trong hai bản",
        "3. BBOX CHỈ CÓ Ở MỘT BẢN — một người gán, người kia không",
        "4. BBOX LỆCH NHAU — cùng xe nhưng khoanh khác nhau",
        "5. MỘT BÊN BỎ SÓT HẲN — một xe chỉ có ở một bản",
        "6. PHỦ KHÁC NHAU — hai người bắt đầu/kết thúc track ở frame khác nhau",
    ),
}

MODE_HINTS = {
    "annotation": ("-> tách ra rồi Merge lại đúng cặp", "-> gộp lại bằng Merge (M)",
                   "-> bấm outside đúng frame xe rời khung", "-> thêm keyframe quanh đây"),
    "model": ("", "", "", ""),
    "peer": ("", "", "", "-> thống nhất luật khoanh bbox rồi sửa cả hai bản"),
}


def report(result: dict, gate: bool, mode: str = "annotation") -> None:
    m = result["metrics"]
    d = result["diagnostics"]
    w = 74
    print("=" * w)
    print(f"  {result['pred_label']}  vs  {result['gt_label']}")
    print(f"  clip: {result['clip']} · {result['frames']} frame · IoU ngưỡng {result['iou_threshold']}")
    print("=" * w)
    print(f"  HOTA {m['HOTA']:.3f}   = sqrt(DetA x AssA)   -- điểm tổng của tracking")
    print(f"    DetA {m['DetA']:.3f}  tìm đúng vật thể chưa (giống bài toán Ngày 2)")
    print(f"    AssA {m['AssA']:.3f}  giữ đúng ID chưa      (phần riêng của tracking)")
    print(f"    LocA {m['LocA']:.3f}  bbox khít đến đâu")
    print("-" * w)
    print(f"  IDF1 {m['IDF1']:.3f}   MOTA {m['MOTA']:.3f}   MOTP {m['MOTP']:.3f}")
    whose = {"annotation": "của bạn", "model": "của model", "peer": "bản B"}[mode]
    # Ở chế độ peer không có ai là "đáp án", nên gọi hai bên là bản A / bản B.
    ref = "bản A" if mode == "peer" else "gold"
    print(f"  FP {m['FP']}  FN {m['FN']}  ID switch {m['IDSW']}"
          f"   |  bbox {ref} {m['GT_boxes']}  bbox {whose} {m['PRED_boxes']}"
          f"  |  track {ref} {d['n_gt_tracks']}  track {whose} {d['n_pred_tracks']}")
    print("=" * w)

    if gate:
        checks = result["gate"]["checks"]
        print("  CỔNG QUA BÀI")
        for name, item in checks.items():
            mark = "ĐẠT " if item["passed"] else "CHƯA"
            print(f"    [{mark}] {name:5s} {item['value']:.3f}  (cần >= {item['required']:.2f})")
        print(f"  => {'ĐẠT — sang bước chạy model' if result['gate']['passed'] else 'CHƯA ĐẠT — sửa nhãn rồi chạy lại'}")
        print("=" * w)

    def section(title: str, rows: list, render) -> None:
        if not rows:
            return
        print(f"\n  {title}  ({len(rows)})")
        for row in rows[:8]:
            print(f"    - {render(row)}")
        if len(rows) > 8:
            print(f"    ... còn {len(rows) - 8} mục nữa, xem file JSON")

    titles = MODE_TITLES[mode]
    h = MODE_HINTS[mode]
    section(titles[0], d["id_switches"],
            lambda r: f"frame {r['frame']}: track {ref} {r['gt_track']} đang là ID {r['from_track']} -> nhảy sang ID {r['to_track']} {h[0]}".rstrip())
    section(titles[1], d["fragmented_gt_tracks"],
            lambda r: f"track {ref} {r['gt_track']} ({r['gt_length']} frame) bị chia cho ID {r['pred_tracks']} {h[1]}".rstrip())
    section(titles[2], d["ghost_pred_tracks"],
            lambda r: f"ID {r['pred_track']}: {r['reason']} (frame {r['frames'][0]}-{r['frames'][1]}, {r['length']} frame) {h[2]}".rstrip())
    section(titles[3], d["loose_boxes"],
            lambda r: f"frame {r['frame']}: track {ref} {r['gt_track']} chỉ còn IoU {r['iou']:.2f} {h[3]}".rstrip())
    section(titles[4], [dict(t=t) for t in d["missed_gt_tracks"]],
            lambda r: f"track {ref} {r['t']} hoàn toàn không có ID nào khớp")
    section(titles[5], d["partially_covered_gt_tracks"],
            lambda r: f"track {ref} {r['gt_track']}: mới phủ {r['covered']}/{r['gt_length']} frame ({r['ratio']:.0%})")
    print()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--pred", type=Path, required=True, help="file nhãn cần chấm (MOT 1.1)")
    parser.add_argument("--gt", type=Path, required=True, help="file ground truth (MOT 1.1)")
    parser.add_argument("--seqinfo", type=Path, default=None, help="data/clips/<clip>/seqinfo.ini")
    parser.add_argument("--output", type=Path, default=None, help="ghi kết quả đầy đủ ra JSON")
    parser.add_argument("--iou", type=float, default=DEFAULT_IOU, help="ngưỡng IoU cho MOTA/IDF1")
    parser.add_argument("--min-conf", type=float, default=0.0, help="bỏ bbox dự đoán có conf thấp hơn")
    parser.add_argument("--pred-label", default=None)
    parser.add_argument("--gt-label", default=None)
    parser.add_argument("--mode", choices=sorted(MODE_TITLES), default="annotation",
                        help="annotation = nhãn của bạn vs gold (mặc định, có cổng qua bài); "
                             "model = kết quả tracker vs gold; peer = so với bản của bạn cùng nhóm")
    parser.add_argument("--no-gate", action="store_true", help="không in cổng qua bài")
    args = parser.parse_args()

    try:
        gt = parse_mot(args.gt)
        pred = parse_mot(args.pred, min_conf=args.min_conf)
    except MotFormatError as exc:
        print(f"LỖI ĐỊNH DẠNG: {exc}", file=sys.stderr)
        return 2

    if not gt:
        print(f"LỖI: {args.gt} không có dòng nhãn nào.", file=sys.stderr)
        return 2
    if not pred:
        print(f"LỖI: {args.pred} không có dòng nhãn nào. Bạn đã export đúng MOT 1.1 chưa?", file=sys.stderr)
        return 2

    info = read_seqinfo(args.seqinfo)
    clear = clear_mot(gt, pred, args.iou)
    metrics = {**hota(gt, pred), **identity(gt, pred, args.iou),
               **{k: v for k, v in clear.items() if k not in ("switches", "matched_per_gt_track")}}

    gate_checks = {
        "IDF1": dict(value=metrics["IDF1"], required=GATE_IDF1, passed=metrics["IDF1"] >= GATE_IDF1),
        "MOTA": dict(value=metrics["MOTA"], required=GATE_MOTA, passed=metrics["MOTA"] >= GATE_MOTA),
        "MOTP": dict(value=metrics["MOTP"], required=GATE_MOTP, passed=metrics["MOTP"] >= GATE_MOTP),
    }
    result = dict(
        clip=info.get("name", args.seqinfo.parent.name if args.seqinfo else "?"),
        frames=int(info["seqLength"]) if "seqLength" in info else len({d.frame for d in gt}),
        iou_threshold=args.iou,
        pred_file=str(args.pred), gt_file=str(args.gt),
        pred_label=args.pred_label or f"PRED {args.pred}",
        gt_label=args.gt_label or f"GT   {args.gt}",
        metrics={k: (round(v, 4) if isinstance(v, float) else v) for k, v in metrics.items()},
        gate=dict(checks=gate_checks, passed=all(c["passed"] for c in gate_checks.values())),
        diagnostics=diagnose(gt, pred, clear, args.iou),
    )

    report(result, gate=(args.mode == "annotation" and not args.no_gate), mode=args.mode)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"  Đã ghi {args.output}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
