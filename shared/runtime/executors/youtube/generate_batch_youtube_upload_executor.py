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

        story = task.batch.story

        if not story:
            raise ValueError(
                "Story missing"
            )

        payload = task.payload

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
                task.batch.batch_name
            )

            story_title = (
                story.ai_title
                or story.original_title
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
                )
            )

            tags = [
                story.ai_title
                or story.original_title,
                "truyện audio",
                "audio truyện",
                "truyện tranh",
                "radio truyện"
            ]

            video_url = (
                youtube_api
                .upload_video_with_playlist(

                    channel_id=
                    story.channel.youtube_channel_id,

                    video_path=
                    str(local_video),

                    title=
                    upload_title,

                    description=
                    description,

                    tags=
                    tags,

                    playlist_name=
                    story_title,

                    playlist_description=
                    story.description or "",

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

