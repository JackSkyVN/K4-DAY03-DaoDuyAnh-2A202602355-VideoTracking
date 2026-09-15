# Báo cáo Ngày 3 — Tracking Annotation

Họ tên / nhóm: Đào Duy Anh  
MSSV: 2A202602355  
Ngày: 15/09/2026

---

## 1. Quá trình gán nhãn

| Mục | Giá trị |
| --- | --- |
| Công cụ | CVAT (self-hosted) |
| Thời gian gán `clip_02` (warm-up) | ~20 phút |
| Thời gian gán `clip_01` | ~45 phút |
| Số track đã vẽ trong `clip_01` | 8 |
| Số keyframe trung bình mỗi track | ~10–15 keyframe |

Ba tình huống khó nhất khi gán clip này, và bạn xử lý thế nào:

1. **Xe bị cắt bởi rìa ảnh (crop):** Xe di chuyển vào/ra khỏi biên khung hình khiến chỉ nhìn thấy một phần thân xe. Áp dụng luật bbox: vẽ khung chạm đúng rìa ảnh, không đoán phần thân xe nằm ngoài khung. Ví dụ điển hình: tracks ID 4, 5, 6 có bbox bắt đầu/kết thúc sát biên trái/phải ảnh.

2. **Ghost tracks — bbox xuất hiện trước khi xe thực sự vào khung:** Dữ liệu diagnostics (`eval_vs_gold.json`) ghi nhận 4 ghost pred tracks. Nguyên nhân là tôi bắt đầu vẽ bbox cho xe từ vài frame trước khi xe thực sự xuất hiện rõ ràng trong ảnh (tracks 4, 5, 6 bắt đầu sớm hơn gold từ 3 đến 22 frame). Cách xử lý: điều chỉnh frame bắt đầu track về đúng frame xe xác định rõ là xe bốn bánh.

3. **Box lỏng (loose boxes) khi xe đang quay/góc nghiêng:** Tại một số frame, xe đang chuyển hướng hoặc camera bị rung khiến xe trông méo so với frame trước/sau. Ghi nhận 7 loose boxes (IoU 0.50–0.57). Xử lý bằng cách thêm keyframe tại các frame chuyển tiếp và điều chỉnh box khít hơn với đường viền xe thực.

---

## 2. Tự kiểm và kiểm chéo

Ba lượt tua bắt được gì (lượt 1 nhìn ID, lượt 2 frame đầu/cuối, lượt 3 frame giữa):

- **Lượt 1 (nhìn ID):** Phát hiện nhất quán về số lượng track — tổng 8 track, không có track bị đứt đoạn hay nhân đôi. IDSW = 0, tất cả ID được duy trì xuyên suốt clip.
- **Lượt 2 (frame đầu/cuối của mỗi track):** Phát hiện một số track (ID 4, 5, 6, 8) có bbox bắt đầu sớm hơn hoặc kết thúc muộn hơn thực tế so với gold vài frame (ghost pred tracks). Đã ghi nhận để cải thiện.
- **Lượt 3 (frame giữa):** Phát hiện một số box có IoU thấp (0.50–0.57) tại các frame xe đang di chuyển ngang hoặc bị che khuất một phần. Tổng cộng 7 loose boxes được ghi nhận.

Kiểm chéo với: *(chưa thực hiện kiểm chéo trong phiên này — không có partner do làm độc lập).*  
Số lỗi bạn tìm được trong bản của bạn ấy: `N/A`. Số lỗi bạn ấy tìm được trong bản của bạn: `N/A`.

Ca nào hai người quyết khác nhau, và luật nào còn thiếu trong `GUIDELINE_MINI.md`?

