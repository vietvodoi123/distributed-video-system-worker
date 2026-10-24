# 🚀 HƯỚNG DẪN CẬP NHẬT VÀ ĐỒNG BỘ WORKER VỚI SERVER MASTER

> **Mục đích:** Tài liệu này cung cấp đầy đủ thông tin kỹ thuật, danh sách file cần sửa đổi và mã nguồn chuẩn để Worker (`distributed-video-system-worker`) hoạt động hoàn hảo với Server Master hiện tại.
> **Ngày cập nhật:** 24/10/2026.

---

## 📌 1. TỔNG QUAN CÁC THAY ĐỔI TRÊN SERVER MASTER

Server Master đã có những nâng cấp kiến trúc quan trọng:
1. **Gộp `preprocess_text` vào `crawl_chapter`:**
   - Server đã **xóa bỏ task `preprocess_text`** khỏi đồ thị DAG.
   - Task `crawl_chapter` giờ đây đảm nhiệm toàn bộ: Cào text -> Làm sạch (clean) -> Xác thực (validate tiếng Trung) -> Lưu cả `raw_text` và `cleaned_text` vào DB trong 1 request.
   - Nếu trang bị chặn/quá ít tiếng Trung, `crawl_chapter` sẽ nổ lỗi `FAILED` ngay tại chỗ để tự động retry (`RetryPolicy.SELF`).
2. **Server tự sinh Thumbnail và Metadata:**
   - Đã **xóa bỏ task `generate_batch_thumbnail`** khỏi đồ thị `BATCH_GRAPH`. Server tự động render batch thumbnail bằng canvas/PIL trước khi upload YouTube.
   - Đã **xóa bỏ task `generate_youtube_description`** khỏi `BATCH_GRAPH`.
3. **Đồ thị DAG Chapter chuẩn hiện tại:**
   $$\text{crawl\_chapter} \longrightarrow \text{translate\_text} \longrightarrow \text{audio} \longrightarrow \text{video}$$
4. **Đồ thị DAG Batch chuẩn hiện tại:**
   $$\text{video (mọi chapter)} \longrightarrow \text{merge\_batch\_video}$$
5. **Khai tử MinIO (Port 9000):**
   - Không còn dùng MinIO.
   - Dùng `STORAGE_BACKEND: local` (nếu Worker cùng máy với Server) hoặc `STORAGE_BACKEND: http` (nếu Worker kết nối qua LAN/Wi-Fi tới Port 8000).

---

## 🛠️ 2. CHI TIẾT CÁC FILE CẦN THAY ĐỔI PHÍA WORKER

### 📁 File 1: `shared/contracts/capabilities/capabilities.py`
**Vấn đề:** Hiện tại file này đang thiếu hằng số `AUDIO_C` và còn chứa các task cũ đã bỏ.

👉 **Nội dung chuẩn thay thế:**
```python
CRAWL_CHAPTER_C = "crawl_chapter"
TRANSLATE_MOXHI = "translate_moxhi"
AUDIO_C = "audio"
VIDEO_C = "video"
MERGE_BATCH_VIDEO_C = "merge_batch_video"
MERGE_TTS_SEGMENTS_C = "merge_tts_segments"

# Legacy / Deprecated (Giữ lại để tương thích ngược nếu cần)
PREPROCESS_TEXT_C = "preprocess_text"
GENERATE_YOUTUBE_DESCRIPTION_C = "generate_youtube_description"
GENERATE_BATCH_THUMBNAIL_C = "generate_thumbnail"
```

---

### 📁 File 2: `shared/runtime/executors/registry/register_executors.py`
**Vấn đề:** Không cần đăng ký `PreprocessTextExecutor` và `GenerateBatchThumbnailExecutor` nữa vì Server không bao giờ tạo 2 task này.

👉 **Mã nguồn chuẩn của `register_executors`:**
```python
from shared.runtime.executors.registry.task_executor_registry import TaskExecutorRegistry
from shared.runtime.executors.crawl.crawl_chapter_executor import CrawlChapterExecutor
from shared.runtime.executors.translation.translate_text_excutor import TranslateTextExecutor
from shared.runtime.executors.audio.audio_executor import AudioExecutor
from shared.runtime.executors.audio.service.tts_service import TTSService
from shared.runtime.executors.video.generate_video_executor import GenerateVideoExecutor
from shared.runtime.executors.video.merge_batch_videos_executor import MergeBatchVideosExecutor
from shared.contracts.enums.task_types import *
from shared.config.settings import settings

def register_executors(gpu_available, model_path, config_path):
    max_concurrency = getattr(settings.tts, "max_concurrency", 3)
    tts_service = TTSService(
        model_path=model_path,
        config_path=config_path,
        use_cuda=gpu_available,
        max_concurrency=max_concurrency,
    )

    # Đăng ký 5 Executor cốt lõi khớp với Server
    TaskExecutorRegistry.register(CRAWL_CHAPTER, CrawlChapterExecutor())
    TaskExecutorRegistry.register(TRANSLATE_TEXT, TranslateTextExecutor())
    TaskExecutorRegistry.register(AUDIO, AudioExecutor(tts_service=tts_service))
    TaskExecutorRegistry.register(VIDEO, GenerateVideoExecutor())
    TaskExecutorRegistry.register(MERGE_BATCH_VIDEO, MergeBatchVideosExecutor())
```

