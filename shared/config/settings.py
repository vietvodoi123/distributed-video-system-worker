from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    # =====================================
    # MINIO
    # =====================================

    MINIO_ENDPOINT: str = "100.114.159.127:9000"

    MINIO_ACCESS_KEY: str = "admin"

    MINIO_SECRET_KEY: str = "password123"

    MINIO_BUCKET: str = "tts-system"

    MINIO_SECURE: bool = False

    # =====================================
    # WORKER
    # =====================================

    WORKER_POLL_INTERVAL: int = 5

    TASK_LEASE_SECONDS: int = 30

    # =====================================
    # API
    # =====================================

    API_BASE_URL: str = "http://100.114.159.127:8000"

    class Config:

        env_file = ".env"
    RUNWARE_API_KEY: str="CWIphkGEitqkHYtJBqoUJGvHxRGnZppO"

    RUNWARE_IMAGE_MODEL: str = "openai:gpt-image@2"

settings = Settings()