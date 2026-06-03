from shared.runtime.storage.local_shared_storage import LocalSharedStorage
import asyncio
async def main():
    storage = LocalSharedStorage()

    await storage.write_text(
        "test/a.txt",
        "hello"
    )

    text = await storage.read_text(
        "test/a.txt"
    )

    print(text)
    print(storage.root_dir.absolute())

if __name__ == "__main__":
    asyncio.run(main())