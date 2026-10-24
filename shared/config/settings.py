import os
from pathlib import Path
from dotenv import load_dotenv
import yaml
from pydantic import BaseModel


class MinioSettings(BaseModel):
    endpoint: str = ""
    access_key: str = ""
    secret_key: str = ""
    bucket: str = ""
    secure: bool = False


class WorkerSettings(BaseModel):
    poll_interval: int = 5
    task_lease_seconds: int = 30
    max_slots: int = 2
    max_audio_slots: int = 2
    max_video_slots: int = 1


class ApiSettings(BaseModel):
    base_url: str = "http://192.168.1.147:8000"
    translate_moxhi: str = "http://192.168.1.147:8090"
    flaresolverr: str = "http://192.168.1.147:8191/v1"


class CrawlerSettings(BaseModel):
    flaresolverr_url: str = "http://192.168.1.147:8191/v1"


class RunwareSettings(BaseModel):
    api_key: str
    model: str


class GeminiSettings(BaseModel):
    model: str
    api_keys: list[str]
    timeout: int
    cooldown_seconds: int
    max_retry: int
    max_concurrent_requests: int


class LLMSettings(BaseModel):
    gemini: GeminiSettings


class YoutubeSettings(BaseModel):
    client_secret_file: str
    token_dir: str
    api_key: str


class FontSetting(BaseModel):
    font_path: str


class OpenAiSetting(BaseModel):
    open_ai_api_key: str


class TranslationSetting(BaseModel):
    chunk_max_chars: int


class ttsSetting(BaseModel):
    tts_model: str
    max_concurrency: int = 10
    default_speed: float = 1.2


class VideoRenderSetting(BaseModel):
    num_workers: int = 2
    frame_jpeg_quality: int = 70
    acceleration: str = "auto"
    nvenc_preset: str = "p1"
    nvenc_cq: int = 27
    cpu_preset: str = "ultrafast"
    cpu_crf: int = 27
    target_bitrate: str = "2M"
    max_bitrate: str = "3M"
    bufsize: str = "6M"


class Settings(BaseModel):
    minio: MinioSettings | None = None
    worker: WorkerSettings = WorkerSettings()
    api: ApiSettings = ApiSettings()
    crawler: CrawlerSettings = CrawlerSettings()
    runware: RunwareSettings | None = None
    llm: LLMSettings | None = None
    youtube: YoutubeSettings | None = None
    font: FontSetting | None = None
    open_ai: OpenAiSetting | None = None
    capabilities: list[str] = []
    translation: TranslationSetting = TranslationSetting(chunk_max_chars=6000)
    tts: ttsSetting = ttsSetting(tts_model="shared/data/model/ngochuyennew.onnx")
    video_render: VideoRenderSetting = VideoRenderSetting()

    # Worker deployment settings (aligned with master server & .env)
    API_BASE_URL: str = "http://192.168.1.147:8000"
    STORAGE_BACKEND: str = "http"
    STORAGE_ROOT_DIR: str = "storage"
    WORKER_ID: str = "worker_pc_rtx3060"
    WORKER_TYPE: str = "gpu"
    WORKER_POLL_INTERVAL: int = 5
    TASK_LEASE_SECONDS: int = 30
    FLARESOLVERR_URL: str = "http://192.168.1.147:8191/v1"

    @classmethod
    def load(cls, path: str | Path):
        load_dotenv()

        data: dict = {}
        target_path = Path(path)
        if target_path.exists():
            with open(target_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}

        # Merge environment variables (override yaml)
        api_base = os.getenv(
            "API_BASE_URL",
            data.get("api", {}).get("base_url", "http://192.168.1.147:8000")
        )
        translate_moxhi = os.getenv(
            "TRANSLATE_MOXHI_URL",
            data.get("api", {}).get("translate_moxhi", "http://192.168.1.147:8090")
        )
        flaresolverr_url = os.getenv(
            "FLARESOLVERR_URL",
            data.get("crawler", {}).get(
                "flaresolverr_url",
                data.get("api", {}).get("flaresolverr", "http://192.168.1.147:8191/v1")
            )
        )
        storage_backend = os.getenv("STORAGE_BACKEND", "http")
        storage_root_dir = os.getenv("STORAGE_ROOT_DIR", "storage")
        worker_id = os.getenv("WORKER_ID", "worker_pc_rtx3060")
        worker_type = os.getenv("WORKER_TYPE", "gpu")
        poll_interval = int(os.getenv(
            "WORKER_POLL_INTERVAL",
            str(data.get("worker", {}).get("poll_interval", 5))
        ))
        lease_seconds = int(os.getenv(
            "TASK_LEASE_SECONDS",
            str(data.get("worker", {}).get("task_lease_seconds", 30))
        ))

        data["API_BASE_URL"] = api_base
        data["STORAGE_BACKEND"] = storage_backend
        data["STORAGE_ROOT_DIR"] = storage_root_dir
        data["WORKER_ID"] = worker_id
        data["WORKER_TYPE"] = worker_type
        data["WORKER_POLL_INTERVAL"] = poll_interval
        data["TASK_LEASE_SECONDS"] = lease_seconds
        data["FLARESOLVERR_URL"] = flaresolverr_url

        if "api" not in data:
            data["api"] = {}
        data["api"]["base_url"] = api_base
        data["api"]["translate_moxhi"] = translate_moxhi
        data["api"]["flaresolverr"] = flaresolverr_url

        if "crawler" not in data:
            data["crawler"] = {}
        data["crawler"]["flaresolverr_url"] = flaresolverr_url

        if "minio" not in data:
            data["minio"] = {}
        if os.getenv("MINIO_ENDPOINT"):
            data["minio"]["endpoint"] = os.getenv("MINIO_ENDPOINT")
        if os.getenv("MINIO_ACCESS_KEY"):
            data["minio"]["access_key"] = os.getenv("MINIO_ACCESS_KEY")
        if os.getenv("MINIO_SECRET_KEY"):
            data["minio"]["secret_key"] = os.getenv("MINIO_SECRET_KEY")
        if os.getenv("MINIO_BUCKET"):
            data["minio"]["bucket"] = os.getenv("MINIO_BUCKET")

        if "worker" not in data:
            data["worker"] = {}
        data["worker"]["poll_interval"] = poll_interval
        data["worker"]["task_lease_seconds"] = lease_seconds

        if "runware" in data and os.getenv("RUNWARE_API_KEY"):
            data["runware"]["api_key"] = os.getenv("RUNWARE_API_KEY")

        return cls.model_validate(data)


settings = Settings.load(
    Path(__file__).with_name("settings.yaml")
)
