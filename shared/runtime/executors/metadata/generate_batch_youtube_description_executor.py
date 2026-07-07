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

from shared.runtime.contexts.batch_runtime_context import (
    BatchRuntimeContext
)

from shared.utils.chapter_title_cleaner import (
    clean_chapter_title
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


        story = (
            payload["story"]
        )


        channel = (
            payload["channel"]
        )


        chapters = (
            payload.get(
                "chapters",
                []
            )
        )


        batch_id = (
            task.batch_id
        )


        translator = (
            DichNhanhTranslateService()
        )


        # ================================
        # CHANNEL INFO
        # ================================

        channel_info = (

            youtube_api
            .get_channel_by_handle(

                channel[
                    "youtube_channel_id"
                ]
            )
        )


        youtube = (

            youtube_api
            .auth_provider
            .get_authenticated_service(

                channel[
                    "youtube_channel_id"
                ]
            )
        )


        playlist_id = (

            youtube_api
            .get_or_create_playlist(

                youtube=youtube,

                playlist_name=
                    story["title"],

                description=
                    story.get(
                        "description"
                    )
                    or ""
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

        timeline_lines = []

        current_seconds = 0


        for chapter in chapters:

            title = chapter.get(
                "title",
                ""
            )


            try:

                title = await (
                    translator
                    .translate(
                        title
                    )
                )

            except Exception:
                pass


            title = clean_chapter_title(

                title=title,

                chapter_number=
                    chapter[
                        "chapter_number"
                    ]
            )


            timestamp = (

                f"{current_seconds // 3600:02d}:"
                f"{(current_seconds % 3600)//60:02d}:"
                f"{current_seconds % 60:02d}"
            )


            timeline_lines.append(

                f"{timestamp} "
                f"Chương "
                f"{chapter['chapter_number']} "
                f"- {title}"
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


        description = (

            f"Tên truyện: "
            f"{story['title']}\n\n"

            f"Mô tả:\n"
            f"{story.get('description','')}\n\n"

            f"Mục lục:\n"
            f"{chapters_text}\n\n"

            f"Danh sách phát:\n"
            f"{playlist_url}\n\n"

            f"🎙Thông tin kênh:\n"
            f"{channel_info.get('description','')}\n\n"

            f"Đăng ký kênh:\n"
            f"https://www.youtube.com/"
            f"{channel['youtube_channel_id']}"
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

            "result": {

                "story_title":
                    story["title"],

                "chapter_count":
                    len(chapters)
            },

            "output_path":
                output_path
        }


    def get_resource_requirements(
            self,
            task,
            runtime_context
    ):

        return {

            "cpu": 1,
            "ram": 1,
            "gpu": 0,
            "network": 2,
            "disk_io": 1
        }