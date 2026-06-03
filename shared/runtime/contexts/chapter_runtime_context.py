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

class ChapterRuntimeContext(
    BaseRuntimeContext
):

    def __init__(
        self,
        task,
        worker_id: str,
        workspace_dir: Path,
        artifact_storage,
        batch_id: str,
        chapter_id: str,
        chapter_number: int,
    ):
        super().__init__(
            task=task,
            worker_id=worker_id,
            workspace_dir=workspace_dir,
            artifact_storage=artifact_storage,
        )

        self.batch_id = batch_id

        self.chapter_id = chapter_id

        self.chapter_number = (
            chapter_number
        )
        self.raw_title = None
        # =====================================
        # CHAPTER ROOT
        # =====================================

        self.chapter_dir = (
            get_chapter_dir(
                batch_id,
                chapter_number
            )
        )
        # =====================================
        # TEXT ARTIFACTS
        # =====================================

        self.raw_text_path = (
            get_raw_text_path(
                batch_id,
                chapter_number
            )
        )

        self.preprocess_text_path = (
            get_preprocess_text_path(
                batch_id,
                chapter_number
            )
        )

        self.translation_text_path = (
            get_translation_text_path(
                batch_id,
                chapter_number
            )
        )

        self.final_script_path = (
            get_final_script_path(
                batch_id,
                chapter_number
            )
        )
        # =====================================
        # AUDIO
        # =====================================

        self.audio_path = (
            get_audio_path(
                batch_id,
                chapter_number
            )
        )

        # =====================================
        # VIDEO
        # =====================================

        self.render_video_path = (
            get_render_video_path(
                batch_id,
                chapter_number
            )
        )

        # =====================================
        # METADATA
        # =====================================

        self.youtube_description_path = (
            get_youtube_description_path(
                batch_id,
                chapter_number
            )
        )

        # =====================================
        # RAW ARTIFACTS
        # =====================================

        self.raw_html_path = (
            get_raw_html_path(
                batch_id,
                chapter_number
            )
        )

        self.raw_metadata_path = (
            get_raw_metadata_path(
                batch_id,
                chapter_number
            )
        )

        self.crawl_manifest_path = (
            get_crawl_manifest_path(
                batch_id,
                chapter_number
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

        chapter = self.task.chapter

        if not chapter:
            raise ValueError(
                "Task has no chapter"
            )

        story = chapter.story

        if not story:
            raise ValueError(
                "Chapter has no story"
            )

        channel = story.channel

        if not channel:
            raise ValueError(
                "Story has no channel"
            )

        self.raw_title = (

                chapter.original_title

                or

                chapter.translated_title

                or

                f"Chapter {chapter.chapter_number}"
        )

        self.channel = channel

        self.mc_path = (
            channel.mc_path
        )

        self.mc_name = (
            channel.mc_name
        )