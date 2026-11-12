# SpamCleaner — Module Lọc Dòng Rác & Watermark Chương Truyện

Module độc lập dùng để ghép vào quy trình crawl/xử lý truyện (giữa bước lấy `raw_text` và bước dịch/TTS/render video).

---

## 1. Cấu trúc thư mục

```
spam_cleaner/
├── __init__.py           # Export SpamCleaner class
├── cleaner.py            # Logic phân loại & làm sạch 1 chương truyện
├── features.py           # Chuẩn hóa Unicode script & trích xuất đặc trưng
├── spam_model.joblib     # File model đã được huấn luyện sẵn (v3 dual-classifier)
├── batch_processor.py    # Script mẫu chạy làm sạch hàng loạt trực tiếp từ DB
├── requirements.txt      # Các thư viện phụ thuộc (joblib, scikit-learn, numpy, scipy)
└── README.md             # Tài liệu này
```

---

## 2. Cách hoạt động của Model

Module sử dụng kiến trúc **Song song 2 Bộ phân loại (Dual-Classifier)** chạy gộp dạng batch:

1. **Model A (Full-line Classifier):**
   * Quét toàn bộ các dòng trong chương.
   * Kết hợp TF-IDF char n-grams + Phân bố nhóm chữ Unicode (Unicode Script Features: CJK, Latin, Cyrillic, Greek, Math fonts, Emoji) + Vị trí tương đối (`pos_ratio`) trong chương.
   * Xóa trọn vẹn các dòng quảng cáo, tên miền, nút điều hướng (`添加書籤`, `返回目錄`, `章節報錯`, `天天看小說`, `shuhaige.net`, `8book`, ...).

2. **Model B (Tail-window Classifier, cửa sổ 65 ký tự):**
   * Tự động phát hiện các đuôi watermark dính liền vào câu thoại truyện (ví dụ: `69shux.com`, emoji trang trí, link web, số nhóm QQ) **mà không phụ thuộc vào regex tên miền cố định**.
   * Cắt chính xác tại dấu kết câu tiếng Trung chuẩn (`。`, `！`, `？`, `」`, `”`), bảo toàn 100% nội dung truyện phía trước.

---

## 3. Hướng dẫn ghép vào Code / Hệ thống

### Cài đặt thư viện:
```bash
pip install -r requirements.txt
```

### Sử dụng trực tiếp trong code Python:
```python
from spam_cleaner import SpamCleaner

# Khởi tạo cleaner (chỉ cần load 1 lần cho worker / server)
cleaner = SpamCleaner(full_threshold=0.80, tail_threshold=0.80)

# 1. Cách 1: Chỉ lấy chuỗi văn bản sạch
cleaned_text = cleaner.clean_text(raw_text)

# 2. Cách 2: Lấy chi tiết các dòng đã lọc để ghi log / debug
result = cleaner.clean(raw_text)
print("Văn bản sạch:\n", result["cleaned_text"])
print("Các dòng rác đã xóa:", result["removed_lines"])
print("Các đuôi watermark đã cắt:", result["stripped_tails"])
```

---

## 4. Chạy làm sạch hàng loạt trong Database (Batch Processor)

Module đi kèm file `batch_processor.py` để quét và cập nhật trực tiếp vào PostgreSQL:

```bash
# Xử lý thử nghiệm 1.000 chương chưa được làm sạch
python spam_cleaner/batch_processor.py --limit 1000

# Chạy làm sạch toàn bộ DB (batch size 500 chương/lần)
python spam_cleaner/batch_processor.py --batch-size 500

# Chạy quét đè lại cả các chương đã có cleaned_text
python spam_cleaner/batch_processor.py --overwrite
```

### Thông số cấu hình CLI:
* `--db-url`: Connection string PostgreSQL (mặc định lấy từ biến môi trường `DATABASE_URL`).
* `--batch-size`: Số chương cập nhật trong mỗi transaction DB (mặc định: `500`).
* `--threshold`: Ngưỡng độ tin cậy để xóa/cắt rác (mặc định: `0.80` — mức an toàn không xóa nhầm nội dung truyện).
* `--limit`: Giới hạn số chương cần xử lý (`0` là xử lý hết).
* `--overwrite`: Cho phép xử lý lại các chương đã có dữ liệu `cleaned_text`.

---

## 5. Tốc độ & Tài nguyên
* **Tốc độ xử lý:** ~15 – 20 ms / chương (~50 – 70 chương/giây trên 1 core CPU thường).
* **Bộ nhớ RAM:** Model rất nhẹ (~12 MB RAM khi nạp vào bộ nhớ).
* **Xử lý toàn bộ ~142.000 chương:** Ước tính mất khoảng **35 – 45 phút** trên CPU máy cá nhân.
