from pathlib import Path

import yaml
from pydantic import BaseModel


class MinioSettings(BaseModel):
    endpoint: str
    access_key: str
    secret_key: str
    bucket: str
    secure: bool


class WorkerSettings(BaseModel):
    poll_interval: int
    task_lease_seconds: int


class ApiSettings(BaseModel):
    base_url: str


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
    token_dir:str
    api_key: str

class FontSetting(BaseModel):
    font_path: str

class OpenAiSetting(BaseModel):
    open_ai_api_key: str

class TranslationSetting(BaseModel):
    chunk_max_chars: int

class Settings(BaseModel):
    minio: MinioSettings
    worker: WorkerSettings
    api: ApiSettings
    runware: RunwareSettings
    llm: LLMSettings
    youtube: YoutubeSettings
    font: FontSetting
    open_ai: OpenAiSetting
    capabilities: list[str]
    translation: TranslationSetting

    @classmethod
    def load(cls, path: str | Path):
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        return cls.model_validate(data)


settings = Settings.load(
    Path(__file__).with_name("settings.yaml")
)