from pathlib import Path

from shared.integrations.youtube.bootstrap import (
    youtube_api
)

from shared.runtime.contexts.batch_runtime_context import (
    BatchRuntimeContext
)

from shared.runtime.executors.base.base_task_executor import (
    BaseTaskExecutor
)


def normalize_youtube_tags(tags):
    result = []
    total = 0

    for tag in tags:
        tag = str(tag).strip()

        if not tag:
            continue

        # giới hạn mỗi tag
        if len(tag) > 40:
            tag = tag[:40]

        # YouTube tính thêm dấu phân cách
        next_size = len(tag) + 2

        if total + next_size >= 450:
            break

        result.append(tag)
        total += next_size

    return result


class GenerateBatchYoutubeUploadExecutor(
    BaseTaskExecutor
):
    task_type = (
        "youtube_upload"
    )

    async def execute(
            self,
            task,
            runtime_context: BatchRuntimeContext
    ):

        storage = (
            runtime_context
            .artifact_storage
        )

        payload = (
            task.payload
        )

        # =====================================
        # FILE PATHS
        # =====================================

        final_video_path = (
            payload["video_path"]
        )

        description_path = (
            payload["description_path"]
        )

        thumbnail_path = (
            payload["thumbnail_path"]
        )

        # =====================================
        # VALIDATE FILES
        # =====================================

        if not await storage.exists(
                final_video_path
        ):
            raise FileNotFoundError(
                f"Missing final video: "
                f"{final_video_path}"
            )

        if not await storage.exists(
                description_path
        ):
            raise FileNotFoundError(
                f"Missing youtube description: "
                f"{description_path}"
            )

        if not await storage.exists(
                thumbnail_path
        ):
            raise FileNotFoundError(
                f"Missing thumbnail: "
                f"{thumbnail_path}"
            )

        try:

            # =================================
            # DOWNLOAD FILES
            # =================================

            print(
                "[GenerateBatchYoutubeUploadExecutor] "
                "Downloading artifacts..."
            )

            local_video = await (
                storage.get_local_path(
                    final_video_path,
                    runtime_context.workspace_dir
                )
            )

            local_description = await (
                storage.get_local_path(
                    description_path,
                    runtime_context.workspace_dir
                )
            )

            local_thumbnail = await (
                storage.get_local_path(
                    thumbnail_path,
                    runtime_context.workspace_dir
                )
            )

            # =================================
            # TITLE
            # =================================

            chapter_eps = (
                payload["num_eps"]
            )

            story_title = (
                payload["title"]
            )

            upload_title = (
                f"{story_title} - Tập {chapter_eps}"
            )

            description = Path(
                local_description
            ).read_text(
                encoding="utf-8"
            )

            privacy_status = (
                task.payload.get(
                    "privacy_status",
                    "public"
                )
            )

            publish_at = (
                task.payload.get(
                    "publish_at"
                ), None
            )

            raw_tags = payload.get("tags", [])

            if isinstance(raw_tags, str):
                raw_tags = raw_tags.split(",")

            tags = [
                *raw_tags,
                "truyện audio",
                "truyện full",
                "nghe truyện",
                "audio hay",
            ]

            tags = [
                tag.strip()
                for tag in tags
                if tag.strip()
            ]
            tags = normalize_youtube_tags(tags)
            print(
                "[GenerateBatchYoutubeUploadExecutor] ")
            print(tags)

            video_url = (
                youtube_api
                .upload_video_with_playlist(

                    channel_id=
                    payload["youtube_channel_id"],

                    video_path=
                    str(local_video),

                    title=
                    upload_title,

                    description=
                    description,

                    tags=tags,

                    playlist_name=
                    story_title,

                    playlist_description=
                    payload.get(
                        "description",
                        ""
                    ),

                    thumbnail_path=
                    str(local_thumbnail),

                    publish_time=
                    publish_at
                    if privacy_status == "private"
                    else None,
                )
            )

            if not video_url:
                raise ValueError(
                    "YouTube upload failed"
                )

            video_id = (
                video_url.split(
                    "v="
                )[-1]
            )

            try:

                await storage.delete(
                    runtime_context.batch_output_dir
                )

            except Exception as cleanup_error:

                print(
                    "[Cleanup Failed]",
                    cleanup_error
                )

            return {

                "result": {

                    "success": True,

                    "video_id":
                        video_id,

                    "video_url":
                        video_url,
                },

                "output_path":
                    final_video_path
            }

        except Exception as ex:

            print(
                "[GenerateBatchYoutubeUploadExecutor]",
                str(ex)
            )

            raise
