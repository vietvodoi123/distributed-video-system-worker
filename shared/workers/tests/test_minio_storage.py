import pytest

from shared.runtime.storage.minio_artifact_storage import (
    MinioArtifactStorage
)


@pytest.mark.asyncio
async def test_minio_write_read():

    storage = (
        MinioArtifactStorage()
    )

    path = (
        "test/hello.txt"
    )

    await storage.write_text(
        path,
        "hello world"
    )

    exists = await storage.exists(
        path
    )

    assert exists is True

    content = await storage.read_text(
        path
    )

    assert content == "hello world"