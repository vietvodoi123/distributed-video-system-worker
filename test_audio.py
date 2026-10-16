import asyncio
import os
import sys
import time
import wave
from pathlib import Path

# Đảm bảo in tiếng Việt trên console Windows không bị lỗi font
sys.stdout.reconfigure(encoding="utf-8")

import numpy as np

from shared.config.settings import settings
from shared.runtime.executors.audio.service.models import TTSOptions
from shared.runtime.executors.audio.service.tts_service import TTSService
from shared.runtime.executors.audio.utils.audio_concat import concat_wav_files

ROOT_DIR = Path(__file__).resolve().parent
MODEL_PATH = ROOT_DIR / "shared/data/model/ngochuyennew.onnx"
CONFIG_PATH = ROOT_DIR / "shared/data/model/ngochuyennew.onnx.json"
OUTPUT_DIR = ROOT_DIR / "output_test"

# Đoạn văn bản mẫu kiểm tra đa dạng tình huống (câu thường, hội thoại, câu ngắn, ngắt nhịp)
SAMPLE_LINES = [
    "Chương 1: Mở đầu cuộc hành trình bí ẩn.",
    "Bóng đêm dần bao trùm lên khắp ngôi làng cổ kính dưới chân núi.",
    "Tiếng gió rít qua từng khe cửa, mang theo hơi lạnh buốt giá của mùa đông.",
    "Hắn khẽ mở mắt, nhìn về phía khoảng không vô định trước mặt.",
    '"Ai đang ở ngoài đó?" - Hắn cất tiếng hỏi, nhưng chỉ có tiếng gió đáp lại.',
    "...",  # Dòng dấu câu để kiểm tra cơ chế fallback chống file 0-byte
    "Một bóng đen lướt nhanh qua tán cây rồi biến mất tăm.",
    "Chuyến phiêu lưu đầy nguy hiểm và kịch tính chính thức bắt đầu từ đây!",
]


def check_audio_file(file_path: Path) -> dict:
    """Kiểm tra tính hợp lệ và cường độ âm thanh của file WAV."""
    if not file_path.exists():
        return {"valid": False, "error": "File does not exist"}

    file_size = file_path.stat().st_size
    if file_size <= 44:
        return {"valid": False, "error": "Empty or header-only file"}

    with wave.open(str(file_path), "rb") as w:
        sample_rate = w.getframerate()
        channels = w.getnchannels()
        sampwidth = w.getsampwidth()
        n_frames = w.getnframes()
        duration = n_frames / sample_rate

        raw_bytes = w.readframes(n_frames)
        data = np.frombuffer(raw_bytes, dtype=np.int16)

        max_amp = int(np.max(np.abs(data))) if len(data) > 0 else 0
        mean_amp = float(np.mean(np.abs(data))) if len(data) > 0 else 0.0

    # Âm thanh được coi là có tiếng thực sự nếu max_amp > 1000
    has_sound = max_amp > 1000

    return {
        "valid": True,
        "sample_rate": sample_rate,
        "channels": channels,
        "sampwidth": sampwidth,
        "n_frames": n_frames,
        "duration": duration,
        "file_size": file_size,
        "max_amp": max_amp,
        "mean_amp": mean_amp,
        "has_sound": has_sound,
    }


