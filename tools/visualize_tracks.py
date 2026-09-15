#!/usr/bin/env python3
"""Vẽ nhãn tracking lên frame để xem bằng mắt — tầng 1 của quy trình kiểm tra.

    # xem nhãn của mình
    python3 tools/visualize_tracks.py --clip data/clips/clip_01 \
        --tracks annotations/clip_01/gt.txt --out outputs/vis_clip_01

    # xem nhãn của mình (xanh) chồng lên gold (trắng, nét đứt)
    python3 tools/visualize_tracks.py --clip data/clips/clip_01 \
        --tracks annotations/clip_01/gt.txt --compare gold/clip_01/gt.txt \
        --out outputs/vis_vs_gold --only-frames 100-140

Cần Pillow (`pip install pillow`). Nếu có sẵn OpenCV, thêm `--video out.mp4`
để ghép luôn thành video xem cho nhanh.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from motlib import by_frame, parse_mot  # noqa: E402

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:  # pragma: no cover
    raise SystemExit("Cần Pillow: pip install pillow")

# Bảng màu ổn định theo track_id — cùng một ID luôn ra cùng một màu.
PALETTE = [
    (239, 71, 111), (6, 214, 160), (255, 209, 102), (17, 138, 178),
    (155, 93, 229), (241, 91, 181), (0, 187, 249), (0, 245, 212),
    (254, 127, 45), (76, 201, 240), (181, 23, 158), (114, 224, 106),
]


def colour(track_id: int) -> tuple[int, int, int]:
    return PALETTE[track_id % len(PALETTE)]


def parse_frame_filter(spec: str | None) -> set[int] | None:
    if not spec:
        return None
    frames: set[int] = set()
    for chunk in spec.split(","):
        chunk = chunk.strip()
        if "-" in chunk:
            start, _, end = chunk.partition("-")
            frames.update(range(int(start), int(end) + 1))
        elif chunk:
            frames.add(int(chunk))
    return frames


def dashed_rectangle(draw: ImageDraw.ImageDraw, box: tuple[float, float, float, float],
                     fill: tuple[int, int, int], dash: int = 7) -> None:
    x1, y1, x2, y2 = box
    for x in range(int(x1), int(x2), dash * 2):
        draw.line([(x, y1), (min(x + dash, x2), y1)], fill=fill, width=2)
        draw.line([(x, y2), (min(x + dash, x2), y2)], fill=fill, width=2)
    for y in range(int(y1), int(y2), dash * 2):
        draw.line([(x1, y), (x1, min(y + dash, y2))], fill=fill, width=2)
        draw.line([(x2, y), (x2, min(y + dash, y2))], fill=fill, width=2)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--clip", type=Path, required=True, help="data/clips/<clip>")
    parser.add_argument("--tracks", type=Path, required=True, help="file MOT cần xem")
    parser.add_argument("--compare", type=Path, default=None, help="file MOT thứ hai, vẽ nét đứt màu trắng")
    parser.add_argument("--out", type=Path, required=True, help="thư mục ghi ảnh")
    parser.add_argument("--only-frames", default=None, help="ví dụ: 1-30,100,150-160")
    parser.add_argument("--every", type=int, default=1, help="chỉ vẽ mỗi N frame")
    parser.add_argument("--video", type=Path, default=None, help="ghép thêm video (cần opencv)")
    parser.add_argument("--min-conf", type=float, default=0.0)
    args = parser.parse_args()

    images = sorted((args.clip / "img1").glob("*.jpg"))
    if not images:
        raise SystemExit(f"Không thấy ảnh trong {args.clip / 'img1'}")

    primary = by_frame(parse_mot(args.tracks, min_conf=args.min_conf))
    secondary = by_frame(parse_mot(args.compare)) if args.compare else {}
    wanted = parse_frame_filter(args.only_frames)

    args.out.mkdir(parents=True, exist_ok=True)
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 16)
    except OSError:
        font = ImageFont.load_default()

    written = []
    for index, image_path in enumerate(images, start=1):
        if wanted is not None and index not in wanted:
            continue
        if (index - 1) % args.every:
            continue
        image = Image.open(image_path).convert("RGB")
        draw = ImageDraw.Draw(image)

        for det in secondary.get(index, []):
            dashed_rectangle(draw, (det.x, det.y, det.x + det.w, det.y + det.h), (255, 255, 255))

        for det in primary.get(index, []):
            bbox_colour = colour(det.track_id)
            draw.rectangle((det.x, det.y, det.x + det.w, det.y + det.h), outline=bbox_colour, width=3)
            label = f"{det.track_id}"
            tx, ty = det.x, max(0.0, det.y - 19)
            draw.rectangle((tx, ty, tx + 12 + 9 * len(label), ty + 19), fill=bbox_colour)
            draw.text((tx + 5, ty + 2), label, fill=(0, 0, 0), font=font)

        banner = f"frame {index}/{len(images)}   {len(primary.get(index, []))} bbox"
        draw.rectangle((0, 0, 12 + 9 * len(banner), 22), fill=(0, 0, 0))
        draw.text((6, 3), banner, fill=(255, 255, 255), font=font)

        target = args.out / f"{index:06d}.jpg"
        image.save(target, "JPEG", quality=88)
        written.append(target)

    print(f"Đã ghi {len(written)} ảnh vào {args.out}")

    if args.video:
        try:
            import cv2
        except ImportError:
            print("Bỏ qua --video: chưa cài opencv-python")
            return 0
        first = cv2.imread(str(written[0]))
        height, width = first.shape[:2]
        writer = cv2.VideoWriter(str(args.video), cv2.VideoWriter_fourcc(*"mp4v"), 12.5, (width, height))
        for path in written:
            writer.write(cv2.imread(str(path)))
        writer.release()
        print(f"Đã ghi video {args.video}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
