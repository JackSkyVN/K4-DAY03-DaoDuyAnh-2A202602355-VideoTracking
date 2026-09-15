# Quy tắc làm bài Day 3 — Video Tracking

## Phạm vi và thứ tự bắt buộc

- Bạn được làm cá nhân hoặc phối hợp nhóm, với cùng rubric và deliverables.
- Mỗi người phải tự tạo annotation `clip_01`, snapshot pre-gold và repo nộp cá
  nhân. Không dùng annotation/evidence của người khác làm bài của mình.
- Gán nhãn độc lập → tự kiểm/peer review → khóa pre-gold → mới nhận teaching
  reference và chạy model. Không đảo thứ tự này.
- Sửa bbox/track trong CVAT rồi export lại; không chỉnh trực tiếp file MOT để
  làm đẹp kết quả validator hoặc metric.

## Hợp tác, AI và nguồn tham khảo

- Được trao đổi cách dùng CVAT, thảo luận guideline, hỗ trợ debug và review
  chéo. Khi làm nhóm, dùng [TEAM.md](TEAM.md) để minh bạch ai làm gì.
- Không sao chép track, report, metric interpretation hay reflection của người
  khác. Peer reviewer nêu finding; người sở hữu repo tự quyết và ghi lần sửa.
- Có thể dùng AI để giải thích khái niệm, đọc lỗi command/notebook hoặc cải
  thiện cách diễn đạt report. AI không được thay bạn quyết định ID/bbox, tạo
  evidence review giả, thay nội dung reflection, hay đưa gold/model vào trước
  pre-gold lock.
- Chỉ dùng dữ liệu, schema và reference được phát trong lab. Không truy ngược
  nguồn dataset để tìm đáp án nhãn.

## Deadline và thay đổi sau hạn

- Hạn mặc định là 23:59 `Asia/Ho_Chi_Minh` trong ngày lab, nộp link repo cá
  nhân trên VLearn.
- Chỉ Key Coach mới công bố ngoại lệ deadline. Sau hạn, không force-push hay
  sửa artifact nộp trừ khi Lab Coach/Key Coach yêu cầu xử lý kỹ thuật; mọi thay
  đổi được ghi rõ bằng commit mới.

## Dữ liệu, quyền riêng tư và bí mật

- Không đưa token, API key, mật khẩu, file `.env`, thông tin cá nhân không cần
  thiết hoặc dữ liệu ngoài phạm vi lab vào repo/report/screenshot.
- Không commit hoặc chia sẻ `gold/clip_01/gt.txt`, dữ liệu instructor, model
  weights hay artifact nội bộ của Lab Coach.
- Khi cần hỏi hỗ trợ, gửi lỗi và đường dẫn artifact tối thiểu cần thiết; che
  thông tin nhạy cảm trước khi gửi ảnh màn hình.
