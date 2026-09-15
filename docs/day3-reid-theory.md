# ReID trong Lab Day 3: giữ đúng ID khi chuyển động không đủ thông tin

## Mục tiêu

Sau phần này, bạn phải giải thích được vì sao một tracker có thể tìm đúng xe ở
từng frame nhưng vẫn đổi ID, và kiểm tra bằng evidence liệu appearance/ReID có
giúp trên clip này hay không.

Đây là bài **so sánh có kiểm soát**, không phải bài train ReID và không phải bài
nhận diện biển số, tên người hay danh tính ngoài đời.

## Một tracking pipeline làm gì?

Mỗi frame, YOLO phát hiện các bbox. Tracker phải nối bbox mới với track cũ để
quyết định ID nào tiếp tục:

```text
YOLO bbox ở frame t
      │
      ├─ motion / Kalman: xe cũ dự đoán sẽ ở đâu?
      ├─ IoU: bbox mới có chồng với dự đoán không?
      └─ appearance / ReID: crop mới có giống track cũ không?
      │
track_id ở frame t
```

**Detection đúng không đồng nghĩa association đúng.** Hai xe có thể cắt nhau;
box của cả hai vẫn tốt, nhưng tracker có thể gắn chúng vào nhầm ID.

## ByteTrack là control

ByteTrack dùng Kalman + IoU. Nó ghép detection confidence cao trước, rồi thử
ghép các detection confidence thấp còn lại để cứu track khi vật thể che một
phần. Vì vậy nó xử lý được nhiều ca occlusion ngắn mà không cần appearance.

Nó không có ReID. Khi hai dự đoán có vị trí gần như nhau, ByteTrack không có
thông tin “xe này nhìn giống xe nào hơn”. Đây là control nhanh, đơn giản và là
điểm xuất phát của thí nghiệm.

## ReID thêm thông tin gì?

ReID biến crop của bbox thành một **embedding**: một vector số tóm tắt đặc điểm
thị giác. Với track cũ và detection mới, tracker đo độ giống trong embedding
space (thường là cosine similarity). Nếu vừa hợp lý về vị trí vừa đủ giống về
appearance, tracker có thêm bằng chứng để nối ID qua occlusion/crossing.

BoT-SORT-ReID trong lab vẫn dùng motion và IoU; nó **không thay thế** hai tín
hiệu đó. ReID chỉ là cue thứ ba.

| Cue | Câu hỏi nó trả lời tốt | Khi yếu |
| --- | --- | --- |
| Motion/Kalman | Xe này được dự đoán sẽ đi tới đâu? | Occlusion lâu, quay đầu, chuyển động bất ngờ. |
| IoU | Box mới có gần box dự đoán không? | Hai xe overlap/cắt nhau; detector jitter. |
| ReID/appearance | Crop mới có giống track cũ không? | Hai xe nhìn giống nhau, blur, góc nhìn/ánh sáng đổi. |

## Thí nghiệm trong notebook

Notebook giữ cố định YOLO weights, clip, frame order, `conf`, `iou`, `imgsz` và
COCO classes. Nó chạy:

1. `ByteTrack control` với `bytetrack.yaml`.
2. `BoT-SORT + ReID treatment` với `configs/trackers/botsort-reid.yaml`.

Treatment dùng `with_reid: true`, `model: auto`, `proximity_thresh` và
`appearance_thresh`. Camera của clip cố định nên `gmc_method: none`: không trộn
camera-motion compensation vào bài học ReID.

Đây là **system comparison**, không phải causal ablation chỉ của ReID:
ByteTrack và BoT-SORT là hai implementation association khác nhau, nên chênh
lệch metric không chứng minh appearance cue một mình gây ra thay đổi. Kết luận
đúng ở core là “BoT-SORT + ReID treatment tốt/xấu/không khác đáng kể hơn
ByteTrack trên clip này”. Muốn cô lập riêng ReID phải so BoT-SORT cùng config với
`with_reid: false` — đó là POC/extension cho coach, không phải yêu cầu 4 giờ.

Đọc kết quả theo thứ tự:

1. **IDF1, AssA, IDSW** — identity có ổn định hơn không?
2. **DetA, FP, FN** — detector/track output có thay đổi coverage không?
3. **Worst frames** — xem frame trước, trong và sau một occlusion/crossing.

Không có kết quả “đúng sẵn”. Treatment có thể tốt hơn, như nhau hoặc tệ hơn trên
một clip; kết luận chỉ hợp lệ khi kèm frame, ID và lý do.

## Các ngưỡng không phải nút tăng điểm

| Config | Ý nghĩa | Rủi ro khi chỉnh tùy tiện |
| --- | --- | --- |
| `proximity_thresh` | Mức gần nhau trong ảnh trước khi ReID được xét. | Thấp quá: xe xa nhưng giống màu có thể bị nối nhầm. |
| `appearance_thresh` | Mức giống visual tối thiểu để ReID match. | Cao quá: cùng xe bị tách track; thấp quá: xe giống nhau bị swap. |
| `track_buffer` | Số frame giữ track mất dấu. | Lâu quá có thể hồi sinh sai ID. |

Core lab không yêu cầu tune các ngưỡng theo gold. Stretch chỉ được thử sau core,
và phải ghi cấu hình lẫn trade-off.

## Những kết luận sai cần tránh

- “ReID biết xe nào ngoài đời.” Không; nó chỉ so appearance trong một tracking
  context, không xác minh danh tính.
- “ReID sửa detector.” Không; nếu YOLO không có bbox thì ReID không có crop để
  match.
- “IDF1 tăng là đủ.” Không; hãy kiểm FP/FN/IDSW và frame sequence.
- “Treatment thắng nghĩa là ReID một mình gây ra khác biệt.” Không; ByteTrack và
  BoT-SORT khác implementation. Cần ablation cùng BoT-SORT mới kết luận causal.

## Dành cho Lab Coach

Hỏi theo evidence:

1. Trước khi chạy model, học viên dự đoán đoạn nào motion/IoU dễ nhầm? Vì sao?
2. Nếu metric đổi, đoạn frame nào giải thích thay đổi đó?
3. ReID cue có hợp lý về spatial proximity và appearance không?
4. Có phải lỗi còn lại là detection (FN/FP) thay vì association không?

Không gọi output model là ground truth và không cho học viên sửa annotation từ
model output. Chỉ phát gold sau pre-gold lock như workflow của lab.

## Nguồn

- [ByteTrack: Multi-Object Tracking by Associating Every Detection Box](https://arxiv.org/abs/2110.06864)
- [BoT-SORT: Robust Associations Multi-Pedestrian Tracking](https://arxiv.org/abs/2206.14651)
- [Simple Online and Realtime Tracking with a Deep Association Metric (Deep SORT)](https://arxiv.org/abs/1703.07402)
- [Ultralytics: YOLO Multi-Object Tracking](https://docs.ultralytics.com/modes/track)
