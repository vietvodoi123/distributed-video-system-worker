def serialize_channel(channel):

    if not channel:
        return None

    return {

        "id":
            str(channel.id),

        "youtube_channel_id":
            channel.youtube_channel_id,

        "mc_name":
            channel.mc_name,

        "mc_path":
            channel.mc_path
    }


def serialize_story(story):

    if not story:
        return None

    return {

        "id":
            str(story.id),

        "original_title":
            story.original_title,

        "ai_title":
            story.ai_title,

        "description":
            story.description,

        "thumbnail_hook":
            story.thumbnail_hook,

        "background_image_url":
            story.background_image_url,

        "genre":
            story.genre,

        "channel":
            serialize_channel(
                story.channel
            )
    }


def serialize_chapter(chapter):

    if not chapter:
        return None

    return {

        "id":
            str(chapter.id),

        "chapter_number":
            chapter.chapter_number,

        "original_title":
            chapter.original_title,

        "translated_title":
            chapter.translated_title,

        "story":
            serialize_story(
                chapter.story
            )
    }


def serialize_batch(batch):

    if not batch:
        return None

    return {

        "id":
            str(batch.id),

        "batch_name":
            batch.batch_name,

        "story":
            serialize_story(
                batch.story
            )
    }


def serialize_task(task):

    return {

        "id":
            str(task.id),

        "task_type":
            task.task_type,

        "task_stage":
            task.task_stage,

        "task_group":
            task.task_group,

        "payload":
            task.payload or {},

        "batch":
            serialize_batch(
                task.batch
            ),

        "chapter":
            serialize_chapter(
                task.chapter
            ),
        "batch_id":
            str(task.batch_id)
            if task.batch_id
            else None,

        "chapter_id":
            str(task.chapter_id)
            if task.chapter_id
            else None,

        "chapter_number":
            task.chapter_number,
    }