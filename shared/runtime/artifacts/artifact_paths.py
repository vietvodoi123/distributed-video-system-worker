from pathlib import Path
# ==========================================
# ROOT
# ==========================================
def get_project_root() -> Path:

    return (
        Path(__file__)
        .resolve()
        .parents[2]
    )
def get_batch_output_dir(
    batch_id:str
) -> str:

    return (
        f"batches/{batch_id}"
    )


def get_batch_manifest_path(
    batch_id:str
) -> str:

    return (
        f"batches/"
        f"{batch_id}/"
        f"manifest.json"
    )


# ==========================================
# CHAPTER ROOT
# ==========================================

def get_chapter_dir(
    batch_id:str,
    chapter_number:int
) -> str:

    return (

        f"batches/"
        f"{batch_id}/"
        f"chapters/"
        f"{chapter_number}"
    )


# ==========================================
# STAGE DIRS
# ==========================================

def get_raw_dir(
    batch_id:str,
    chapter_number:int
) -> str:

    return (
        f"{get_chapter_dir(batch_id, chapter_number)}/raw"
    )


def get_preprocess_dir(
    batch_id:str,
    chapter_number:int
) -> str:

    return (
        f"{get_chapter_dir(batch_id, chapter_number)}/preprocess"
    )


def get_translation_dir(
    batch_id:str,
    chapter_number:int
) -> str:

    return (
        f"{get_chapter_dir(batch_id, chapter_number)}/translation"
    )


def get_refine_dir(
    batch_id:str,
    chapter_number:int
) -> str:

    return (
        f"{get_chapter_dir(batch_id, chapter_number)}/refine"
    )


def get_audio_dir(
    batch_id:str,
    chapter_number:int
) -> str:

    return (
        f"{get_chapter_dir(batch_id, chapter_number)}/audio"
    )


def get_render_dir(
    batch_id:str,
    chapter_number:int
) -> str:

    return (
        f"{get_chapter_dir(batch_id, chapter_number)}/render"
    )


def get_metadata_dir(
    batch_id:str,
    chapter_number:int
) -> str:

    return (
        f"{get_chapter_dir(batch_id, chapter_number)}/metadata"
    )


# ==========================================
# FILES
# ==========================================

def get_raw_text_path(
    batch_id:str,
    chapter_number:int
) -> str:

    return (
        f"{get_raw_dir(batch_id, chapter_number)}/raw.txt"
    )


def get_preprocess_text_path(
    batch_id:str,
    chapter_number:int
) -> str:

    return (
        f"{get_preprocess_dir(batch_id, chapter_number)}/preprocess.txt"
    )


def get_translation_text_path(
    batch_id:str,
    chapter_number:int
) -> str:

    return (
        f"{get_translation_dir(batch_id, chapter_number)}/translated.txt"
    )


def get_final_script_path(
    batch_id:str,
    chapter_number:int
) -> str:

    return (
        f"{get_refine_dir(batch_id, chapter_number)}/final_script.txt"
    )


def get_audio_path(
    batch_id:str,
    chapter_number:int
) -> str:

    return (
        f"{get_audio_dir(batch_id, chapter_number)}/narration.wav"
    )


def get_render_video_path(
    batch_id:str,
    chapter_number:int
) -> str:

    return (
        f"{get_render_dir(batch_id, chapter_number)}/final.mp4"
    )


def get_youtube_description_path(
    batch_id:str,
    chapter_number:int
) -> str:

    return (
        f"{get_metadata_dir(batch_id, chapter_number)}/youtube_description.txt"
    )

def get_raw_html_path(
    batch_id: str,
    chapter_number: int
) -> str:

    return (
        f"{get_chapter_dir(batch_id, chapter_number)}"
        "/raw/raw.html"
    )

def get_raw_metadata_path(
    batch_id: str,
    chapter_number: int
) -> str:

    return (
        f"{get_chapter_dir(batch_id, chapter_number)}"
        "/raw/metadata.json"
    )

def get_crawl_manifest_path(
    batch_id: str,
    chapter_number: int
) -> str:

    return (
        f"{get_chapter_dir(batch_id, chapter_number)}"
        "/raw/crawl_manifest.json"
    )

# ==========================================
# TTS
# ==========================================

TTS_DIR = "tts"

TTS_SEGMENTS_DIR = "tts/segments"

TTS_MERGED_DIR = "tts/merged"

TTS_METADATA_DIR = "tts/metadata"

