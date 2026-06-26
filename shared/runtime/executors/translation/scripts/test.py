import os
from pathlib import Path

os.environ["HACHIMIMT_MODELS_DIR"] = r"C:\Users\HLC\PycharmProjects\distributed-video-system-worker\shared\runtime\executors\translation\models"

from translator import HachimiTranslator

PROJECT_ROOT = Path(__file__).resolve().parent.parent

translator = HachimiTranslator()

print(translator.load("HachimiMT-30"))



translated = translator.translate_text(
    "古武天才傲天遇害血染混沌之玉穿越异界，重生华夏神龙，以无上龙体泡泡妞，揍圣域，砍传奇，灭半神，神挡杀神！",
    chunk_mode="sentence",   # hoặc "paragraph"
    beam_size=1,
)


print(translated)