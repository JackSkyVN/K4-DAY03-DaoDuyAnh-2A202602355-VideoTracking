# Dữ liệu Ngày 3

Hai clip cảnh giao thông đô thị, đã cắt sẵn và đánh số lại cho bài lab.

| Clip | Frame | Kích thước | FPS | Thời lượng | Track | Bbox | Ground truth |
| --- | ---: | --- | ---: | ---: | ---: | ---: | --- |
| `clip_01` | 190 | 960x540 | 12.5 | 15.2 s | 8 | 573 | giảng viên phát ở mốc 2:35 |
| `clip_02` | 60 | 960x540 | 12.5 | 4.8 s | 6 | 227 | có sẵn tại `clip_02/gt/gt.txt` |

`clip_01` là bài chính. `clip_02` là clip warm-up: nhãn đúng đã nằm sẵn trong repo
để bạn tự hiệu chỉnh tay nghề trước khi vào bài chính — hãy gán nó trước, chấm
ngay, rồi mới sang `clip_01`.

## Cấu trúc (chuẩn MOTChallenge)

```text
data/clips/clip_01/
  img1/000001.jpg ... 000190.jpg    # frame, đánh số liên tục từ 1
  seqinfo.ini                        # tên clip, fps, số frame, kích thước ảnh
data/clips/clip_02/
  img1/000001.jpg ... 000060.jpg
  seqinfo.ini
  gt/gt.txt                          # gold của clip warm-up
```

Đây đúng là bố cục mà CVAT, MOTChallenge và TrackEval đều hiểu, nên bạn upload
thẳng thư mục `img1/` lên CVAT được, không cần chuyển đổi gì.

## Định dạng nhãn: MOT 1.1

Mỗi dòng là **một bbox ở một frame**:

```text
frame, track_id, bb_left, bb_top, bb_width, bb_height, conf, class, visibility
1,1,210.13,250.78,91.79,38.69,1,1,1
2,1,210.13,250.81,91.81,38.74,1,1,1
```

- `frame` đánh số từ **1**, không phải 0.
- `track_id` là cột quan trọng nhất của hôm nay: hai dòng cùng `track_id` nghĩa là
  **cùng một chiếc xe**.
- Toạ độ là **pixel**, gốc ở góc trên trái, và là `left, top, width, height` —
  khác hẳn YOLO của Ngày 2 (`x_center y_center w h`, normalized).
- `conf`, `class`, `visibility` không được dùng khi chấm; để `1,1,1` là được.

`track_id` của bạn **không cần trùng** với `track_id` của gold. Chỉ số đánh giá
(HOTA, IDF1) tự ghép ID của bạn với ID của gold; cái được chấm là bạn có giữ
**cùng một ID cho cùng một chiếc xe** hay không.

## Lớp vật thể

Clip chỉ gán **xe bốn bánh**: xe con, van, xe buýt, xe tải. Bài này gộp tất cả
thành một lớp duy nhất `vehicle`, vì hôm nay câu hỏi là *ai là ai theo thời gian*,
không phải *cái này là loại xe gì* (đó là Ngày 2).

**Không gán**: người đi bộ, xe đạp, **xe máy / mô tô**. Trong clip có xe máy và
người đi bộ — đó không phải chỗ bạn bỏ sót, chúng nằm ngoài schema. Gán thêm
chúng vào sẽ bị tính là bbox thừa (FP) và kéo điểm xuống.

## Nguồn dữ liệu và giấy phép

Hai clip được cắt từ **UA-DETRAC** (Wen et al., *UA-DETRAC: A New Benchmark and
Protocol for Multi-Object Detection and Tracking*), qua bản phát hành lại
`abhineet123/ua_detrac` trên HuggingFace dưới giấy phép **CC-BY-4.0**. Đây là
cảnh CCTV giao thông tại Bắc Kinh/Thiên Tân, cùng họ dữ liệu với ảnh Ngày 2.

Frame đã được **đổi tên tuần tự, re-encode để xoá EXIF**, và `track_id` đã được
**đánh số lại từ 1** theo thứ tự xuất hiện. Repository không chứa tên sequence
gốc, chỉ số frame gốc hay `target_id` gốc, nên không tra ngược ra đáp án được.
Không dùng dữ liệu ngoài repo để đi tìm nhãn — xem phần cổng bắt buộc trong
[../RUBRIC.md](../RUBRIC.md).

Đã lọc bỏ toàn bộ *ignored region* của UA-DETRAC: hai clip này được chọn trong số
năm sequence không có vùng bỏ qua nào, nên luật gán nhãn gọn đúng một câu —
**mọi xe bốn bánh nhìn thấy được đều phải có bbox**.
