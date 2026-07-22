from shared.integrations.youtube.bootstrap import (
    youtube_api
)

from shared.runtime.executors.base.base_task_executor import (
    BaseTaskExecutor
)

from shared.runtime.artifacts.artifact_paths import (
    get_batch_output_dir
)

from shared.runtime.contexts.batch_runtime_context import (
    BatchRuntimeContext
)


class GenerateBatchYoutubeDescriptionExecutor(
    BaseTaskExecutor
):

    task_type = (
        "generate_batch_youtube_description"
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
        youtube_channel_id=payload["youtube_channel_id"]
        title = payload["title"]
        description=payload["description"]
        timeline=payload["timeline"]

        batch_id = (
            task.batch_id
        )

        # ================================
        # CHANNEL INFO
        # ================================

        channel_info = (
            youtube_api
            .get_channel_by_handle(
                youtube_channel_id
            )
        )

        youtube = (
            youtube_api
            .auth_provider
            .get_authenticated_service(
                youtube_channel_id
            )
        )

        playlist_id = (
            youtube_api
            .get_or_create_playlist(
                youtube=youtube,
                playlist_name=title,
                description=description
            )
        )

        playlist_url = (

            "https://www.youtube.com/"
            f"playlist?list="
            f"{playlist_id}"
        )
        # ================================
        # TIMELINE
        # ================================
        description = (

            f"Tên truyện: "
            f"{title}\n\n"

            f"Mô tả:\n"
            f"{description}\n\n"

            f"Mục lục:\n"
            f"{timeline}\n\n"

            f"Danh sách phát:\n"
            f"{playlist_url}\n\n"

            f"🎙Thông tin kênh:\n"
            f"{channel_info.get('description','')}\n\n"

            f"Đăng ký kênh:\n"
            f"https://www.youtube.com/"
            f"{youtube_channel_id}"
        )

        output_path = (
            f"{get_batch_output_dir(batch_id)}"
            "/metadata/"
            "youtube_description.txt"
        )
        await storage.write_text(
            output_path,
            description
        )


        return {
            "output_path":
                output_path
        }
