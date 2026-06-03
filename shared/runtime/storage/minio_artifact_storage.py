from io import BytesIO
import json
from pathlib import Path

from minio import Minio

from shared.runtime.storage.base_artifact_storage import (
    BaseArtifactStorage
)
from shared.config.settings import settings
from minio.deleteobjects import DeleteObject

class MinioArtifactStorage(
    BaseArtifactStorage
):

    def __init__(self):

        self.bucket = settings.MINIO_BUCKET

        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )

    # =====================================
    # EXISTS
    # =====================================

    async def exists(
            self,
            path: str
    ) -> bool:

        try:



            self.client.stat_object(
                self.bucket,
                path
            )

            return True

        except Exception as e:

            print(
                "[MINIO EXISTS MISS]",
                path,
                repr(e)
            )

            return False

    # =====================================
    # WRITE TEXT
    # =====================================

    async def write_text(
        self,
        path: str,
        content: str
    ):

        data = content.encode("utf-8")

        self.client.put_object(

            self.bucket,

            path,

            BytesIO(data),

            length=len(data),

            content_type="text/plain"
        )

    # =====================================
    # READ TEXT
    # =====================================

    async def read_text(
        self,
        path: str
    ) -> str:

        response = self.client.get_object(
            self.bucket,
            path
        )

        data = response.read()

        return data.decode("utf-8")

    # =====================================
    # WRITE JSON
    # =====================================

    async def write_json(
        self,
        path: str,
        data: dict
    ):

        json_bytes = json.dumps(
            data,
            ensure_ascii=False,
            indent=2
        ).encode("utf-8")

        self.client.put_object(

            self.bucket,

            path,

            BytesIO(json_bytes),

            length=len(json_bytes),

            content_type="application/json"
        )

    # =====================================
    # READ JSON
    # =====================================

    async def read_json(
        self,
        path: str
    ) -> dict:

        content = await self.read_text(
            path
        )

        return json.loads(content)

    # =====================================
    # WRITE BYTES
    # =====================================

    async def write_bytes(
        self,
        path: str,
        data: bytes
    ):

        self.client.put_object(

            self.bucket,

            path,

            BytesIO(data),

            length=len(data),

            content_type="application/octet-stream"
        )

    # =====================================
    # READ BYTES
    # =====================================

    async def read_bytes(
        self,
        path: str
    ) -> bytes:

        response = self.client.get_object(
            self.bucket,
            path
        )

        return response.read()

    # =====================================
    # DELETE
    # =====================================

    async def delete(
            self,
            path: str
    ):

        # Nếu là file
        try:

            self.client.stat_object(
                self.bucket,
                path
            )

            self.client.remove_object(
                self.bucket,
                path
            )

            return

        except Exception:
            pass

        # Nếu là folder/prefix
        objects = [

            DeleteObject(
                obj.object_name
            )

            for obj in self.client.list_objects(
                self.bucket,
                prefix=path,
                recursive=True
            )
        ]

        if not objects:
            print(
                f"[MinioStorage] "
                f"No objects found: {path}"
            )

            return

        errors = self.client.remove_objects(
            self.bucket,
            objects
        )

        for err in errors:
            print(
                f"[MinioStorage] "
                f"Delete error: {err}"
            )

        print(
            f"[MinioStorage] "
            f"Deleted {len(objects)} objects "
            f"under {path}"
        )

    # =====================================
    # ENSURE DIR
    # =====================================

    async def ensure_dir(
        self,
        path: str
    ):

        # MinIO không cần directories thật
        return

    # =====================================
    # GET LOCAL PATH
    # =====================================

    async def get_local_path(
            self,
            path: str,
            workspace_dir: str
    ) -> str:

        data = await self.read_bytes(
            path
        )

        local_path = (
                Path(workspace_dir)
                / "downloads"
                / path
        )

        local_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        local_path.write_bytes(
            data
        )

        return str(local_path)