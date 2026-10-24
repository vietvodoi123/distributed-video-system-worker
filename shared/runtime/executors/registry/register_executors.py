from shared.runtime.executors.registry.task_executor_registry import TaskExecutorRegistry
from shared.runtime.executors.crawl.crawl_chapter_executor import CrawlChapterExecutor
from shared.runtime.executors.translation.translate_text_excutor import TranslateTextExecutor
from shared.runtime.executors.audio.audio_executor import AudioExecutor
from shared.runtime.executors.audio.service.tts_service import TTSService
from shared.runtime.executors.video.generate_video_executor import GenerateVideoExecutor
from shared.runtime.executors.video.merge_batch_videos_executor import MergeBatchVideosExecutor
from shared.contracts.enums.task_types import *
from shared.config.settings import settings

def register_executors(gpu_available, model_path, config_path):
    max_concurrency = getattr(settings.tts, "max_concurrency", 3)
    tts_service = TTSService(
        model_path=model_path,
        config_path=config_path,
        use_cuda=gpu_available,
        max_concurrency=max_concurrency,
    )

    # Đăng ký 5 Executor cốt lõi khớp với Server
    TaskExecutorRegistry.register(CRAWL_CHAPTER, CrawlChapterExecutor())
    TaskExecutorRegistry.register(TRANSLATE_TEXT, TranslateTextExecutor())
    TaskExecutorRegistry.register(AUDIO, AudioExecutor(tts_service=tts_service))
    TaskExecutorRegistry.register(VIDEO, GenerateVideoExecutor())
    TaskExecutorRegistry.register(MERGE_BATCH_VIDEO, MergeBatchVideosExecutor())
