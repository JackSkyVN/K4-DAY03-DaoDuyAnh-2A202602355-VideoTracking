# Nộp bài Day 3 — Video Tracking

## Cách đặt tên và nơi nộp

Tạo một repo GitHub **cho riêng bạn** theo mẫu:

```text
K4-L2-L3-DAY03-HoVaTen-MSSV-VideoTracking
```

Dùng chữ không dấu, không khoảng trắng và dấu gạch nối giữa các phần. Day 3 là
một repo chung cho lộ trình Level 2→3, vì vậy mẫu tên này cố ý không tách thành
hai bài. Push repo rồi nộp **link repo cá nhân trên VLearn** trước 23:59,
`Asia/Ho_Chi_Minh`, ngày diễn ra lab. Nếu Key Coach công bố ngoại lệ, thông báo
đó là mốc thay thế.

Bạn có thể làm cá nhân hoặc làm cùng nhóm. Làm nhóm không thay thế bài nộp cá
nhân: mỗi thành viên nộp repo có tên/MSSV của chính mình. Khi làm nhóm, điền
[TEAM.md](TEAM.md) trong từng repo nộp.

## Artifact phải có

| Artifact | Evidence cần thấy |
| --- | --- |
| `annotations/clip_02/gt.txt` | warm-up export từ CVAT theo MOT 1.1 |
| `annotations/clip_01/gt.txt` | annotation cuối của clip chính, sau rework |
| `evidence/pre-gold/clip_01/gt.txt` và `manifest.json` | bản độc lập và hash SHA-256 trước gold/model |
| `GUIDELINE_MINI.md` | quy tắc ID/bbox và ít nhất ba ca mơ hồ thật |
| `reports/review_partner.md` | finding có frame, ID, lỗi, cách sửa và closure |
| `outputs/eval_vs_gold.json` | kết quả annotation cuối so với teaching reference |
| `outputs/model_bytetrack_clip_01.txt` | control YOLO26n + ByteTrack theo MOT |
| `outputs/model_reid_clip_01.txt` | treatment YOLO26n + BoT-SORT + ReID theo MOT |
| `outputs/model_run_config.json` | detector input, package/version và tracker config |
| `outputs/eval_bytetrack_vs_gold.json`, `outputs/eval_reid_vs_gold.json`, `outputs/eval_reid_vs_me.json` | evidence để so sánh model với reference và nhãn cuối của bạn |
| `reports/REPORT.md` | report hoàn chỉnh từ [mẫu](reports/REPORT_TEMPLATE.md) |
| `TEAM.md` | chỉ khi làm nhóm; khai báo thành viên và phần việc từng người |

Không commit `gold/`, model weights (`*.pt`), file ZIP, hoặc thư mục
`outputs/vis_*`. Không sửa trực tiếp file MOT để vượt validator: sửa trong CVAT
rồi export lại.

## Tự kiểm trước khi nộp

Chạy hai lệnh kiểm định dạng với hai clip; đường dẫn command là nguồn thực thi
cho tiêu chí định dạng:

```bash
python3 tools/check_mot_labels.py --clip data/clips/clip_02 --tracks annotations/clip_02/gt.txt
python3 tools/check_mot_labels.py --clip data/clips/clip_01 --tracks annotations/clip_01/gt.txt
```

Xác nhận snapshot độc lập đã tạo trước khi xem gold/model:

```bash
python3 tools/lock_pre_gold.py
```

Sau đó đối chiếu [CHECKPOINTS.md](CHECKPOINTS.md), xem
`git status --short`, commit các artifact cần nộp và mở repo bằng browser để
đảm bảo Lab Coach đọc được. Chi tiết điểm và các cổng bắt buộc ở
[RUBRIC.md](RUBRIC.md).