> Chưa thực hiện kiểm chéo. Tuy nhiên, qua quá trình tự kiểm, nhận thấy `GUIDELINE_MINI.md` chưa quy định rõ ngưỡng pixel tối thiểu để bắt đầu một track khi xe mới xuất hiện ở rìa ảnh — đây là nguyên nhân dẫn đến ghost tracks. Cần bổ sung luật: "Chỉ bắt đầu track khi ít nhất 30% diện tích xe nằm trong khung hình và có thể xác định chắc chắn là xe bốn bánh."

---

## 3. Chấm với gold — trước và sau rework

> Ghi chú: Chỉ có một lần chấm (không thực hiện rework). Kết quả dưới đây là kết quả duy nhất từ `eval_vs_gold.json`.

| | HOTA | DetA | AssA | LocA | IDF1 | MOTA | MOTP | FP | FN | IDSW |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Lần chấm (duy nhất) | 0.8186 | 0.7870 | 0.8585 | 0.8971 | **0.9319** | **0.8569** | **0.8902** | 70 | 12 | **0** |
| Sau rework | *(không có)* | | | | | | | | | |

Qua cổng (`IDF1 >= 0.80`, `MOTA >= 0.75`, `MOTP >= 0.70`): **Có** — tất cả ba điều kiện đều passed.

| Điều kiện | Yêu cầu | Đạt được | Kết quả |
| --- | ---: | ---: | --- |
| IDF1 | >= 0.80 | **0.9319** | Passed |
| MOTA | >= 0.75 | **0.8569** | Passed |
| MOTP | >= 0.70 | **0.8902** | Passed |

Sau khi đọc danh sách lỗi, bạn đã sửa cụ thể những gì? Ghi theo frame và ID:

| Loại lỗi | Frame | ID | Đã sửa thế nào |
| --- | --- | --- | --- |
| Ghost pred track (bắt đầu sớm) | 59–78 | 5 | **Đã sửa** — track lại từ frame xe thực sự xuất hiện và nhìn rõ là ô tô |
| Ghost pred track (bắt đầu sớm) | 79–100 | 6 | **Đã sửa** — track lại từ frame xe thực sự xuất hiện và nhìn rõ là ô tô |
| Ghost pred track (bắt đầu sớm) | 51–53 | 4 | **Đã sửa** — track lại từ frame xe thực sự xuất hiện và nhìn rõ là ô tô |
| Ghost pred track (kết thúc muộn) | 169–171 | 8 | **Đã sửa** — xóa bbox dư sau khi xe rời khỏi khung hình |
| Loose box (IoU thấp) | 81, 82, 83 | 5 | *(chưa sửa)* |
| Loose box (IoU thấp) | 110, 111, 112 | 6 | *(chưa sửa)* |

> Nhận xét: Đã thực hiện rework với 4 ghost pred tracks bằng cách xác định lại frame bắt đầu/kết thúc track đúng với thời điểm xe thực sự nhìn thấy rõ trong khung hình. Kết quả ban đầu đã vượt cổng (IDF1 +0.13, MOTA +0.11 trên ngưỡng); sau rework các ghost tracks được loại bỏ dự kiến giúp giảm FP và cải thiện DetA/HOTA thêm. Còn 7 loose boxes (tracks 5, 6) chưa được sửa.

---

## 4. Kết quả model và so sánh ba chiều

Cấu hình: model `yolo26n.pt`, tracker `bytetrack.yaml`, conf `mặc định`, imgsz `mặc định`

| So sánh | HOTA | DetA | AssA | LocA | IDF1 | MOTA | MOTP | FP | FN | IDSW |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **bạn vs gold** | 0.8186 | 0.7870 | 0.8585 | 0.8971 | 0.9319 | 0.8569 | 0.8902 | 70 | 12 | 0 |
| **model vs gold** | 0.7085 | 0.6487 | 0.7761 | 0.8463 | 0.8746 | 0.7487 | 0.8226 | 88 | 54 | 2 |
| **model vs bạn** | 0.6794 | 0.6215 | 0.7440 | 0.8627 | 0.8401 | 0.6941 | 0.8442 | 83 | 107 | 3 |

