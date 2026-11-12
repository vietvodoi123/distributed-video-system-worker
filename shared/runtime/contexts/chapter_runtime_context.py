from pathlib import Path

from shared.runtime.contexts.base_runtime_context import (
    BaseRuntimeContext
)

from shared.runtime.artifacts.artifact_paths import (
    get_chapter_dir,
    get_raw_text_path,
    get_preprocess_text_path,
    get_translation_text_path,
    get_final_script_path,
    get_audio_path,
    get_render_video_path,
    get_youtube_description_path,
    get_raw_html_path,
    get_raw_metadata_path,
    get_crawl_manifest_path,
    get_timeline_path,
    get_tts_segment_dir,
    get_narration_wav_path,
    get_text_scroll_video_path,
    get_mc_loop_video_path,
    get_template_video_path,
    get_composited_video_path,
    get_final_video_path,
)

def _normalize_chapter_number(value):
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


class ChapterRuntimeContext(
    BaseRuntimeContext
):

    def __init__(
            self,
            task,
            worker_id,
            workspace_dir,
            artifact_storage,
            batch_id=None,
            chapter_id=None,
            chapter_number=None,
            chapter_source_id=None,
            story_id=None,
            api_client=None,
            gpu_available=False,
    ):

        super().__init__(
            task=task,
            worker_id=worker_id,
            workspace_dir=workspace_dir,
            artifact_storage=artifact_storage,
            api_client=api_client,
            gpu_available=gpu_available,
        )

        self.batch_id = batch_id

        self.chapter_id = chapter_id

        self.chapter_source_id = chapter_source_id

        self.story_id = story_id

        self.chapter_number = _normalize_chapter_number(chapter_number)
        self.raw_title = None
        # =====================================
        # CHAPTER ROOT
        # =====================================

        if batch_id is not None and self.chapter_number is not None:
            self.chapter_dir = get_chapter_dir(batch_id, self.chapter_number)
        elif story_id is not None:
            chap_key = self.chapter_number if self.chapter_number is not None else (chapter_source_id or chapter_id or task.id)
            self.chapter_dir = f"stories/{story_id}/chapters/{chap_key}"
        else:
            chap_key = self.chapter_number if self.chapter_number is not None else (chapter_source_id or chapter_id or task.id)
            self.chapter_dir = f"chapters/{chap_key}"

        scope_batch_id = batch_id if batch_id is not None else (story_id or "unbatched")
        scope_chapter_number = self.chapter_number if self.chapter_number is not None else (chapter_source_id or chapter_id or task.id)
        # =====================================
        # TEXT ARTIFACTS
        # =====================================

        self.raw_text_path = (
            get_raw_text_path(
                scope_batch_id,
                scope_chapter_number
            )
        )

        self.preprocess_text_path = (
            get_preprocess_text_path(
                scope_batch_id,
                scope_chapter_number
            )
        )

        self.translation_text_path = (
            get_translation_text_path(
                scope_batch_id,
                scope_chapter_number
            )
        )

        self.final_script_path = (
            get_final_script_path(
                scope_batch_id,
                scope_chapter_number
            )
        )
        # =====================================
        # AUDIO
        # =====================================

        self.audio_path = (
            get_audio_path(
                scope_batch_id,
                scope_chapter_number
            )
        )

        # =====================================
        # VIDEO
        # =====================================

        self.render_video_path = (
            get_render_video_path(
                scope_batch_id,
                scope_chapter_number
            )
        )

        # =====================================
        # METADATA
        # =====================================

        self.youtube_description_path = (
            get_youtube_description_path(
                scope_batch_id,
                scope_chapter_number
            )
        )

        # =====================================
        # RAW ARTIFACTS
        # =====================================

        self.raw_html_path = (
            get_raw_html_path(
                scope_batch_id,
                scope_chapter_number
            )
        )

        self.raw_metadata_path = (
            get_raw_metadata_path(
                scope_batch_id,
                scope_chapter_number
            )
        )

        self.crawl_manifest_path = (
            get_crawl_manifest_path(
                scope_batch_id,
                scope_chapter_number
            )
        )

        # =====================================
        # TTS
        # =====================================

        self.timeline_path = (
            get_timeline_path(
                self.chapter_dir
            )
        )

        self.tts_segment_path = (
            get_tts_segment_dir(
                self.chapter_dir
            )
        )

        self.narration_wav_path = (
            get_narration_wav_path(
                self.chapter_dir
            )
        )

        # =====================================
        # VIDEO LAYERS
        # =====================================

        self.text_scroll_video_path = (
            get_text_scroll_video_path(
                self.chapter_dir
            )
        )

        self.mc_loop_video_path = (
            get_mc_loop_video_path(
                self.chapter_dir
            )
        )

        self.template_video_path = (
            get_template_video_path(
                self.chapter_dir
            )
        )

        self.composited_video_path = (
            get_composited_video_path(
                self.chapter_dir
            )
        )

        self.final_video_path = (
            get_final_video_path(
                self.chapter_dir
            )
        )

    async def initialize(self):

        payload = (
                self.task.payload
                or {}
        )

        channel = (
            payload.get(
                "channel"
            )
        )

        if channel:

            self.channel = channel

            self.mc_path = (
                channel.get(
                    "mc_path"
                )
            )

            self.mc_name = (
                channel.get(
                    "mc_name"
                )
            )

        else:

            self.channel = None

            self.mc_path = None

            self.mc_name = None

        self.raw_title = (
            f"Chapter {self.chapter_number}"
        )