from shared.runtime.storage.minio_artifact_storage import (
    MinioArtifactStorage
)


def create_storage():

    print(
        "[StorageFactory] "
        "Using MinioArtifactStorage"
    )

    return MinioArtifactStorage()