async def run_single_chapter_test(tts_service: TTSService, task_name: str = "Task-1"):
    """Mô phỏng 1 task AudioExecutor chạy tổng hợp và ghép audio."""
    print(f"\n========================================================")
    print(f"  [BẮT ĐẦU] {task_name}: Kiểm tra tổng hợp & ghép audio")
    print(f"========================================================")

    task_dir = OUTPUT_DIR / task_name
    task_dir.mkdir(parents=True, exist_ok=True)

    started_at = time.time()
    options = TTSOptions(speed=1.0, volume=1.0, sentence_silence=0.0)

    # 1. Tổng hợp từng dòng song song qua Semaphore dùng chung
    async def synthesize_one(idx: int, line_text: str):
        line_out = task_dir / f"line_{idx:03d}.wav"
        t0 = time.time()
        result = await tts_service.synthesize_text_async(
            text=line_text,
            output_file=line_out,
            options=options,
        )
        elapsed = time.time() - t0
        return {
            "index": idx,
            "text": line_text,
            "output": line_out,
            "duration": result.duration,
            "elapsed": elapsed,
        }

    print(f"[{task_name}] Đang tổng hợp song song {len(SAMPLE_LINES)} dòng...")
    segments = await asyncio.gather(
        *(synthesize_one(i, line) for i, line in enumerate(SAMPLE_LINES))
    )

    print(f"\n[{task_name}] --- Danh sách các Segment ---")
    current_time = 0.0
    sum_durations = 0.0
    for seg in segments:
        start_t = round(current_time, 3)
        end_t = round(start_t + seg["duration"], 3)
        sum_durations += seg["duration"]
        current_time = end_t
        preview = (seg["text"][:30] + "...") if len(seg["text"]) > 30 else seg["text"]
        print(
            f"  Line {seg['index']:02d} | [{start_t:6.2f}s -> {end_t:6.2f}s] "
            f"(dur: {seg['duration']:5.2f}s | TTS: {seg['elapsed']:.2f}s) | \"{preview}\""
        )

    # 2. Ghép audio (Native Wave Concat)
    merged_file = task_dir / "merged_final.wav"
    input_files = [seg["output"] for seg in segments]

    t_concat_start = time.time()
    await concat_wav_files(
        input_files=input_files,
        output_file=merged_file,
        workspace_dir=task_dir,
        apply_loudnorm=False,
    )
    concat_elapsed = time.time() - t_concat_start

    # 3. Kiểm định chất lượng file merged
    info = check_audio_file(merged_file)
    total_elapsed = time.time() - started_at

    print(f"\n[{task_name}] --- Kết Quả File Merged ---")
    print(f"  Đường dẫn file: {merged_file}")
    print(f"  Thời gian ghép (concat): {concat_elapsed:.4f} giây")
    print(f"  Tổng thời gian xử lý:    {total_elapsed:.2f} giây")
    print(f"  Độ dài tính từ segments: {sum_durations:.3f} giây")
    print(f"  Độ dài thực tế file WAV: {info['duration']:.3f} giây")
    print(f"  Độ lệch timeline:        {abs(info['duration'] - sum_durations):.4f} giây")
    print(f"  Cường độ âm thanh max:   {info['max_amp']}/32767")
    print(f"  Cường độ âm thanh TB:    {info['mean_amp']:.1f}")
    print(f"  Trạng thái âm thanh:     {'✅ CÓ TIẾNG RÕ RÀNG' if info['has_sound'] else '❌ BỊ CÂM / MẤT TIẾNG'}")

    assert info["has_sound"], f"LỖI: File {merged_file} không có âm thanh!"
    assert abs(info["duration"] - sum_durations) < 0.01, "LỖI: Lệch timeline giữa segment và audio!"

    return merged_file


async def run_concurrent_tasks_test(tts_service: TTSService):
    """Mô phỏng 2 task Audio chạy đồng thời cùng lúc để kiểm tra độ ổn định."""
    print(f"\n========================================================")
    print(f"  [TEST NÂNG CAO] Chạy đồng thời 2 Task Audio cùng lúc")
    print(f"========================================================")

    t0 = time.time()
    res1, res2 = await asyncio.gather(
        run_single_chapter_test(tts_service, task_name="Task-A"),
        run_single_chapter_test(tts_service, task_name="Task-B"),
    )
    elapsed = time.time() - t0

    print(f"\n========================================================")
    print(f"  ✅ TẤT CẢ CÁC BÀI TEST ĐÃ HOÀN THÀNH XUẤT SẮC!")
    print(f"  Tổng thời gian chạy 2 task song song: {elapsed:.2f}s")
    print(f"  File Task-A: {res1}")
    print(f"  File Task-B: {res2}")
    print(f"  👉 Bạn có thể mở 2 file WAV trên để nghe thử giọng đọc!")
    print(f"========================================================\n")


async def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("========================================================")
    print("  KIỂM TRA HỆ THỐNG AUDIO EXECUTOR & TTS PIPER")
    print("========================================================")
    print(f"Model ONNX:    {MODEL_PATH}")
    print(f"Model tồn tại: {'Có' if MODEL_PATH.exists() else 'KHÔNG TÌM THẤY'}")

    if not MODEL_PATH.exists():
        print(f"Lỗi: Không tìm thấy file model tại {MODEL_PATH}")
        return

    # Khởi tạo TTSService với max_concurrency = 3
    tts_concurrency = getattr(settings.tts, "max_concurrency", 3)
    tts_service = TTSService(
        model_path=MODEL_PATH,
        config_path=CONFIG_PATH,
        use_cuda=False,
        max_concurrency=tts_concurrency,
    )
    print(f"Sample Rate:   {tts_service.sample_rate} Hz")
    print(f"Max Worker Concurrency: {tts_service.max_concurrency}")

    # Chạy test đơn trước
    await run_single_chapter_test(tts_service, task_name="Single-Chapter-Test")

    # Tiếp tục chạy test mô phỏng 2 task đồng thời
    await run_concurrent_tasks_test(tts_service)


if __name__ == "__main__":
    asyncio.run(main())
