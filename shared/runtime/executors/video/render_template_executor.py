import json
import subprocess
import time

from datetime import datetime
from pathlib import Path

from shared.runtime.executors.base.base_task_executor import (
    BaseTaskExecutor
)

from shared.runtime.templates.reddit_story.python.html_template_renderer import (
    render_template
)

from shared.runtime.templates.reddit_story.python.generate_concat_txt import (
    generate_frames_concat_from_timeline
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
        runtime_context:ChapterRuntimeContext
    ):
        # =================================
        # STORY METADATA
        # =================================

        payload = (
            task.payload
        )

        story = (
            payload["story"]
        )

        channel = (
            payload["channel"]
        )

        started_at = time.time()

        storage = (
            runtime_context
            .artifact_storage
        )

        # =================================
        # LOAD TIMELINE
        # =================================

        timeline_artifact_path = task.payload.get(
            "timeline_path"
        )

        if not timeline_artifact_path:
            raise ValueError(
                "Missing timeline_path"
            )

        local_timeline = await (
            storage.get_local_path(
                timeline_artifact_path,
                runtime_context.workspace_dir
            )
        )

        timeline_file = Path(
            local_timeline
        )

        timeline_data = json.loads(

            timeline_file.read_text(
                encoding="utf-8"
            )
        )

        segments = (
            timeline_data.get(
                "segments",
                []
            )
        )

        if not segments:

            raise ValueError(
                "Timeline empty"
            )

        # =================================
        # YOUTUBE METADATA
        # =================================

        channel_info = (
            youtube_api
            .get_channel_by_handle(
                channel[
                    "youtube_channel_id"
                ]
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

            "title":
                story["title"],

            "number_eps":
                payload[
                    "episode_number"
                ],

            "type":
                story.get(
                    "genre",
                    ""
                ),

            "background_url":
                story.get(
                    "background_image_url",
                    ""
                ),

            "channel_name":
                channel_info["name"],

            "channel_id":
                channel[
                    "youtube_channel_id"
                ],

            "channel_subs":
                channel_info[
                    "subscribers"
                ],

            "channel_avatar_url":
                channel_info[
                    "avatar_url"
                ],

            "mc_name":
                channel[
                    "mc_name"
                ]
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

                str(timeline_file),

                str(frames_dir),

                str(rendered_html)
            ],

            stdout=subprocess.PIPE,

            stderr=subprocess.PIPE,

            text=True
        )

        print("=" * 80)
        print("[renderer stdout]")
        print(process.stdout)

        print("=" * 80)
        print("[renderer stderr]")
        print(process.stderr)

        print("=" * 80)
        print("[return code]")
        print(process.returncode)

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
        generate_frames_concat_from_timeline(

            timeline_path=
            timeline_file,

            frames_dir=
            frames_dir,

            output_concat_path=
            concat_path
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

        # =================================
        # MANIFEST
        # =================================

        manifest = {

            "success": True,

            "executor":
            self.__class__.__name__,

            "generated_at":
            datetime.utcnow().isoformat(),

            "timeline_path":
            timeline_artifact_path,

            "output_path":
            runtime_context.template_video_path,

            "segments":
            len(segments),

            "duration_seconds":
            round(
                time.time()
                - started_at,
                2
            )
        }

        manifest_path = (
            f"{runtime_context.chapter_dir}"
            f"/video/metadata/"
            f"template_manifest.json"
        )

        await storage.write_json(
            manifest_path,
            manifest
        )

        print(
            "[RenderTemplateExecutor] "
            "Completed"
        )

        return {

            "output_path":
            runtime_context
            .template_video_path,

            "manifest_path":
            manifest_path,

            "result":
                {"manifest":manifest,
                 "metrics": {

                     "segment_count":
                         len(segments),

                     "executor_duration":
                         round(
                             time.time() - started_at,
                             2
                         )
                 }
                 }
        }

    def get_resource_requirements(
            self,
            task,runtime_context
    ):

        segment_count = (
            task.payload.get(
                "segment_count",
                100
            )
        )

        factor = max(
            1,
            segment_count / 100
        )

        return {

            "cpu": min(
                20,
                6 * factor
            ),

            "ram": min(
                24,
                8 * factor
            ),

            "gpu": 0,

            "network": 1,

            "disk_io": min(
                30,
                10 * factor
            )
        }