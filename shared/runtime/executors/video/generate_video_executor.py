import json
import subprocess
from pathlib import Path

from shared.runtime.executors.base.base_task_executor import (
    BaseTaskExecutor
)

from shared.runtime.contexts.chapter_runtime_context import (
    ChapterRuntimeContext
)

from shared.runtime.static_assets.mc_loop.mc_loop_asset_manager import (
    McLoopAssetManager
)

from shared.runtime.static_assets.text_scroll.text_scroll_asset_manager import (
    TextScrollAssetManager
)

from shared.runtime.executors.video.services.video_layer_composer import (
    VideoLayerComposer,
    OverlayLayer
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

from shared.utils.run_ffmpeg_with_progress import (
    run_ffmpeg_with_progress
)


class GenerateVideoExecutor(
    BaseTaskExecutor
):


    async def execute(
        self,
        task,
        runtime_context: ChapterRuntimeContext
    ):
        payload = task.payload or {}
        storage = runtime_context.artifact_storage
        workspace = runtime_context.workspace_dir

        # =====================================
        # PAYLOAD
        # =====================================

        title = payload.get("title")
        video_type = payload.get("type")
        number_eps = payload.get("number_eps")
        background_url = payload.get("background_url")
        youtube_channel_id = payload.get("youtube_channel_id")

        mc_name = payload.get("mc_name")
        mc_path = payload.get("mc_path")

        segments = payload.get("segments")
        duration = payload.get("duration")
        audio_input = payload.get("audio_input")

        required = {
            "title": title,
            "type": video_type,
            "number_eps": number_eps,
            "background_url": background_url,
            "youtube_channel_id": youtube_channel_id,
            "mc_name": mc_name,
            "mc_path": mc_path,
            "segments": segments,
            "duration": duration,
            "audio_input": audio_input,
        }

        missing = [
            name
            for name, value in required.items()
            if value is None
        ]

        if missing:
            raise ValueError(
                "Missing video task payload fields: "
                + ", ".join(missing)
            )

        # =====================================
        # LOCAL ARTIFACTS
        # =====================================

        rendered_html = (
            workspace / "rendered.html"
        )

        frames_dir = (
            workspace / "frames"
        )

        concat_path = (
            workspace / "concat.txt"
        )

        template_output = (
            workspace / "template.mp4"
        )

        text_scroll_output = (
            workspace / "text_scroll.mp4"
        )

        mc_loop_output = (
            workspace / "mc_loop.mp4"
        )

        composited_output = (
            workspace / "composited.mp4"
        )

        final_output = (
            workspace / "final.mp4"
        )

        # =====================================
        # 1. RENDER TEMPLATE
        # =====================================

        print(
            "[GenerateVideoExecutor] "
            "Step 1/5 - Rendering template"
        )

        channel_info = (
            youtube_api
            .get_channel_by_handle(
                youtube_channel_id
            )
        )

        project_root = get_project_root()

        engine_dir = (
            project_root
            / "runtime"
            / "templates"
            / "reddit_story"
        )

        template_path = (
            engine_dir
            / "html"
            / "template.html"
        )

        renderer_js = (
            engine_dir
            / "js"
            / "renderer.js"
        )

        metadata = {
            "title": title,
            "number_eps": number_eps,
            "type": video_type,
            "background_url": background_url,
            "channel_name": channel_info["name"],
            "channel_id": youtube_channel_id,
            "channel_subs": channel_info["subscribers"],
            "channel_avatar_url": channel_info["avatar_url"],
            "mc_name": mc_name,
        }

        render_template(
            template_path=template_path,
            output_path=rendered_html,
            context=metadata
        )

        process = subprocess.run(
            [
                "node",
                str(renderer_js),
                str(frames_dir),
                str(rendered_html)
            ],
            input=json.dumps(
                segments,
                ensure_ascii=False
            ),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8"
        )

        if process.returncode != 0:
            raise RuntimeError(
                "[GenerateVideoExecutor] "
                "renderer.js failed\n\n"
                f"STDOUT:\n{process.stdout}\n\n"
                f"STDERR:\n{process.stderr}"
            )

        generate_frames_concat_from_segments(
            segments=segments,
            frames_dir=frames_dir,
            output_concat_path=concat_path
        )

        create_video_from_concat(
            concat_file=str(concat_path),
            output_file=str(template_output),
            fps=8
        )

        if not template_output.exists():
            raise FileNotFoundError(
                "Template render failed"
            )

        # =====================================
        # 2. GENERATE TEXT SCROLL
        # =====================================

        print(
            "[GenerateVideoExecutor] "
            "Step 2/5 - Generating text scroll"
        )

        text_scroll_manager = (
            TextScrollAssetManager()
        )

        text_scroll_manager.create_duration_variant(
            duration=duration,
            output_path=text_scroll_output
        )

        if not text_scroll_output.exists():
            raise FileNotFoundError(
                "Failed to generate text scroll video"
            )

        # =====================================
        # 3. GENERATE MC LOOP
        # =====================================

        print(
            "[GenerateVideoExecutor] "
            "Step 3/5 - Generating MC loop"
        )

        mc_manager = (
            McLoopAssetManager(
                mc_path=mc_path,
                artifact_storage=storage
            )
        )

        await mc_manager.create_duration_variant(
            duration=duration,
            output_path=mc_loop_output
        )

        if not mc_loop_output.exists():
            raise FileNotFoundError(
                "Failed to generate MC loop video"
            )

        # =====================================
        # 4. COMPOSE VIDEO LAYERS
        # =====================================

        print(
            "[GenerateVideoExecutor] "
            "Step 4/5 - Composing video layers"
        )

        composer = VideoLayerComposer()

        composer.compose(
            base_video=str(template_output),
            overlays=[
                OverlayLayer(
                    path=str(text_scroll_output),
                    x=24,
                    y=590
                ),
                OverlayLayer(
                    path=str(mc_loop_output),
                    x=961,
                    y=256
                )
            ],
            output_path=str(composited_output),
            use_gpu=False
        )

        if not composited_output.exists():
            raise FileNotFoundError(
                "Compose render failed"
            )

        if composited_output.stat().st_size <= 0:
            raise ValueError(
                "Composited video empty"
            )

        # =====================================
        # 5. MERGE AUDIO
        # =====================================

        print(
            "[GenerateVideoExecutor] "
            "Step 5/5 - Merging narration audio"
        )

        local_audio = Path(
            await storage.get_local_path(
                audio_input,
                workspace
            )
        )

        if not local_audio.exists():
            raise FileNotFoundError(
                f"Missing narration audio: {local_audio}"
            )

        cmd = [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "info",
            "-i",
            str(composited_output),
            "-i",
            str(local_audio),
            "-map",
            "0:v",
            "-map",
            "1:a",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-shortest",
            "-movflags",
            "+faststart",
            str(final_output)
        ]

        run_ffmpeg_with_progress(cmd)

        # =====================================
        # VALIDATE FINAL OUTPUT
        # =====================================

        if not final_output.exists():
            raise FileNotFoundError(
                "Final video not generated"
            )

        if final_output.stat().st_size <= 0:
            raise ValueError(
                "Final video empty"
            )

        # =====================================
        # UPLOAD ONLY FINAL ARTIFACT
        # =====================================

        await storage.write_bytes(
            runtime_context.final_video_path,
            final_output.read_bytes()
        )

        print(
            "[GenerateVideoExecutor] "
            f"Completed: "
            f"{runtime_context.final_video_path}"
        )

        # =====================================
        # RESULT
        # =====================================

        return {
            "output_path": (
                runtime_context.final_video_path
            )
        }