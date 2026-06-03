def build_metrics(
    *,
    input_length=0,
    output_length=0,
    input_segments=0,
    output_segments=0,
    input_files=0,
    output_files=0,
    duration_seconds=0,
    video_count=0,
    executor_duration=0,
):
    return {

        "input_length": input_length,

        "output_length": output_length,

        "input_segments": input_segments,

        "output_segments": output_segments,

        "input_files": input_files,

        "output_files": output_files,

        "duration_seconds": duration_seconds,

        "video_count": video_count,

        "executor_duration": executor_duration,
    }