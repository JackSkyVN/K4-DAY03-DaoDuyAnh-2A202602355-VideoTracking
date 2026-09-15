# Nhãn của bạn đặt ở đây

Sau khi export từ CVAT ở định dạng **MOT 1.1**, giải nén và đặt file `gt.txt` vào:

```text
annotations/clip_01/gt.txt     <- bài chính (190 frame)
annotations/clip_02/gt.txt     <- clip warm-up (60 frame)
```

Trong file zip CVAT tải về, `gt.txt` nằm ở `gt/gt.txt`. Chỉ cần lấy đúng file đó.

Kiểm tra ngay sau khi đặt:

```bash
python3 ../tools/check_mot_labels.py --clip ../data/clips/clip_01 --tracks clip_01/gt.txt
```

Hai file này là bài nộp — nhớ `git add` chúng.