def get_tts_segment_dir(
    chapter_dir: str,
) -> str:

    return (
        f"{chapter_dir}/tts/segments/"
    )


def get_tts_segment_path(
    chapter_dir: str,
    line_index: int
) -> str:

    return (
        f"{chapter_dir}/tts/segments/"
        f"{line_index:04d}.wav"
    )

def get_timeline_path(
    chapter_dir: str
) -> str:

    return (
        f"{chapter_dir}/tts/metadata/"
        f"timeline.json"
    )

def get_narration_wav_path(
    chapter_dir: str
) -> str:

    return (
        f"{chapter_dir}/tts/merged/"
        f"narration.wav"
    )

# ==========================================
# VIDEO
# ==========================================

VIDEO_DIR = "video"

VIDEO_LAYERS_DIR = "video/layers"

VIDEO_FINAL_DIR = "video/final"


def get_video_dir(
    chapter_dir: str
) -> str:

    return (
        f"{chapter_dir}/video"
    )


def get_video_layers_dir(
    chapter_dir: str
) -> str:

    return (
        f"{chapter_dir}/video/layers"
    )


def get_video_final_dir(
    chapter_dir: str
) -> str:

    return (
        f"{chapter_dir}/video/final"
    )


# ==========================================
# VIDEO LAYERS
# ==========================================

def get_text_scroll_video_path(
    chapter_dir: str
) -> str:

    return (
        f"{chapter_dir}/video/layers/"
        f"text_scroll.mp4"
    )


def get_mc_loop_video_path(
    chapter_dir: str
) -> str:

    return (
        f"{chapter_dir}/video/layers/"
        f"mc_loop.mp4"
    )


def get_template_video_path(
    chapter_dir: str
) -> str:

    return (
        f"{chapter_dir}/video/layers/"
        f"template.mp4"
    )


def get_composited_video_path(
    chapter_dir: str
) -> str:

    return (
        f"{chapter_dir}/video/layers/"
        f"composited.mp4"
    )

def get_scroll_text_path(
    chapter_dir: str
) -> str:

    return (
        f"{chapter_dir}/video/metadata/"
        f"scroll_text.txt"
    )
# ==========================================
# STATIC ASSETS
# ==========================================



PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[3]
)

STATIC_ASSETS_DIR = (
    PROJECT_ROOT
    / "shared"
    / "runtime"
    / "static_assets"
)

STATIC_CACHE_DIR = (
    STATIC_ASSETS_DIR / "cache"
)

STATIC_CONTENT_DIR = (
    STATIC_ASSETS_DIR / "content"
)

# ==========================================
# FINAL VIDEO
# ==========================================

def get_final_video_path(
    chapter_dir: str
) -> str:

    return (
        f"{chapter_dir}/video/final/"
        f"final.mp4"
    )

# ==========================================
# TEXT SCROLL STATIC ASSETS
# ==========================================

def get_text_scroll_content_path() -> Path:

    return (
        STATIC_CONTENT_DIR
        / "text_scroll_content.txt"
    )


def get_text_scroll_cache_dir() -> Path:

    return (
        STATIC_CACHE_DIR
        / "text_scroll"
    )


def get_text_scroll_master_cache_path() -> Path:

    return (
        get_text_scroll_cache_dir()
        / "master.mp4"
    )


def get_text_scroll_master_manifest_path() -> Path:

    return (
        get_text_scroll_cache_dir()
        / "master_manifest.json"
    )

# ==========================================
# MC STATIC ASSETS
# ==========================================

def get_mc_cache_dir() -> Path:

    return (
        STATIC_CACHE_DIR
        / "mc_loop"
    )

# ==========================================
# BATCH FINAL OUTPUTS
# ==========================================


def get_batch_final_video_path(
    batch_id: str
) -> str:

    return (
        f"batches/{batch_id}/final/"
        f"final.mp4"
    )



def get_batch_youtube_description_path(
    batch_id: str
) -> str:

    return (
        f"batches/{batch_id}/metadata/"
        f"youtube_description.txt"
    )

# ==========================================
# BATCH THUMBNAIL
# ==========================================

def get_batch_thumbnail_path(
    batch_id: str
) -> str:

    return (
        f"batches/{batch_id}/metadata/"
        f"thumbnail.jpg"
    )


# ==========================================
# THUMBNAIL STATIC CACHE
# ==========================================

def get_thumbnail_cache_dir() -> Path:

    return (
        STATIC_CACHE_DIR
        / "thumbnails"
    )