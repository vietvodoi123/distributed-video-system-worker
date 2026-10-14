import json
import subprocess
from pathlib import Path

from shared.config.settings import settings
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
from shared.runtime.artifacts.artifact_paths import (
    get_project_root
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

        channel_name = payload.get("channel_name")
        channel_id = payload.get("channel_id")
        channel_subs = payload.get("channel_subs")
        channel_avatar_url = payload.get("channel_avatar_url")

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
            "channel_name": channel_name,
            "channel_id": channel_id,
            "channel_subs": channel_subs,
            "channel_avatar_url": channel_avatar_url,
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

        final_output = (
            workspace / "final.mp4"
        )

        # =====================================
        # 1. RENDER TEMPLATE FRAMES (PUPPETEER)
        # =====================================

        vr = getattr(settings, "video_render", None)
        num_workers = vr.num_workers if vr else 2
        jpeg_quality = vr.frame_jpeg_quality if vr else 70

        print(
            f"[GenerateVideoExecutor] Step 1/3 - Rendering frames "
            f"(Workers: {num_workers}, Quality: {jpeg_quality})"
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
            "channel_name": channel_name,
            "channel_id": channel_id,
            "channel_subs": channel_subs,
            "channel_avatar_url": channel_avatar_url,
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
                str(rendered_html),
                str(num_workers),
                str(jpeg_quality)
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

        # =====================================
        # 2. PREPARE STATIC ASSETS & AUDIO
        # =====================================

        print(
            "[GenerateVideoExecutor] "
            "Step 2/3 - Preparing layers and narration audio"
        )

        # Text Scroll master video (cached 3600s, stream looped)
        text_scroll_manager = TextScrollAssetManager()
        text_scroll_master = text_scroll_manager.ensure_cache_exists()

        # MC video source (cached source, auto looped & scaled in ffmpeg)
        mc_manager = McLoopAssetManager(
            mc_path=mc_path,
            artifact_storage=storage
        )
        mc_source = await mc_manager.ensure_cache_exists()

        # Narration audio
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

        # =====================================
        # 3. 1-PASS COMPOSITING (ALL-IN-ONE)
        # =====================================

        print(
            "[GenerateVideoExecutor] "
            "Step 3/3 - 1-Pass Direct Rendering to final.mp4"
        )

        composer = VideoLayerComposer()

        composer.compose(
            base_video=str(concat_path),
            overlays=[
                OverlayLayer(
                    path=str(text_scroll_master),
                    x=24,
                    y=590
                ),
                OverlayLayer(
                    path=str(mc_source),
                    x=961,
                    y=256,
                    width=264,
                    height=-1
                )
            ],
            audio_path=str(local_audio),
            output_path=str(final_output),
            use_gpu=runtime_context.gpu_available
        )

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
        # UPLOAD FINAL ARTIFACT
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