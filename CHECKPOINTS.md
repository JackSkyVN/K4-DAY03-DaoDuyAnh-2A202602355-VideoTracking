# Checkpoints Day 3 — Video Tracking

Mỗi checkpoint đều có một artifact để chứng minh việc đã làm và một self-check
để phát hiện sai càng sớm càng tốt. Dùng checklist này cùng
[GUIDE.md](GUIDE.md) hoặc [lab-guide.html](lab-guide.html).

| Mốc | Việc phải làm | Artifact / bằng chứng | Bạn cần hiểu | Self-check |
| --- | --- | --- | --- | --- |
| 0–15 | Preflight và tạo task `clip_02` | task có đúng label `vehicle`, chọn Rectangle Track | Track khác Shape vì ID đi qua nhiều frame | mở object list: track có timeline, không phải box rời |
| 15–45 | Warm-up `clip_02`, export MOT 1.1 | `annotations/clip_02/gt.txt` | dòng MOT mang frame, ID và bbox | validator `clip_02` không báo lỗi |
| 45–135 | Gán độc lập `clip_01` | task đã Save, tối thiểu 6 track hợp lệ | xe bị che tạm thời vẫn giữ ID; xe rời khung dùng Outside | rà frame vào/ra, occlusion và crossing ở tốc độ chậm |
| 135–155 | Tự kiểm ba lượt và kiểm chéo | `reports/review_partner.md` | finding tốt phải chỉ ra frame, ID, lỗi và cách sửa | mọi finding có closure `fixed`, `needs-review` hoặc `not-a-defect` |
| 155–165 | Export cuối và khóa pre-gold | `evidence/pre-gold/clip_01/gt.txt`, `manifest.json` | hash chứng minh annotation có trước gold/model | chạy `lock_pre_gold.py` thành công; chưa mở gold/model |
| 165–195 | Nhận reference, evaluate và rework | `outputs/eval_vs_gold.json`, thay đổi ghi trong report | IDF1/AssA gợi ý lỗi identity; MOTA/MOTP gợi ý coverage/geometry | report có metric trước/sau và frame evidence của lần sửa |
| 195–225 | Chạy notebook control và treatment | hai MOT model, config và ba JSON evaluation | so sánh hệ thống, không coi model là đáp án | cả ByteTrack và BoT-SORT + ReID dùng cùng detector input |
| 225–240 | Hoàn tất report, commit và nộp VLearn | `reports/REPORT.md`, link repo cá nhân | evidence phải truy về được người nộp | làm [SUBMISSION.md](SUBMISSION.md) trước khi dán link |

Nếu một self-check chưa đạt, dừng ở checkpoint đó, sửa và kiểm lại; đừng đi tiếp
chỉ để kịp mốc thời gian.
