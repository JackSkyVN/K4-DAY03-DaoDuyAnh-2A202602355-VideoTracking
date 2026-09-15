# Mini annotation guideline — Ngày 3 (tracking)

> Điền file này **trong lúc gán nhãn**, không phải sau khi xong. Mỗi lần bạn dừng
> lại nghĩ "cái này tính sao nhỉ?" thì đó là một dòng phải ghi vào đây.
>
> Đây là tài liệu mà người gán nhãn tiếp theo sẽ đọc để làm giống bạn. Nếu hai
> người trong nhóm gán khác nhau, gần như luôn là vì file này chưa nói rõ — chứ
> không phải vì ai kém.

Nhóm / tên: Đào Duy Anh — 2A202602355
Clip: `clip_01`, `clip_02`

---

## 1. Phạm vi: gán cái gì, không gán cái gì

Một lớp duy nhất: **`vehicle`** — xe bốn bánh (xe con, van, xe buýt, xe tải).

| Gán | Không gán |
| --- | --- |
| xe con, SUV, taxi, xe bán tải | người đi bộ |
| van, minivan | xe đạp |
| xe buýt, minibus | **xe máy / mô tô** |
| xe tải, xe đầu kéo | xe trong ảnh quảng cáo, trong gương, dưới bóng nước |

Bổ sung của nhóm: Không gán bóng xe, vệt phản chiếu dưới mặt đường, hoặc xe nhìn thấy qua kính xe khác.

## 2. Luật ID — phần quan trọng nhất

| Tình huống | Luật của nhóm | Vì sao |
| --- | --- | --- |
| Xe bị che một phần rồi hiện lại | giữ nguyên ID nếu bị che **dưới 10 frame** | 10 frame ≈ 0.8 giây — đủ ngắn để còn nhớ quỹ đạo và màu xe, tránh gán nhầm ID mới |
| Xe bị che lâu hơn ngưỡng trên | tạo **track mới** (reset ID) | Che quá lâu không thể xác định chắc chắn là cùng xe; tạo mới an toàn hơn |
| Xe rời khung hình rồi quay lại | giữ nguyên ID **nếu nhận ra chắc chắn** là cùng xe (màu, kích thước, vị trí tái xuất hiện gần biên cũ); nếu không chắc → track mới | Xe quay lại gần cùng vị trí biên trong vài frame có thể là cùng xe; không chắc thì tạo mới |
| Hai xe cắt nhau / chồng lên nhau | vẽ bbox ôm **phần nhìn thấy được** của từng xe, không đoán phần bị che; giữ cả hai track liên tục | Tránh overfit vào phần khuất; nhất quán với luật bbox chung |

## 3. Luật bbox

| Tình huống | Luật của nhóm |
| --- | --- |
| Xe bị cắt bởi rìa ảnh | bbox chạm đúng rìa, không đoán phần ngoài ảnh |
| Xe bị xe khác che một phần | bbox ôm phần **nhìn thấy được** |
| Xe vừa xuất hiện, còn rất nhỏ / rất mờ | bắt đầu track từ frame đầu tiên xe chiếm ít nhất **30% diện tích khung** và có thể xác định rõ ít nhất 2 đặc điểm (màu sơn + dạng thân/mui) là xe bốn bánh |
| Xe đang đỗ, không di chuyển | gán nhãn bình thường; chỉ cần **1 keyframe mỗi 10 frame** vì bbox không thay đổi |
| Keyframe đặt dày ở đâu | đặt dày (mỗi 3–5 frame) khi xe đang **xoay / thay đổi hướng** và khi xe **vào/ra khỏi rìa ảnh** |

## 4. Ít nhất ba ca mơ hồ đã gặp thật

Ghi **frame cụ thể** và **ID cụ thể**, không ghi chung chung.

### Ca 1
- Clip / frame / ID: `clip_01` / frame 51–53 / ID 4
- Tình huống: Xe ID 4 vừa xuất hiện ở rìa phải ảnh, chỉ nhìn thấy phần đầu xe rất nhỏ, chưa đủ để phân biệt rõ là xe con hay xe tải nhỏ.
- Quyết định: Ban đầu bắt đầu track từ frame 51. Sau khi chấm với gold phát hiện đây là ghost track (sớm hơn gold 3 frame). Đã sửa sau rework: dời frame bắt đầu về đúng frame xe nhìn rõ.
- Lý do: Áp dụng ngưỡng 30% diện tích + 2 đặc điểm nhận dạng — frame 51 xe chưa đủ điều kiện này.

### Ca 2
- Clip / frame / ID: `clip_01` / frame 59–78 / ID 5
- Tình huống: Xe ID 5 xuất hiện từ rìa trái ảnh, còn rất mờ và nhỏ ở khoảng cách xa. Khó xác định frame nào là frame đầu tiên xe "đủ rõ" để bắt đầu track.
- Quyết định: Ban đầu bắt đầu từ frame 59 — sau khi chấm phát hiện ghost (sớm hơn gold 20 frame). Đã sửa: dời frame bắt đầu về frame xe thực sự nhìn rõ là ô tô bốn bánh.
- Lý do: Cần ngưỡng rõ ràng cho xe xuất hiện từ xa — phải 30% diện tích **và** nhìn rõ ít nhất 2 đặc điểm (màu + dạng thân).

### Ca 3
- Clip / frame / ID: `clip_01` / frame 110–112 / ID 6
- Tình huống: Xe ID 6 đang di chuyển ngang và bị xe ID 5 (lớn hơn) chồng lên một phần. Bbox của xe 6 khó vẽ khít vì đường viền bị che khuất.
- Quyết định: Vẽ bbox ôm phần nhìn thấy của xe 6, chấp nhận bbox nhỏ hơn thực tế. IoU so với gold chỉ đạt 0.515–0.564 tại các frame này (loose box).
- Lý do: Ưu tiên không đoán phần bị che; nếu đoán sai sẽ tạo ra FP không cần thiết và lệch MOTP.

## 5. Sửa gì sau khi chấm với gold và sau khi kiểm chéo

Luật nào trong file này hoá ra còn thiếu hoặc còn mơ hồ? Viết lại cho rõ:

- **Ngưỡng bắt đầu track chưa đủ cụ thể:** Ban đầu chỉ ghi "xác định được là xe bốn bánh" mà không rõ khi xe còn nhỏ ở xa. Bổ sung: phải chiếm ít nhất 30% diện tích khung **và** nhìn rõ ít nhất 2 đặc điểm. Việc này giải quyết 4 ghost tracks bị phát hiện sau khi chấm với gold.
- **Ngưỡng giữ ID khi bị che cần ghi theo frame, không theo giây:** Thay "2 giây" bằng "10 frame" để nhất quán — không phụ thuộc fps của clip.