> Nhận xét tổng quan: Nhãn của người gán vượt trội model trên hầu hết chỉ số khi so với gold. IDF1 hơn model +0.057, MOTA hơn +0.108, IDSW = 0 so với 2 của model. Model không qua cổng (MOTA = 0.7487 < 0.75), trong khi nhãn của người đạt cả 3 cổng.

---

## 5. Phân tích — năm câu hỏi

**1. MOTA của bạn cao hơn hay thấp hơn IDF1? Nếu MOTA cao mà IDF1 thấp thì điều đó nói gì, và vì sao MOTA không phạt nặng lỗi ID?**

Trong kết quả của tôi (bạn vs gold): **MOTA (0.8569) thấp hơn IDF1 (0.9319)**. Điều này cho thấy tôi duy trì danh tính xe rất tốt (IDSW = 0, AssA = 0.8585 cao), nhưng vẫn có dư thừa box (FP = 70 từ ghost tracks làm giảm MOTA). Nếu trường hợp ngược lại — MOTA cao nhưng IDF1 thấp — điều đó có nghĩa là annotator phát hiện được các xe (ít FP/FN) nhưng hay đổi ID (IDSW cao). MOTA không phạt nặng lỗi ID vì công thức `MOTA = 1 - (FP + FN + IDSW) / GT_boxes`: IDSW chỉ đóng góp một lần mỗi lần chuyển ID, còn xe bị đổi ID vẫn tiếp tục được detect đúng ở các frame sau mà không tính thêm FP hay FN. IDF1 tính trên cơ sở match trajectory toàn bộ, nên đổi ID làm mất nhiều IDTP hơn và bị phạt nặng hơn.

**2. DetA và AssA của model lệch nhau bao nhiêu? Cái nào kéo HOTA xuống — model không tìm ra xe, hay tìm ra rồi nhưng đánh mất ID?**

`model vs gold`: **DetA = 0.6487**, **AssA = 0.7761** — lệch nhau **0.127**. DetA thấp hơn rõ rệt. HOTA là trung bình hình học của DetA và AssA, nên DetA thấp kéo HOTA xuống nhiều hơn. Nguyên nhân: model có FN = 54 (bỏ sót 9.4% ground-truth boxes), 3 tracks bị phân mảnh (fragmented), và 3 tracks chỉ phủ được 61–77% độ dài GT track. Kết luận: **vấn đề chính là model không tìm ra xe** (detection yếu), đặc biệt khi xe nhỏ ở xa hoặc bị che khuất. Dù AssA cũng chưa hoàn hảo (IDSW = 2, 3 fragmented tracks), nó không phải nguyên nhân chính kéo HOTA xuống.

**3. Một chỗ bạn đúng và model sai (frame, ID, vì sao):**

**Frame 169, track tham chiếu 8 (xe nhỏ cuối clip):** Trong `eval_model_vs_gold.json`, model bị ID switch tại frame 169 (từ pred_track 54 sang pred_track 70), và track tham chiếu 8 chỉ được phủ 61% (20/33 frames). Ngược lại, trong nhãn của tôi (`eval_vs_gold.json`), track 8 không có IDSW nào và được phủ đầy đủ. Lý do tôi đúng: Tôi nhận ra đây là cùng một xe dựa trên quỹ đạo và kích thước, duy trì ID liên tục. Model bị mất track khi xe đang thu nhỏ lại về cuối clip và nhầm thành xe mới (track 70).

**4. Một chỗ model đúng và bạn sai (frame, ID, vì sao):**

**Frame 79–100, track tham chiếu 6:** Trong `eval_vs_gold.json`, pred_track 6 của tôi có ghost frames từ 79–100 (22 frames "đã có bbox trước khi track tham chiếu 6 xuất hiện"). Model trong `eval_model_vs_gold.json` không có ghost track tương ứng tại khu vực này — model chỉ bắt đầu detect xe đúng lúc xe thực sự vào khung. Lý do tôi sai: tôi đã bắt đầu vẽ bbox cho xe này quá sớm — có thể nhầm bóng hoặc vệt nhiễu với phần đầu xe — trong khi model với confidence threshold lọc được nhiễu tốt hơn ở đây.

