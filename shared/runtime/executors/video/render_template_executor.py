import json
import subprocess
import time

from datetime import datetime

from shared.runtime.executors.base.base_task_executor import (
    BaseTaskExecutor
)

from shared.runtime.templates.reddit_story.python.html_template_renderer import (
    render_template
)

from shared.runtime.templates.reddit_story.python.generate_concat_txt import (
    generate_frames_concat_from_segments
)

from shared.runtime.templates.reddit_story.python.render_video import (
    create_video_from_concat
)

from shared.integrations.youtube.bootstrap import (
    youtube_api
)
from shared.runtime.artifacts.artifact_paths import (
    get_project_root
)
from shared.runtime.contexts.chapter_runtime_context import (ChapterRuntimeContext)


class RenderTemplateExecutor(
    BaseTaskExecutor
):

    async def execute(
            self,
            task,
            runtime_context: ChapterRuntimeContext
    ):
        # =================================
        # STORY METADATA
        # =================================

        payload = (
            task.payload
        )

        title = payload['title']
        type = payload['type']

        number_eps = payload['number_eps']
        background_url = payload['background_url']
        youtube_channel_id = payload['youtube_channel_id']

        mc_name = payload['mc_name']
        segments = payload['segments']

        started_at = time.time()

        storage = (
            runtime_context
            .artifact_storage
        )

        # =================================
        # YOUTUBE METADATA
        # =================================

        channel_info = (
            youtube_api
            .get_channel_by_handle(
                youtube_channel_id
            )
        )

        # =================================
        # TEMPLATE ENGINE
        # =================================

        project_root = (
            get_project_root()
        )

        engine_dir = (
                project_root
                / "runtime/templates/"
                  "reddit_story"
        )

        template_path = (
                engine_dir
                / "html/template.html"
        )

        renderer_js = (
                engine_dir
                / "js/renderer.js"
        )

        rendered_html = (
                runtime_context
                .workspace_dir
                / "rendered.html"
        )

        frames_dir = (
                runtime_context
                .workspace_dir
                / "frames"
        )

        concat_path = (
                runtime_context
                .workspace_dir
                / "concat.txt"
        )

        local_output = (
                runtime_context
                .workspace_dir
                / "template.mp4"
        )

        metadata = {

            "title": title,

            "number_eps": number_eps,

            "type": type,

            "background_url": background_url,

            "channel_name":
                channel_info["name"],

            "channel_id":
                youtube_channel_id,

            "channel_subs":
                channel_info[
                    "subscribers"
                ],

            "channel_avatar_url":
                channel_info[
                    "avatar_url"
                ],

            "mc_name": mc_name
        }

        # =================================
        # RENDER HTML
        # =================================

        render_template(

            template_path=
            template_path,

            output_path=
            rendered_html,

            context=
            metadata
        )

        # =================================
        # RENDER FRAMES
        # =================================

        process = subprocess.run(

            [

                "node",

                str(renderer_js),

                str(frames_dir),

                str(rendered_html)
            ],

            input=json.dumps(
                segments,
                ensure_ascii=False,
            ),

            stdout=subprocess.PIPE,

            stderr=subprocess.PIPE,

            text=True,

            encoding="utf-8"
        )

        if process.returncode != 0:
            raise RuntimeError(

                "[RenderTemplateExecutor] "
                "renderer.js failed\n\n"

                f"STDOUT:\n"
                f"{process.stdout}\n\n"

                f"STDERR:\n"
                f"{process.stderr}"
            )

        # =================================
        # CONCAT
        # =================================
        generate_frames_concat_from_segments(
            segments=segments,
            frames_dir=frames_dir,
            output_concat_path=concat_path
        )

        # =================================
        # RENDER VIDEO
        # =================================

        create_video_from_concat(

            concat_file=
            str(concat_path),

            output_file=
            str(local_output),

            fps=8
        )

        # =================================
        # VALIDATE
        # =================================

        if not local_output.exists():
            raise FileNotFoundError(
                "Template render failed"
            )

        # =================================
        # UPLOAD
        # =================================

        await storage.write_bytes(

            runtime_context
            .template_video_path,

            local_output.read_bytes()
        )

        return {
            "output_path":
                runtime_context
                .template_video_path,
        }
