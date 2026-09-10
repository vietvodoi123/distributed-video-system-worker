from pathlib import Path
import re
import time

from shared.runtime.executors.base.base_task_executor import (
    BaseTaskExecutor
)

from shared.utils.run_ffmpeg_with_progress import (
    run_ffmpeg_with_progress
)

from shared.runtime.contexts.batch_runtime_context import (
    BatchRuntimeContext
)


class MergeBatchVideosExecutor(
    BaseTaskExecutor
):
    CAPABILITIES = [
        "ffmpeg"
    ]

    @staticmethod
    def _get_chapter_number(video_path: str) -> int:
        """
        Extract the chapter number from paths such as:

        batches/<batch_id>/chapters/551/video/final/final.mp4
        """
        normalized = str(video_path).replace("\\", "/")

        match = re.search(
            r"/chapters/(\d+)(?:/|$)",
            normalized,
            re.IGNORECASE,
        )

        if not match:
            raise ValueError(
                "Cannot determine chapter number from video path: "
                f"{video_path}"
            )

        return int(match.group(1))

    @classmethod
    def _sort_video_paths(cls, video_paths):
        """
        Never trust the order in payload["video_paths"].

        Workers can finish in any order, so the merge executor must
        establish the order itself immediately before concatenation.
        """
        numbered = []

        for original_index, video_path in enumerate(video_paths):
            chapter_number = cls._get_chapter_number(video_path)

            numbered.append(
                (
                    chapter_number,
                    original_index,
                    video_path,
                )
            )

        numbered.sort(key=lambda item: (item[0], item[1]))

        # Detect duplicate chapters. A duplicate here is almost always
        # a task/payload construction problem and should not silently
        # produce a duplicated chapter in the final video.
        seen = set()

        for chapter_number, _, video_path in numbered:
            if chapter_number in seen:
                raise ValueError(
                    "Duplicate chapter detected while merging: "
                    f"chapter {chapter_number}, path={video_path}"
                )
            seen.add(chapter_number)

        return [
            video_path
            for _, _, video_path in numbered
        ]

    async def execute(
        self,
        task,
        runtime_context: BatchRuntimeContext,
    ):
        started_at = time.time()

        storage = runtime_context.artifact_storage
        payload = task.payload or {}

        # =====================================
        # LOAD CHAPTER VIDEOS
        # =====================================

        video_paths = payload.get("video_paths")

        if not video_paths:
            raise ValueError(
                "No chapter videos found"
            )

        if not isinstance(video_paths, list):
            raise ValueError(
                "video_paths must be a list"
            )

        # =====================================
        # DETERMINISTIC CHAPTER ORDER
        # =====================================

        sorted_video_paths = self._sort_video_paths(
            video_paths
        )

        print(
            "[MergeBatchVideosExecutor] "
            "Merge order:"
        )

        for index, video_path in enumerate(
            sorted_video_paths,
            start=1,
        ):
            chapter_number = self._get_chapter_number(
                video_path
            )

            print(
                f"  {index:03d}. "
                f"Chapter {chapter_number} -> "
                f"{video_path}"
            )

        # =====================================
        # MATERIALIZE LOCAL FILES
        # =====================================

        local_video_paths = []

        for remote_video_path in sorted_video_paths:
            print(
                "[MergeBatchVideosExecutor] "
                f"Materializing: "
                f"{remote_video_path}"
            )

            local_path = Path(
                await storage.get_local_path(
                    remote_video_path,
                    runtime_context.workspace_dir,
                )
            )

            if not local_path.exists():
                raise FileNotFoundError(
                    f"Missing local video: {local_path}"
                )

            if local_path.stat().st_size <= 0:
                raise ValueError(
                    f"Video file is empty: {local_path}"
                )

            local_video_paths.append(local_path)

        # =====================================
        # CONCAT FILE
        # =====================================

        concat_file = (
            runtime_context.workspace_dir
            / "concat.txt"
        )

        concat_lines = []

        for video_path in local_video_paths:
            safe_path = (
                str(video_path.resolve())
                .replace("\\", "/")
                .replace("'", r"'\''")
            )

            concat_lines.append(
                f"file '{safe_path}'"
            )

        concat_file.write_text(
            "\n".join(concat_lines) + "\n",
            encoding="utf-8",
        )

        print(
            "[MergeBatchVideosExecutor] "
            f"Concat file created: {concat_file}"
        )

        # =====================================
        # OUTPUT
        # =====================================

        local_output = (
            runtime_context.workspace_dir
            / "merged_batch.mp4"
        )

        remote_output = (
            runtime_context.final_video_path
        )

        # =====================================
        # FFMPEG
        # =====================================

        cmd = [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "info",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_file),
            "-c",
            "copy",
            "-movflags",
            "+faststart",
            str(local_output),
        ]

        print(
            "[MergeBatchVideosExecutor] "
            "Starting FFmpeg merge..."
        )

        run_ffmpeg_with_progress(cmd)

        # =====================================
        # VALIDATE OUTPUT
        # =====================================

        if not local_output.exists():
            raise FileNotFoundError(
                "Merged batch video not generated"
            )

        if local_output.stat().st_size <= 0:
            raise ValueError(
                "Merged batch video empty"
            )

        # =====================================
        # UPLOAD
        # =====================================

        await storage.write_bytes(
            remote_output,
            local_output.read_bytes(),
        )

        print(
            "[MergeBatchVideosExecutor] "
            f"Uploaded merged video: {remote_output}"
        )

        elapsed = time.time() - started_at

        print(
            "[MergeBatchVideosExecutor] "
            f"Completed in {elapsed:.2f}s"
        )

        return {
            "output_path": remote_output,
        }