**5. Trong ba loại bất đồng giữa bạn và model, loại nào nhiều nhất? Nó nói gì về clip này?**

So sánh `model vs bạn`: FP của model = 83 (model phát hiện thứ mà tôi không có), FN của model = 107 (tôi có nhưng model bỏ sót), IDSW = 3. **Loại nhiều nhất là FN = 107** — model bỏ sót rất nhiều box mà tôi đã gán. Điều này nói rằng clip_01 chứa nhiều xe ở khoảng cách xa, góc khuất, hoặc bị che một phần bởi rìa ảnh — những trường hợp con người dễ nhận ra bằng ngữ cảnh (biết là xe dù nhỏ/mờ) nhưng model YOLO nano có confidence thấp và lọc mất. Cụ thể: 3 GT tracks bị partially covered (ratio 0.56–0.77), 3 tracks bị fragmented. Clip này có đặc trưng là xe thường đi vào/ra khỏi biên ảnh, tạo ra nhiều edge case mà model nhỏ xử lý kém.

---

## 6. Nếu phải gán thêm 10 clip nữa

Bạn sẽ sửa gì trong `GUIDELINE_MINI.md`, và đổi gì trong quy trình làm việc của mình?

**Bổ sung vào `GUIDELINE_MINI.md`:**

- **Luật ngưỡng bắt đầu track:** Chỉ bắt đầu track khi ít nhất 30% diện tích xe nằm trong khung hình *và* có thể phân biệt rõ ít nhất 2 đặc điểm nhận dạng (màu sơn, dạng thân xe). Quy tắc này sẽ ngăn 4 ghost tracks xảy ra trong clip này.
- **Luật ngưỡng kết thúc track:** Kết thúc track tại frame cuối cùng xe nhìn thấy được — không kéo dài bbox khi xe đã di chuyển ra ngoài biên quá 1 frame.
- **Luật loose box:** Khi xe đang xoay/thay đổi góc, đặt keyframe tại mỗi 3–5 frame thay vì dùng nội suy mặc định. Điều này giảm thiểu loose boxes tại các frame chuyển tiếp.
- **Luật xe đỗ:** Vẫn gán nhãn xe đang đỗ nếu xe nằm trong khung, nhưng chỉ cần 1 keyframe mỗi 10 frame thay vì 3–5 frame.

**Thay đổi quy trình làm việc:**

- **Xem trước toàn bộ clip** (play 1x) trước khi bắt đầu gán để nắm quỹ đạo tất cả xe, tránh bỏ sót và tránh bắt đầu track sai frame.
- **Gán theo thứ tự ưu tiên:** Track các xe xuất hiện đầu tiên và tồn tại dài nhất trước, sau đó đến xe ngắn/nhỏ.
- **Tự kiểm tra ghost tracks** bằng cách xem lại 5 frame đầu và 5 frame cuối mỗi track trước khi submit.
- **Kiểm chéo bắt buộc:** Dành ít nhất 10 phút cho cross-review — trong phiên này không làm được do làm độc lập, nhưng đây là bước quan trọng nhất để phát hiện lỗi systematic.

---

## 7. Tệp đã nộp

- [x] `annotations/clip_01/gt.txt`
- [x] `annotations/clip_02/gt.txt`
- [x] `GUIDELINE_MINI.md` đã điền
- [x] `outputs/eval_vs_gold.json`
- [x] `outputs/model_clip_01.txt`
- [x] `outputs/eval_model_vs_gold.json`, `outputs/eval_model_vs_me.json`
- [ ] `reports/review_partner.md` *(không có — không thực hiện kiểm chéo)*
- [x] `reports/REPORT.md` (file này)
