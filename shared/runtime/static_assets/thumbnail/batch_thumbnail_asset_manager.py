import hashlib
import json
import uuid
from shared.runtime.static_assets.thumbnail.services.compose_thumbnail import (
    compose_thumbnail
)

from shared.runtime.static_assets.thumbnail.services.compress_thumbnail import (
    compress_thumbnail
)
from pathlib import Path

import aiohttp

from shared.runtime.artifacts.artifact_paths import (
    get_thumbnail_cache_dir
)


class BatchThumbnailAssetManager:

    asset_name = "batch_thumbnail"

    # =====================================
    # INIT
    # =====================================

    def __init__(
        self,
        title: str,
        description: str,
        thumbnail_hook: str,
        artifact_storage,
        runware_api_key: str,
        font_path: str,
        episode_text: str,
        story_id:str,
        model: str = "runware:100@1",
    ):

        self.title = (
            title.strip()
        )

        self.story_id = story_id

        self.description = (
            description.strip()
        )

        self.thumbnail_hook = (
            thumbnail_hook.strip()
        )

        self.artifact_storage = (
            artifact_storage
        )
        self.font_path = (
            font_path
        )

        self.episode_text = (
            episode_text
        )
        self.runware_api_key = (
            runware_api_key
        )

        self.model = model

    # =====================================
    # CACHE KEY
    # =====================================

    def get_cache_key(
            self
    ) -> str:

        return str(
            self.story_id
        )

    def get_remote_raw_path(
            self
    ) -> str:

        return (
            "static_assets/"
            "thumbnails/"
            f"{self.story_id}/"
            "raw.png"
        )
    # =====================================
    # CACHE DIR
    # =====================================

    def get_cache_dir(
        self
    ) -> Path:

        return (
            get_thumbnail_cache_dir()
            / self.get_cache_key()
        )

    # =====================================
    # LOCAL CACHE FILES
    # =====================================
    def get_local_raw_path(
        self
    ) -> Path:

        return (
            self.get_cache_dir()
            / "raw.png"
        )

    def get_local_thumbnail_path(
        self
    ) -> Path:

        return (
            self.get_cache_dir()
            / "thumbnail.png"
        )

    def get_local_manifest_path(
        self
    ) -> Path:

        return (
            self.get_cache_dir()
            / "manifest.json"
        )

    def get_local_prompt_path(
        self
    ) -> Path:

        return (
            self.get_cache_dir()
            / "prompt.txt"
        )

    # =====================================
    # REMOTE CACHE FILES
    # =====================================

    def get_remote_thumbnail_path(
        self
    ) -> str:

        return (
            "static_assets/"
            "thumbnails/"
            f"{self.get_cache_key()}/"
            "thumbnail.png"
        )

    def get_remote_manifest_path(
        self
    ) -> str:

        return (
            "static_assets/"
            "thumbnails/"
            f"{self.get_cache_key()}/"
            "manifest.json"
        )

    def get_remote_prompt_path(
        self
    ) -> str:

        return (
            "static_assets/"
            "thumbnails/"
            f"{self.get_cache_key()}/"
            "prompt.txt"
        )

    # =====================================
    # PROMPT
    # =====================================

    def build_prompt(
        self
    ) -> str:

        return f"""
        Create a cinematic anime webnovel thumbnail.

        TITLE:
        {self.title}

        STORY DESCRIPTION:
        {self.description}

        THUMBNAIL HOOK:
        {self.thumbnail_hook}

        STYLE REQUIREMENTS:
        - anime cinematic scene
        - emotional lighting
        - dramatic composition
        - highly detailed
        - ultra quality
        - youtube thumbnail style
        - eye catching
        - vibrant contrast

        IMPORTANT:
        - absolutely no text
        - no letters
        - no words
        - no typography
        - no captions
        - no subtitles
        - no watermark
        - no signature
        - no logo
        - no UI
        - clean image background only
        - text-free image
        """.strip()

    # =====================================
    # CACHE CHECK
    # =====================================

    async def ensure_cache_exists(
        self
    ) -> Path:

        cache_dir = (
            self.get_cache_dir()
        )

        cache_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        local_thumbnail = (
            self.get_local_thumbnail_path()
        )

        # =================================
        # LOCAL CACHE HIT
        # =================================

        raw_path = (
            self.get_local_raw_path()
        )

        # =================================
        # RAW CACHE HIT
        # =================================

        if raw_path.exists():
            print(
                "[BatchThumbnailAssetManager] "
                "Using cached RAW image"
            )

            # =============================
            # RE-COMPOSE THUMBNAIL
            # =============================

            compose_thumbnail(

                input_path=
                raw_path,

                output_path=
                local_thumbnail,

                title=
                self.title,

                thumbnail_hook=
                self.thumbnail_hook,

                episode_text=
                self.episode_text,

                font_path=
                self.font_path,
            )

            # =============================
            # COMPRESS
            # =============================

            compressed_path = (
                compress_thumbnail(
                    local_thumbnail
                )
            )

            return compressed_path

        remote_raw = (
            self.get_remote_raw_path()
        )

        if await self.artifact_storage.exists(
                remote_raw
        ):
            print(
                "[BatchThumbnailAssetManager] "
                "Downloading RAW image "
                "from storage..."
            )

            temp_path = await (
                self.artifact_storage
                .get_local_path(
                    remote_raw
                )
            )

            raw_path.write_bytes(
                Path(temp_path).read_bytes()
            )

            print(
                "[BatchThumbnailAssetManager] "
                "RAW restored"
            )

            compose_thumbnail(

                input_path=
                raw_path,

                output_path=
                local_thumbnail,

                title=
                self.title,

                thumbnail_hook=
                self.thumbnail_hook,

                episode_text=
                self.episode_text,

                font_path=
                self.font_path,
            )

            compressed_path = (
                compress_thumbnail(
                    local_thumbnail
                )
            )

            return compressed_path

        # =================================
        # GENERATE
        # =================================

        print(
            "[BatchThumbnailAssetManager] "
            "Generating thumbnail..."
        )

        image_bytes = await (
            self.generate_thumbnail()
        )

        # ==============================
        # SAVE RAW
        # ==============================

        raw_path = (
            self.get_local_raw_path()
        )

        raw_path.write_bytes(
            image_bytes
        )

        # ==============================
        # COMPOSE FINAL
        # ==============================

        compose_thumbnail(

            input_path=
            raw_path,

            output_path=
            local_thumbnail,

            title=
            self.title,

            thumbnail_hook=
            self.thumbnail_hook,

            episode_text=
            self.episode_text,

            font_path=
            self.font_path,
        )
        # ==============================
        # COMPRESS
        # ==============================

        compressed_path = (
            compress_thumbnail(
                local_thumbnail
            )
        )

        local_thumbnail = (
            compressed_path
        )
        # =================================
        # SAVE PROMPT
        # =================================

        prompt = self.build_prompt()

        self.get_local_prompt_path().write_text(
            prompt,
            encoding="utf-8"
        )

        # =================================
        # MANIFEST
        # =================================

        manifest = {

            "cache_key":
            self.get_cache_key(),

            "model":
            self.model,

            "title":
            self.title,

            "thumbnail_hook":
            self.thumbnail_hook,

            "remote_thumbnail":
            str(local_thumbnail),

            "episode_text":
                self.episode_text,
            "font_path":
                str(self.font_path),
        }

        self.get_local_manifest_path().write_text(

            json.dumps(
                manifest,
                indent=2,
                ensure_ascii=False,
                default=str
            ),

            encoding="utf-8"
        )

        # =================================
        # UPLOAD STORAGE
        # =================================

        await self.artifact_storage.write_bytes(

            self.get_remote_raw_path(),

            image_bytes
        )

        await self.artifact_storage.write_json(

            self.get_remote_manifest_path(),

            manifest
        )

        await self.artifact_storage.write_bytes(

            self.get_remote_prompt_path(),

            prompt.encode("utf-8")
        )

        print(
            "[BatchThumbnailAssetManager] "
            "Thumbnail cached successfully"
        )

        return local_thumbnail

    # =====================================
    # RUNWARE GENERATION
    # =====================================

    async def generate_thumbnail(
            self
    ) -> bytes:

        import asyncio

        prompt = self.build_prompt()

        # =================================
        # SHORTER DESCRIPTION
        # =================================

        if len(prompt) > 2000:
            prompt = prompt[:2000]

        task_uuid = str(
            uuid.uuid4()
        )

        payload = [
            {
                "taskType": "imageInference",

                "taskUUID": task_uuid,

                "positivePrompt": prompt,

                "width": 1152,
                "height": 640,

                "model": self.model,

                "numberResults": 1,

                # QUAN TRỌNG
                "deliveryMethod": "async"
            }
        ]

        headers = {

            "Authorization":
                f"Bearer {self.runware_api_key}",

            "Content-Type":
                "application/json",
        }

        timeout = aiohttp.ClientTimeout(
            total=180
        )

        # =================================
        # SUBMIT TASK
        # =================================

        print(
            "[BatchThumbnailAssetManager] "
            "Submitting async Runware task..."
        )

        async with aiohttp.ClientSession(
                timeout=timeout
        ) as session:

            async with session.post(

                    "https://api.runware.ai/v1",

                    json=payload,

                    headers=headers

            ) as response:

                text = await response.text()

                if response.status != 200:
                    raise RuntimeError(
                        f"Runware submit error: "
                        f"{response.status} - {text}"
                    )

                try:

                    submit_data = json.loads(
                        text
                    )

                except Exception:

                    raise RuntimeError(
                        f"Invalid Runware response: "
                        f"{text}"
                    )

        print(
            "[BatchThumbnailAssetManager] "
            f"Task submitted: "
            f"{task_uuid}"
        )

        # =================================
        # POLLING
        # =================================

        max_poll_attempts = 60

        for attempt in range(
                max_poll_attempts
        ):

            wait_time = min(
                2 + attempt,
                10
            )

            await asyncio.sleep(
                wait_time
            )

            poll_payload = [
                {
                    "taskType":
                        "getResponse",

                    "taskUUID":
                        task_uuid
                }
            ]

            print(
                "[BatchThumbnailAssetManager] "
                f"Polling attempt "
                f"{attempt + 1}/"
                f"{max_poll_attempts}"
            )

            async with aiohttp.ClientSession(
                    timeout=timeout
            ) as session:

                async with session.post(

                        "https://api.runware.ai/v1",

                        json=poll_payload,

                        headers=headers

                ) as response:

                    text = await response.text()

                    if response.status != 200:
                        print(
                            "[BatchThumbnailAssetManager] "
                            f"Polling HTTP error: "
                            f"{response.status}"
                        )

                        continue

                    try:

                        poll_data = json.loads(
                            text
                        )

                    except Exception:

                        print(
                            "[BatchThumbnailAssetManager] "
                            "Invalid polling JSON"
                        )

                        continue

            # =============================
            # ERRORS
            # =============================

            errors = poll_data.get(
                "errors",
                []
            )

            if errors:

                error = errors[0]

                code = error.get(
                    "code",
                    "unknown"
                )

                message = error.get(
                    "message",
                    "Unknown error"
                )

                retryable_codes = {

                    "failedTaskTimeout",

                    "timeoutProvider",

                    "providerRateLimitExceeded"
                }

                if code in retryable_codes:
                    print(
                        "[BatchThumbnailAssetManager] "
                        f"Retryable polling error: "
                        f"{code} - {message}"
                    )

                    continue

                raise RuntimeError(
                    f"Runware polling error: "
                    f"{code} - {message}"
                )

            # =============================
            # DATA
            # =============================

            response_data = poll_data.get(
                "data",
                []
            )

            if not response_data:
                print(
                    "[BatchThumbnailAssetManager] "
                    "No polling data yet"
                )

                continue

            item = response_data[0]

            status = item.get(
                "status"
            )

            print(
                "[BatchThumbnailAssetManager] "
                f"Status: {status}"
            )

            # =============================
            # PROCESSING
            # =============================

            if status == "processing":
                continue

            # =============================
            # SUCCESS
            # =============================

            if status == "success":

                image_url = item.get(
                    "imageURL"
                )

                if not image_url:
                    raise RuntimeError(
                        f"Missing imageURL: "
                        f"{poll_data}"
                    )

                print(
                    "[BatchThumbnailAssetManager] "
                    f"Generated image: "
                    f"{image_url}"
                )

                # =========================
                # DOWNLOAD
                # =========================

                async with aiohttp.ClientSession(
                        timeout=timeout
                ) as session:

                    async with session.get(
                            image_url
                    ) as response:
                        if response.status != 200:
                            raise RuntimeError(
                                f"Failed downloading image: "
                                f"{response.status}"
                            )

                        return await response.read()

            # =============================
            # ERROR
            # =============================

            if status == "error":
                raise RuntimeError(
                    f"Runware task failed: "
                    f"{poll_data}"
                )

        # =================================
        # TIMEOUT
        # =================================

        raise TimeoutError(
            "Runware polling timeout"
        )