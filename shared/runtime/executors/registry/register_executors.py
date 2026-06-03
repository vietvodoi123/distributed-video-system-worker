from shared.runtime.executors.registry.task_executor_registry import (
    TaskExecutorRegistry
)

from shared.runtime.executors.crawl.crawl_chapter_executor import (
    CrawlChapterExecutor
)

from shared.runtime.executors.text.preprocess_text_executor import (
    PreprocessTextExecutor
)
from shared.runtime.executors.translation.translate_text_excutor import (
    TranslateTextExecutor
)
from shared.runtime.executors.refine.refine_text_executor import (
    RefineTextExecutor
)
from shared.runtime.executors.audio.generate_tts_segments_executor import (
    GenerateTtsSegmentsExecutor
)

from shared.runtime.executors.audio.merge_tts_segments_executor import (
    MergeTtsSegmentsExecutor
)

from shared.runtime.executors.video.generate_text_scroll_executor import (
    GenerateTextScrollExecutor
)
from shared.runtime.executors.video.generate_mc_loop_executor import (
    GenerateMcLoopExecutor
)
from shared.runtime.executors.video.render_template_executor import (
    RenderTemplateExecutor
)
from shared.runtime.executors.video.compose_video_layers_executor import (
    ComposeVideoLayersExecutor
)
from shared.runtime.executors.video.merge_audio_into_video_executor import (
    MergeAudioIntoVideoExecutor
)
from shared.runtime.executors.metadata.generate_batch_youtube_description_executor import (
    GenerateBatchYoutubeDescriptionExecutor
)
from shared.runtime.executors.video.merge_batch_videos_executor import (
    MergeBatchVideosExecutor
)
from shared.runtime.executors.video.generate_batch_thumbnail_executor import (
    GenerateBatchThumbnailExecutor
)
from shared.runtime.executors.youtube.generate_batch_youtube_upload_executor import (
    GenerateBatchYoutubeUploadExecutor
)
from shared.contracts.enums.task_types import (
    CRAWL_CHAPTER,
    PREPROCESS_TEXT,
    TRANSLATE_TEXT,
    REFINE_TEXT,
    GENERATE_TTS_SEGMENTS,
    MERGE_TTS_SEGMENTS,
    TEXT_SCROLL_LOOP,
    MC_LOOP,RENDER_TEMPLATE,
    COMPOSE_VIDEO_LAYERS,
    MERGE_AUDIO_INTO_VIDEO,
    GENERATE_YOUTUBE_DESCRIPTION,
    MERGE_BATCH_VIDEO,
    GENERATE_BATCH_THUMBNAIL,
    GENERATE_BATCH_YOUTUBE_UPLOAD
)
def register_executors():

    TaskExecutorRegistry.register(
        CRAWL_CHAPTER,
        CrawlChapterExecutor()
    )
    TaskExecutorRegistry.register(
        PREPROCESS_TEXT,
        PreprocessTextExecutor()
    )
    TaskExecutorRegistry.register(
        TRANSLATE_TEXT,
        TranslateTextExecutor()
    )
    TaskExecutorRegistry.register(
        REFINE_TEXT,
        RefineTextExecutor()
    )
    TaskExecutorRegistry.register(
        GENERATE_TTS_SEGMENTS,
        GenerateTtsSegmentsExecutor()
    )
    TaskExecutorRegistry.register(
        MERGE_TTS_SEGMENTS,
        MergeTtsSegmentsExecutor()
    )
    TaskExecutorRegistry.register(
        TEXT_SCROLL_LOOP,
        GenerateTextScrollExecutor()
    )
    TaskExecutorRegistry.register(
        MC_LOOP,
        GenerateMcLoopExecutor()
    )
    TaskExecutorRegistry.register(
        RENDER_TEMPLATE,
        RenderTemplateExecutor()
    )
    TaskExecutorRegistry.register(
        COMPOSE_VIDEO_LAYERS,
        ComposeVideoLayersExecutor()
    )
    TaskExecutorRegistry.register(
        MERGE_AUDIO_INTO_VIDEO,
        MergeAudioIntoVideoExecutor()
    )
    TaskExecutorRegistry.register(
        GENERATE_YOUTUBE_DESCRIPTION,
        GenerateBatchYoutubeDescriptionExecutor()
    )
    TaskExecutorRegistry.register(
        MERGE_BATCH_VIDEO,
        MergeBatchVideosExecutor()
    )
    TaskExecutorRegistry.register(
        GENERATE_BATCH_THUMBNAIL,
        GenerateBatchThumbnailExecutor()
    )
    TaskExecutorRegistry.register(
        GENERATE_BATCH_YOUTUBE_UPLOAD,
        GenerateBatchYoutubeUploadExecutor()
    )
