# CVAT task specification — Day 3 V2

Tạo hai interpolation task từ đúng image sequence trong starter. Không chạy
automatic annotation/tracking trước vòng annotation độc lập.

## Media contract

| Task | Input | Frame | FPS | Kích thước | Vai trò |
| --- | --- | ---: | ---: | --- | --- |
| `D03-V2-CLIP02-WARMUP` | `data/clips/clip_02/img1/*.jpg` | 60 | 12.5 | 960×540 | guided warm-up |
| `D03-V2-CLIP01-CORE` | `data/clips/clip_01/img1/*.jpg` | 190 | 12.5 | 960×540 | independent core |

Upload theo thứ tự tên file `000001.jpg…`; không đổi tên hoặc bỏ frame. Dùng một
job liên tục cho mỗi task để track ID có nghĩa trên toàn sequence.

## Label schema

Tạo đúng một Rectangle label:

```text
vehicle
```

Bao gồm xe bốn bánh: car, SUV, van, bus, truck. Không gán pedestrian, bicycle,
motorcycle, sign hoặc ảnh xe trên quảng cáo. Không sao chép 4-class taxonomy hay
attributes của Day 2 vào task này.

## Annotation mode và geometry

- Chọn Rectangle → `vehicle` → **Track**, không chọn Shape.
- Bbox ôm sát phần nhìn thấy được.
- Bbox chạm rìa ảnh nếu xe bị cắt khung; không đoán phần ngoài ảnh.
- Partial occlusion: giữ cùng ID, bbox phần nhìn thấy, bật Occluded nếu phù hợp.
- Full absence: không vẽ box vô hình; dùng Outside tại frame đầu object vắng mặt.
- Entry/exit và crossing phải được kiểm frame-by-frame quanh transition.

## Frame indexing

- Tùy CVAT version, UI có thể hiển thị frame đầu là 0.
- MOT 1.1 trong lab dùng frame đầu là 1.
- Peer finding ghi cả CVAT frame và MOT frame khi chúng lệch nhau.
- Không sửa số frame hoặc `track_id` bằng tay sau export.

## Task creation smoke

1. Kiểm đúng frame count và resolution.
2. Kiểm chỉ có một label `vehicle`.
3. Vẽ một Rectangle Track thử, thêm keyframe, bật Outside, Save.
4. Reload và kiểm track vẫn tồn tại.
5. Export MOT 1.1 từ Task → Requests → Download.
6. Xác nhận archive có `gt/gt.txt`, cột hai có nhiều track ID.
7. Xóa annotation thử trước khi giao task sạch cho học viên.

UI wording có thể đổi theo CVAT version. Nếu khác ảnh hướng dẫn, Lab Coach cập
nhật ảnh chụp từ thao tác thật và smoke-test lại trước cohort.
