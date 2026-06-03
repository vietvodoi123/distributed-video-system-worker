from dataclasses import dataclass
from dataclasses import field


@dataclass
class ChannelDto:

    id: str | None = None

    youtube_channel_id: str | None = None

    mc_name: str | None = None

    mc_path: str | None = None

    @classmethod
    def from_dict(cls, data):

        if not data:
            return None

        return cls(**data)


@dataclass
class StoryDto:

    id: str | None = None

    original_title: str | None = None

    ai_title: str | None = None

    description: str | None = None

    thumbnail_hook: str | None = None

    background_image_url: str | None = None

    genre: list[str] | None = None

    channel: ChannelDto | None = None

    @classmethod
    def from_dict(cls, data):

        if not data:
            return None

        return cls(

            id=data.get("id"),

            original_title=data.get(
                "original_title"
            ),

            ai_title=data.get(
                "ai_title"
            ),

            description=data.get(
                "description"
            ),

            thumbnail_hook=data.get(
                "thumbnail_hook"
            ),

            background_image_url=data.get(
                "background_image_url"
            ),

            genre=data.get(
                "genre"
            ),

            channel=ChannelDto.from_dict(
                data.get("channel")
            )
        )


@dataclass
class ChapterDto:

    id: str | None = None

    chapter_number: int | None = None

    translated_title: str | None = None

    story: StoryDto | None = None

    original_title: str | None = None


    @classmethod
    def from_dict(cls, data):

        if not data:
            return None

        return cls(

            id=data.get("id"),

            chapter_number=data.get(
                "chapter_number"
            ),

            translated_title=data.get(
                "translated_title"
            ),

            story=StoryDto.from_dict(
                data.get("story")
            ),
            original_title=data.get(
                "original_title"
            ),
        )


@dataclass
class BatchDto:

    id: str | None = None

    batch_name: str | None = None

    story: StoryDto | None = None

    @classmethod
    def from_dict(cls, data):

        if not data:
            return None

        return cls(

            id=data.get("id"),

            batch_name=data.get(
                "batch_name"
            ),

            story=StoryDto.from_dict(
                data.get("story")
            )
        )


@dataclass
class TaskDto:

    id: str

    task_type: str

    task_stage: str | None = None

    task_group: str | None = None

    batch_id: str | None = None

    chapter_id: str | None = None

    chapter_number: int | None = None

    payload: dict = field(
        default_factory=dict
    )

    batch: BatchDto | None = None

    chapter: ChapterDto | None = None

    @classmethod
    def from_dict(cls, data):

        return cls(

            id=data["id"],

            task_type=data["task_type"],

            task_stage=data.get(
                "task_stage"
            ),

            task_group=data.get(
                "task_group"
            ),

            payload=data.get(
                "payload",
                {}
            ),

            batch=BatchDto.from_dict(
                data.get("batch")
            ),

            chapter=ChapterDto.from_dict(
                data.get("chapter")
            ),
            batch_id=data.get(
                "batch_id"
            ),

            chapter_id=data.get(
                "chapter_id"
            ),

            chapter_number=data.get(
                "chapter_number"
            ),
        )