import json
from pathlib import Path
import aiohttp

from shared.config.settings import settings
from shared.runtime.storage.base_artifact_storage import BaseArtifactStorage


class HttpArtifactStorage(BaseArtifactStorage):
    """
    Artifact Storage client for workers communicating directly with FastAPI Master /storage endpoints over LAN.
    No MinIO, no S3 credentials, no extra ports needed.
    """

    def __init__(
        self,
        base_url: str | None = None,
        cache_dir: str = "workspace/cache"
    ):
        raw_url = base_url or getattr(settings, "API_BASE_URL", getattr(settings.api, "base_url", "http://192.168.1.147:8000"))
        self.base_url = str(raw_url).rstrip("/")
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = aiohttp.ClientTimeout(total=300)

    async def exists(self, path: str) -> bool:
        url = f"{self.base_url}/storage/exists"
        params = {"path": path}
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("exists", False)
                    return False
        except Exception:
            return False

    async def ensure_dir(self, path: str):
        # Server handles directory creation on upload
        pass

    async def delete(self, path: str):
        url = f"{self.base_url}/storage/files/{path}"
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.delete(url) as resp:
                    pass
        except Exception:
            pass

    async def read_text(self, path: str) -> str:
        data = await self.read_bytes(path)
        return data.decode("utf-8")

    async def write_text(self, path: str, content: str):
        data = content.encode("utf-8")
        await self.write_bytes(path, data)

    async def read_bytes(self, path: str) -> bytes:
        url = f"{self.base_url}/storage/files/{path}"
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            async with session.get(url) as resp:
                resp.raise_for_status()
                return await resp.read()

    async def write_bytes(self, path: str, content: bytes):
        url = f"{self.base_url}/storage/upload"
        params = {"path": path}

        data = aiohttp.FormData()
        filename = Path(path).name or "file.bin"
        data.add_field("file", content, filename=filename)

        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            async with session.post(url, params=params, data=data) as resp:
                resp.raise_for_status()

    async def upload_file(self, remote_path: str, local_file_path: str):
        """
        Upload local file directly from disk via multipart/form-data.
        """
        url = f"{self.base_url}/storage/upload"
        params = {"path": remote_path}
        local_p = Path(local_file_path)
        filename = local_p.name or "file.bin"

        with open(local_file_path, "rb") as f:
            data = aiohttp.FormData()
            data.add_field("file", f, filename=filename)
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(url, params=params, data=data) as resp:
                    resp.raise_for_status()

    async def read_json(self, path: str) -> dict:
        text = await self.read_text(path)
        return json.loads(text)

    async def write_json(self, path: str, content: dict):
        text = json.dumps(content, ensure_ascii=False, indent=2)
        await self.write_text(path, text)

    async def get_local_path(
        self,
        path: str,
        workspace_dir: str = None
    ) -> str:
        """
        Download the artifact from the server into the local cache directory
        and return the local filesystem path.
        """
        local_target = (Path(workspace_dir) if workspace_dir else self.cache_dir) / path
        local_target.parent.mkdir(parents=True, exist_ok=True)

        content = await self.read_bytes(path)
        local_target.write_bytes(content)

        return str(local_target)
