#!/usr/bin/env python3
"""Chạy detector + tracker trên một clip và xuất kết quả ra đúng định dạng MOT 1.1.

    python3 tools/run_tracker.py --clip data/clips/clip_01 \
        --model yolo26n.pt --tracker bytetrack.yaml \
        --out outputs/model_clip_01.txt

Đây chính là "tracking-by-detection" trong slide: YOLO tìm bbox trên từng frame,
ByteTrack nối các bbox đó qua thời gian bằng Kalman + IoU. File xuất ra đọc được
bằng cùng `tools/evaluate_tracking.py` đã dùng để chấm nhãn tay, nên có thể so
sánh ba chiều: nhãn của bạn / nhãn model / gold.

Cần `pip install ultralytics`. Chạy được trên CPU, nhưng Colab có GPU sẽ nhanh hơn.
"""

from __future__ import annotations

import argparse
from pathlib import Path

# COCO không có lớp "van"; van bị model xếp vào car hoặc truck.
# Gold của lab chỉ gán xe bốn bánh, nên KHÔNG lấy motorcycle/bicycle/person.
COCO_VEHICLES = {2: "car", 5: "bus", 7: "truck"}


def track_clip(clip: Path, model_name: str, tracker: str, conf: float, iou: float,
               imgsz: int, classes: list[int], device: str | None = None,
               verbose: bool = True) -> list[tuple[int, int, float, float, float, float, float]]:
    """Trả về list (frame, track_id, x, y, w, h, conf) với frame đánh số từ 1."""
    from ultralytics import YOLO

    images = sorted((clip / "img1").glob("*.jpg"))
    if not images:
        raise SystemExit(f"Không thấy ảnh trong {clip / 'img1'}")

    model = YOLO(model_name)
    rows: list[tuple[int, int, float, float, float, float, float]] = []

    for index, image_path in enumerate(images, start=1):
        # persist=True giữ trạng thái tracker giữa các frame — thiếu nó thì mỗi
        # frame là một clip mới và track_id bị đánh lại từ đầu.
        results = model.track(
            source=str(image_path), persist=True, tracker=tracker,
            conf=conf, iou=iou, imgsz=imgsz, classes=classes,
            device=device, verbose=False,
        )
        boxes = results[0].boxes
        if boxes is None or boxes.id is None:
            continue
        for xyxy, track_id, score in zip(
            boxes.xyxy.tolist(), boxes.id.int().tolist(), boxes.conf.tolist()
        ):
            x1, y1, x2, y2 = xyxy
            rows.append((index, int(track_id), x1, y1, x2 - x1, y2 - y1, score))

        if verbose and index % 25 == 0:
            print(f"  frame {index}/{len(images)} · {len(rows)} bbox tích luỹ")

    return rows


def write_mot(rows, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            f"{f},{t},{x:.2f},{y:.2f},{w:.2f},{h:.2f},{c:.4f},-1,-1,-1"
            for f, t, x, y, w, h, c in sorted(rows)
        ) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--clip", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--model", default="yolo26n.pt")
    parser.add_argument("--tracker", default="bytetrack.yaml", help="bytetrack.yaml hoặc botsort.yaml")
    parser.add_argument("--conf", type=float, default=0.25, help="ngưỡng confidence của detector")
    parser.add_argument("--iou", type=float, default=0.7, help="ngưỡng NMS")
    parser.add_argument("--imgsz", type=int, default=960)
    parser.add_argument("--device", default=None, help="ví dụ 0 cho GPU, cpu cho CPU")
    parser.add_argument("--classes", default="2,5,7",
                        help=f"class id COCO, mặc định xe bốn bánh {COCO_VEHICLES}")
    args = parser.parse_args()

    classes = [int(c) for c in args.classes.split(",") if c.strip()]
    print(f"Model {args.model} · tracker {args.tracker} · conf {args.conf} · imgsz {args.imgsz}")
    print(f"Lớp COCO dùng: {[COCO_VEHICLES.get(c, c) for c in classes]}")

    rows = track_clip(args.clip, args.model, args.tracker, args.conf, args.iou,
                      args.imgsz, classes, args.device)
    write_mot(rows, args.out)
    tracks = {r[1] for r in rows}
    print(f"Đã ghi {args.out}: {len(rows)} bbox · {len(tracks)} track")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
