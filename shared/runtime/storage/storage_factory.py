from shared.config.settings import settings
from shared.runtime.storage.local_shared_storage import (
    LocalSharedStorage
)
from shared.runtime.storage.http_artifact_storage import (
    HttpArtifactStorage
)


def create_storage():
    """
    Factory creating storage based on STORAGE_BACKEND setting:
    - 'http': Remote LAN HTTP client storage (calls Master's FastAPI /storage endpoints)
    - 'local': Direct NVMe/SSD filesystem storage (if worker runs directly on Master machine)
    - 'minio': Legacy S3 object storage (deprecated)
    """
    backend = getattr(settings, "STORAGE_BACKEND", "http").lower()

    if backend == "http":
        base_url = (
            getattr(settings, "API_BASE_URL", None)
            or getattr(settings.api, "base_url", "http://192.168.1.147:8000")
        )
        print(
            "[StorageFactory] "
            f"Using HttpArtifactStorage (Connecting to {base_url})"
        )
        return HttpArtifactStorage(base_url=base_url)

    if backend == "minio":
        try:
            from shared.runtime.storage.minio_artifact_storage import (
                MinioArtifactStorage
            )
            print("[StorageFactory] Using MinioArtifactStorage (Legacy)")
            return MinioArtifactStorage()
        except Exception:
            print("[StorageFactory] Minio not available, falling back to HttpArtifactStorage")
            base_url = (
                getattr(settings, "API_BASE_URL", None)
                or getattr(settings.api, "base_url", "http://192.168.1.147:8000")
            )
            return HttpArtifactStorage(base_url=base_url)

    print(
        "[StorageFactory] "
        "Using LocalSharedStorage (Native High-Speed Local Storage)"
    )
    return LocalSharedStorage(
        root_dir=getattr(settings, "STORAGE_ROOT_DIR", "storage")
    )
