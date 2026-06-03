from shared.integrations.youtube.bootstrap import (
    youtube_api
)
from shared.runtime.executors.translation.services.dichnhanh_translate_service import (
    DichNhanhTranslateService
)
from shared.runtime.executors.base.base_task_executor import (
    BaseTaskExecutor
)

from shared.runtime.artifacts.artifact_paths import (
    get_batch_output_dir
)

from shared.runtime.contexts.batch_runtime_context import (BatchRuntimeContext)

class GenerateBatchYoutubeDescriptionExecutor(
    BaseTaskExecutor
):

    task_type = (
        "generate_batch_youtube_description"
    )

    async def execute(
        self,
        task,
        runtime_context:BatchRuntimeContext
    ):

        storage = (
            runtime_context
            .artifact_storage
        )

        if not task.batch:
            raise ValueError(
                "Task batch missing"
            )
        story = task.batch.story

        batch_id = str(
            task.batch_id
        )

        if not story:
            raise ValueError(
                "Story missing"
            )

        chapters = (
            task.payload.get(
                "chapters",
                []
            )
        )

        translator = (
            DichNhanhTranslateService()
        )


        # =====================================
        # CHANNEL
        # =====================================

        channel = story.channel

        if not channel:

            raise ValueError(
                "Story has no channel"
            )

        channel_info = (
            youtube_api
            .get_channel_by_handle(
                story.channel.youtube_channel_id
            )
        )

        # =====================================
        # PLAYLIST
        # =====================================

        youtube = (
            youtube_api
            .auth_provider
            .get_authenticated_service(
                story.channel.youtube_channel_id
            )
        )

        playlist_id = (
            youtube_api
            .get_or_create_playlist(

                youtube=
                youtube,

                playlist_name=
                story.ai_title
                or story.original_title,

                description=
                story.description or ""
            )
        )

        playlist_url = (
            "https://www.youtube.com/"
            f"playlist?list="
            f"{playlist_id}"
        )

        timeline_lines = []

        current_seconds = 0

        for chapter in chapters:

            chapter_title_cn = (
                chapter.get(
                    "title",
                    ""
                )
            )

            try:

                chapter_title_vi = (
                    await translator.translate(
                        chapter_title_cn
                    )
                )

            except Exception:

                chapter_title_vi = (
                    chapter_title_cn
                )

            timestamp = (

                f"{current_seconds // 3600:02d}:"
                f"{(current_seconds % 3600) // 60:02d}:"
                f"{current_seconds % 60:02d}"
            )

            timeline_lines.append(

                f"{timestamp} "

                f"Chương "

                f"{chapter['chapter_number']} - "

                f"{chapter_title_vi}"
            )

            current_seconds += int(
                chapter.get(
                    "duration_seconds",
                    0
                )
            )

        chapters_text = "\n".join(
            timeline_lines
        )

        # =====================================
        # DESCRIPTION
        # =====================================

        description = (
            f"Tên truyện: "
            f"{story.ai_title or story.original_title}\n\n"
            f"Mô tả: "
            f"{story.description}\n\n"
            f"Mục lục:\n"
            f"{chapters_text}\n\n"
            f"Danh sách phát:\n"
            f"{playlist_url}\n\n"
            f"🎙Thông tin kênh:\n"
            f"{channel_info.get('description', '')}\n\n"
            f"Đăng ký kênh:\n"
            f"https://www.youtube.com/channel/"
            f"{channel.youtube_channel_id}"
        )

        # =====================================
        # OUTPUT
        # =====================================

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

            "result": {

                "story_title":
                story.ai_title,

                "chapter_count":
                len(chapters),

                "output_path":
                output_path
            },

            "output_path":
            output_path
        }

    def get_resource_requirements(
            self,
            task,runtime_context
    ):

        return {

            "cpu": 1,

            "ram": 1,

            "gpu": 0,

            "network": 2,

            "disk_io": 1
        }