---

### 📁 File 3: `shared/runtime/executors/crawl/crawl_chapter_executor.py`
*(Đã được cập nhật commit `b9db82d`)*:
Đảm bảo phần sau khi tải nội dung được viết như sau:
```python
        # =========================
        # CLEAN & VALIDATE TEXT
        # =========================
        raw_text = f"{title}\n\n{content}".strip()
        if not raw_text:
            raise ValueError("Chapter empty")

        # 1. Validate raw text (encoding / binary / replacement chars)
        validate_raw_text(raw_text)

        # 2. Làm sạch tiếng Trung
        cleaned_content = clean_cn_content(content)
        cleaned_text = f"{title}\n\n{cleaned_content}".strip()

        # 3. Validate tiếng Trung (số lượng ký tự Hán >= 100 và tỷ lệ >= 10%)
        # Nếu bị dính trang chặn Cloudflare / 403 / rác -> Sẽ raise lỗi FAILED ngay để Server retry!
        validate_cleaned_chapter(cleaned_text)

        # =========================
        # SAVE TO CONTROL PLANE
        # =========================
        api = runtime_context.api_client
        await api.update_chapter_text(
            chapter_id=runtime_context.chapter_id,
            data={
                "raw_text": raw_text,
                "cleaned_text": cleaned_text,
                "original_title": title,
            }
        )
```

---

### 📁 File 4: `shared/config/settings.yaml`
**Cấu hình tối ưu chuẩn cho máy Worker:**

```yaml
# ==========================================
# WORKER CAPABILITIES (Khớp 100% với Server DAG)
# ==========================================
capabilities:
  - crawl_chapter      # Cào văn bản, validate & làm sạch
  - translate_moxhi    # Dịch thuật tiếng Trung -> tiếng Việt
  - audio              # Sinh giọng đọc thuyết minh TTS
  - video              # Render video từng chương (MC Loop, Text Scroll)
  - merge_batch_video  # Nối các chương thành video hoàn chỉnh

# ==========================================
# CONCURRENCY CONTROL (Tùy chỉnh theo phần cứng)
# ==========================================
worker:
  poll_interval: 5           # Chu kỳ thăm dò việc (giây)
  task_lease_seconds: 30     # Thời gian gia hạn lease
  max_slots: 3               # Tổng số task Worker nhận đồng thời
  max_audio_slots: 2         # Giới hạn số luồng TTS song song
  max_video_slots: 1         # Giới hạn số luồng render video NVENC (1 task để tránh nghẽn GPU)

# ==========================================
# SERVER CONNECTIONS
# ==========================================
api:
  base_url: http://192.168.1.147:8000
  translate_moxhi: http://192.168.1.147:8090   # Địa chỉ dịch thuật Moxhi

# Lưu trữ:
# - Dùng "http" nếu Worker là máy phụ trong mạng LAN (tải/stream qua port 8000)
# - Dùng "local" nếu Worker chạy ngay trên máy chủ Master
STORAGE_BACKEND: http
STORAGE_ROOT_DIR: storage

# ==========================================
# AI & TRANSLATION ENGINE
# ==========================================
translation:
  chunk_max_chars: 6000

tts:
  tts_model: shared/data/model/ngochuyennew.onnx
  max_concurrency: 2
  default_speed: 1.0

# ==========================================
# VIDEO RENDERING
# ==========================================
video_render:
  num_workers: 2
  frame_jpeg_quality: 70
  acceleration: auto
  nvenc_preset: p1
  target_bitrate: 2M
  max_bitrate: 3M
  bufsize: 6M
```

---

## 🏃 3. HƯỚNG DẪN KHỞI CHẠY WORKER

1. **Kích hoạt Virtual Environment:**
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```
2. **Kiểm tra kết nối tới Server Master:**
   ```powershell
   curl http://192.168.1.147:8000/docs
   ```
3. **Khởi động Worker:**
   ```powershell
   python start_worker.py
   ```
4. **Dấu hiệu thành công trong Terminal:**
   ```text
   [BaseWorker] Worker started: worker_pc_rtx3060
   [BaseWorker] Worker Type: gpu
   [BaseWorker] GPU Available: True
   [BaseWorker] Capabilities: ['crawl_chapter', 'translate_moxhi', 'audio', 'video', 'merge_batch_video']
   [StorageFactory] Using HttpArtifactStorage (Connecting to http://192.168.1.147:8000)
   [BaseWorker] Heartbeat OK
   ```

---

## ✅ 4. TÓM TẮT CHECKLIST NHANH
- [x] Đã gộp text clean & validation vào `crawl_chapter`.
- [x] Đã xóa `preprocess_text` khỏi capabilities và executor registry.
- [x] Đã thêm `AUDIO_C = "audio"` vào `capabilities.py`.
- [x] Đã xóa `generate_thumbnail` và `generate_youtube_description` khỏi capabilities.
- [x] Đã chuyển `STORAGE_BACKEND` sang `http` hoặc `local` (bỏ hoàn toàn MinIO port 9000).
