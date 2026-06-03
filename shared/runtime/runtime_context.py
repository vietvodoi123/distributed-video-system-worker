from pathlib import Path

from apps.api.models import Task
from shared.runtime.storage.base_artifact_storage import (
    BaseArtifactStorage
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
from apps.api.db.session import (AsyncSessionLocal)

class RuntimeContext:

    def __init__(
        self,
        task: Task,

        worker_id: str,

        workspace_dir: Path,

        artifact_storage:BaseArtifactStorage,

        batch_id: str,

        chapter_id: str,

        chapter_number: int
    ):
        self.db = AsyncSessionLocal()

        self.task = task
        # =====================================
        # WORKER
        # =====================================

        self.worker_id = worker_id

        # =====================================
        # WORKSPACE
        # =====================================

        self.workspace_dir = workspace_dir

        # =====================================
        # STORAGE
        # =====================================

        self.artifact_storage = (
            artifact_storage
        )

        # =====================================
        # IDs
        # =====================================

        self.batch_id = batch_id

        self.chapter_id = chapter_id

        self.chapter_number = (
            chapter_number
        )

        # =====================================
        # CHAPTER ROOT
        # =====================================

        self.chapter_dir = None

        if (
                batch_id is not None
                and chapter_number is not None
        ):
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

        self.timeline_path = (get_timeline_path(self.chapter_dir))

        self.tts_segment_path = (get_tts_segment_dir(self.chapter_dir))

        self.narration_wav_path = (get_narration_wav_path(self.chapter_dir))

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
        self.channel = None
        self.mc_path = None
        self.mc_name = None

    async def initialize(self):

        from sqlalchemy import select

        from apps.api.models.batch import Batch
        from apps.api.models.chapter import Chapter
        from apps.api.models.story import Story

        story = None

        # ================================
        # CHAPTER TASK
        # ================================

        if self.chapter_id:

            chapter = await self.db.scalar(

                select(Chapter)

                .where(
                    Chapter.id == self.chapter_id
                )
            )

            if chapter:
                story = await self.db.scalar(

                    select(Story)

                    .where(
                        Story.id == chapter.story_id
                    )
                )

        # ================================
        # BATCH TASK
        # ================================

        elif self.batch_id:

            batch = await self.db.scalar(

                select(Batch)

                .where(
                    Batch.id == self.batch_id
                )
            )

            if batch:
                story = await self.db.scalar(

                    select(Story)

                    .where(
                        Story.id == batch.story_id
                    )
                )

        if not story:
            raise ValueError(
                "Story not found"
            )

        self.channel = story.channel

        if not self.channel:
            raise ValueError(
                "Story has no channel"
            )

        self.mc_path = (
            self.channel.mc_path
        )

        self.mc_name = (
            self.channel.mc_name
        )
    @property
    def upstream_task(self):
        return getattr(
            self.task,
            "depends_on_task",
            None
        )

    @property
    def upstream_output_path(self):
        upstream = self.upstream_task

        if not upstream:
            return None

        return upstream.output_path

    @property
    def upstream_manifest_path(self):

        upstream = self.upstream_task

        if not upstream:
            return None

        return upstream.manifest_path