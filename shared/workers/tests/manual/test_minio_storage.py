import asyncio

from shared.runtime.storage.minio_artifact_storage import (
    MinioArtifactStorage
)


async def main():

    storage = (
        MinioArtifactStorage()
    )

    path = (
        "test/hello.txt"
    )

    print("Writing...")

    await storage.write_text(
        path,
        "hello world"
    )

    print("Checking exists...")

    exists = await storage.exists(
        path
    )

    print(
        "Exists:",
        exists
    )

    print("Reading...")

    content = await storage.read_text(
        path
    )

    print(
        "Content:",
        content
    )


if __name__ == "__main__":

    asyncio.run(
        main()
    )