from pathlib import Path

from shared.runtime.executors.audio.service.tts_service import TTSService
from shared.runtime.executors.audio.service.models import TTSOptions
from models import TTSOptions


MODEL_PATH = Path(
    r"/shared/data/model\ngochuyennew.onnx"
)

OUTPUT_DIR = Path(
    r"C:\Users\HLC\PycharmProjects\distributed-video-system-worker\shared\runtime\executors\audio\test-output"
)

TEXT = (
    "Xin chào. Đây là đoạn văn bản "
    "dùng để kiểm tra tốc độ đọc của mô hình."
)


def main():

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    service = TTSService(
        model_path=MODEL_PATH,
    )

    print(f"Model: {MODEL_PATH}")
    print(f"Sample rate: {service.sample_rate}")
    print()

    for name, speed in [
        ("slow", 1.2),
        ("normal", 1.5),
        ("fast", 1.3),
    ]:

        output_file = (
            OUTPUT_DIR / f"{name}.wav"
        )

        result = service.synthesize_text(
            text=TEXT,
            output_file=output_file,
            options=TTSOptions(
                volume=1.5,
                sentence_silence=0.0,
            ),
        )

        print(
            f"{name:8} | "
            f"speed={result.speed:.2f} | "
            f"length_scale={result.length_scale:.4f} | "
            f"duration={result.duration:.3f}s | "
            f"{result.output_file}"
        )


if __name__ == "__main__":
    main()