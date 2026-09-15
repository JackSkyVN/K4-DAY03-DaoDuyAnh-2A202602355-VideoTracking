# CVAT readiness cho Day 3

## Kết quả cần có trước giờ lab

Day 3 tái sử dụng CVAT Community local từ Day 2 nhưng dùng schema tracking riêng:
đúng một label `vehicle`. Hoàn thành [hướng dẫn cài đặt Day 2](https://github.com/VinUni-AI20k/Day2-Object-Detection-Data-pilot/blob/main/CVAT_SETUP.md) trước lớp; installation không tính vào 240 phút. Có thể đối chiếu thêm [tài liệu CVAT Community chính thức](https://docs.cvat.ai/docs/administration/community/basics/installation/).

## Day 3 readiness delta

Trước lớp, xác nhận:

- CVAT mở được tại `http://localhost:8080` và đăng nhập được.
- Cùng CVAT version do lớp chỉ định; không tự nâng version giữa Day 2 và Day 3.
- Tạo được interpolation task từ một image sequence ngắn.
- Trong Rectangle dialog có lựa chọn **Track**.
- Workspace có thể hiển thị object ID; Save hoạt động.
- Export menu có **MOT 1.1**.
- Trình duyệt cho phép download ZIP và mở Google Colab.

Không dùng clip chính hoặc dữ liệu chưa được phê duyệt cho readiness test.

## Readiness gate trong lớp

Trong phút 0–15, chỉ làm:

1. mở CVAT và đăng nhập;
2. mở đúng task `clip_02` 60 frame;
3. xác nhận chỉ có label `vehicle`, Track Mode, Save và MOT 1.1 export menu;
4. báo mentor nếu khác template.

Không debug Docker sâu trong giờ. Nếu UI không sẵn sàng sau một lần restart đã được hướng dẫn, gửi OS, CVAT version, ảnh toàn màn hình lỗi và output health-check từ Day 2; che password/token/email.

## Dừng CVAT an toàn

Sau khi Save và export artifact cuối, dùng quy trình stop của Day 2. Không xóa Docker volumes hoặc gỡ CVAT trước khi kiểm ZIP nộp bài.
