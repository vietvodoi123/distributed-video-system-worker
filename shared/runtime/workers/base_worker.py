import asyncio
import time
import uuid
import traceback
from abc import ABC


from shared.runtime.contexts.runtime_context_factory import (
    create_runtime_context
)
from shared.contracts.task_dto import (
    TaskDto
)
from shared.runtime.executors.registry.task_executor_registry import (
    TaskExecutorRegistry
)

from shared.runtime.executors.registry.register_executors import (
    register_executors
)

from shared.runtime.workspace.workspace_manager import (
    WorkspaceManager
)

from shared.runtime.storage.storage_factory import (
    create_storage
)

from shared.runtime.workers.services.worker_resource_profiler import (
    WorkerResourceProfiler
)
from shared.config.settings import settings
from shared.runtime.workers.services.worker_api_client import (
    WorkerApiClient
)


# ==========================================
# BASE WORKER
# ==========================================

class BaseWorker(ABC):

    capabilities: list[str] = []

    poll_interval: int = getattr(settings, "WORKER_POLL_INTERVAL", getattr(settings.worker, "poll_interval", 5))

    max_batch_size: int = 1

    # ======================================
    # INIT
    # ======================================

    def __init__(self, model_path, config_path):

        self.worker_id = (
            getattr(settings, "WORKER_ID", None)
            or str(uuid.uuid4())
        )
        self.resource_capacity = (
            WorkerResourceProfiler.detect()
        )
        self.gpu_available = (
            WorkerResourceProfiler.detect_gpu()
        )
        self.worker_type = (
            getattr(settings, "WORKER_TYPE", None)
            or ("gpu" if self.gpu_available else "cpu")
        )
        print(
            "[BaseWorker] Worker ID:",
            self.worker_id
        )
        print(
            "[BaseWorker] Worker Type:",
            self.worker_type
        )
        print(
            "[BaseWorker] GPU Available:",
            self.gpu_available
        )
        self.api = WorkerApiClient()
        print(
            "[BaseWorker] Resource Capacity:",
            self.resource_capacity.to_dict()
        )

        self.workspace_manager = (
            WorkspaceManager()
        )

        self.artifact_storage = (
            self.create_artifact_storage()
        )

        register_executors(self.gpu_available, model_path, config_path)

        # ==================================
        # CONCURRENCY CONTROL
        # ==================================

        self.running_tasks: set[str] = set()
        self.task_lease_tracker: dict[str, float] = {}
        self.running_tasks_lock = asyncio.Lock()

        self.task_lease_seconds = int(
            getattr(settings.worker, "task_lease_seconds", 300)
            or getattr(settings, "TASK_LEASE_SECONDS", 300)
            or 300
        )

        self.max_slots = getattr(settings.worker, "max_slots", 2)
        self.general_semaphore = (
            asyncio.Semaphore(self.max_slots)
        )

        self.max_audio_slots = getattr(settings.worker, "max_audio_slots", 2)
        self.audio_semaphore = (
            asyncio.Semaphore(self.max_audio_slots)
        )

        self.max_video_slots = getattr(settings.worker, "max_video_slots", 1)
        self.video_semaphore = (
            asyncio.Semaphore(self.max_video_slots)
        )

        self.inflight_tasks: set[asyncio.Task] = set()

    def available_slots(self) -> int:
        return max(
            0,
            self.max_slots - len(self.inflight_tasks)
        )

    @property
    def lease_renew_threshold(self) -> float:
        """
        Tính thời điểm cần gửi gia hạn lease:
        Chỉ gửi khi task gần hết hạn (mặc định ở mốc 80% thời hạn, ví dụ 300s -> 240s,
        dành 60s còn lại để bù trừ mạng hoặc retry).
        """
        buffer_seconds = min(60.0, max(15.0, self.task_lease_seconds * 0.2))
        return max(10.0, self.task_lease_seconds - buffer_seconds)

    # ======================================
    # STORAGE
    # ======================================

    @staticmethod
    def create_artifact_storage():

        storage = create_storage()

        print(
            "[BaseWorker] "
            f"Using storage: "
            f"{type(storage).__name__}"
        )

        return storage

    # ======================================
    # START
    # ======================================

    async def start(self):

        print(
            "[BaseWorker] "
            f"Worker started: "
            f"{self.worker_id}"
        )

        print(
            "[BaseWorker] "
            f"Capabilities: "
            f"{self.capabilities}"
        )

        heartbeat_task = asyncio.create_task(
            self.heartbeat_loop()
        )

        lease_task = asyncio.create_task(
            self.lease_loop()
        )

        try:
            # Send initial registration heartbeat immediately
            await self.send_heartbeat()

            while True:

                try:

                    await self.poll_once()

                except Exception as e:

                    print(
                        "[BaseWorker] "
                        f"Worker loop error: "
                        f"{str(e)}"
                    )

                    await asyncio.sleep(5)

        finally:

            heartbeat_task.cancel()
            lease_task.cancel()

            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass

            try:
                await lease_task
            except asyncio.CancelledError:
                pass

    # ======================================
    # HEARTBEAT LOOP
    # ======================================

    async def send_heartbeat(self):
        try:
            await self.api.heartbeat(
                worker_id=self.worker_id,
                worker_type=self.worker_type,
                capabilities=self.capabilities,
                max_concurrency=self.max_slots,
                free_slots=self.available_slots(),
            )
        except Exception as e:
            print(f"[BaseWorker] Heartbeat send error: {e}")

    async def heartbeat_loop(self):
        while True:
            try:
                await asyncio.sleep(15)
                await self.send_heartbeat()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[BaseWorker] Heartbeat loop error: {e}")
                await asyncio.sleep(5)

    # ======================================
    # POLL
    # ======================================

    async def poll_once(self):

        response = await self.api.claim_tasks(
            worker_id=self.worker_id,
            worker_type=self.worker_type,
            capabilities=self.capabilities,
            available_slots=self.available_slots(),
            resource_capacity=self.resource_capacity.to_dict(),
        )

        tasks = response.get(
            "tasks",
            [],
        )

        if not tasks:
            await asyncio.sleep(
                response.get(
                    "next_poll_in",
                    self.poll_interval,
                )
            )

            return

        for task_data in tasks:
            future = asyncio.create_task(
                self.execute_with_limits(task_data)
            )

            self.inflight_tasks.add(future)

            future.add_done_callback(
                self.inflight_tasks.discard
            )

        print(
            f"[BaseWorker] Claimed {len(tasks)} task(s) "
            f"(InFlight={len(self.inflight_tasks)}, Available={self.available_slots()})"
        )

    # ======================================
    # TASK LIMITS
    # ======================================

    def get_semaphore_for_task(self, task_type):
        from shared.contracts.enums.task_types import AUDIO, VIDEO, MERGE_BATCH_VIDEO
        if task_type == AUDIO:
            return self.audio_semaphore
        if task_type in (VIDEO, MERGE_BATCH_VIDEO):
            return self.video_semaphore
        return self.general_semaphore

    # ======================================
    # EXECUTE WITH LIMITS
    # ======================================

    async def execute_with_limits(
            self,
            task_data: dict
    ):

        task_type = (
            task_data["task_type"]
        )

        semaphore = (
            self.get_semaphore_for_task(
                task_type
            )
        )

        async with semaphore:
            await self.execute_reserved_task(
                task_data
            )

    # ======================================
    # EXECUTE RESERVED TASK
    # ======================================

    @staticmethod
    def _format_task_tag(task: TaskDto | None) -> str:
        if not task:
            return "[unknown]"
        short_id = str(task.id)[:8]
        payload = task.payload or {}
        chap = task.chapter_number if task.chapter_number is not None else payload.get("chapter_number")
        if isinstance(chap, float) and chap.is_integer():
            chap = int(chap)
        if chap is not None:
            return f"[{task.task_type} ch.{chap} {short_id}]"
        return f"[{task.task_type} {short_id}]"

    async def execute_reserved_task(
        self,
        task_data: dict
    ):

        started_at = time.perf_counter()

        workspace_dir = None

        task = None

        runtime_context = None
        tag = "[unknown]"
        try:

            # ==================================
            # HYDRATE ORM TASK
            # ==================================
            if not task_data:
                raise ValueError("Missing task payload")

            task = TaskDto.from_dict(task_data)
            tag = self._format_task_tag(task)
            task_id_str = str(task.id)
            async with self.running_tasks_lock:
                self.running_tasks.add(task_id_str)
                self.task_lease_tracker[task_id_str] = time.time()

            print(f"[BaseWorker] START {tag}")

            # ==================================
            # EXECUTOR
            # ==================================

            executor = (
                TaskExecutorRegistry
                .get_executor(
                    task.task_type
                )
            )

            if not executor:

                raise ValueError(
                    f"No executor registered "
                    f"for task type: "
                    f"{task.task_type}"
                )

            # ==================================
            # WORKSPACE
            # ==================================

            workspace_dir = (
                self.workspace_manager
                .create_workspace(
                    task.id
                )
            )

            # ==================================
            # RUNTIME CONTEXT
            # ==================================

            runtime_context = await create_runtime_context(
                task=task,
                worker_id=self.worker_id,
                workspace_dir=workspace_dir,
                artifact_storage=self.artifact_storage,
                api_client=self.api,
                gpu_available=self.gpu_available,
            )
            # ==================================
            # EXECUTE
            # ==================================

            execution_result = (

                await executor.execute(

                    task,

                    runtime_context
                )
            )

            # ==================================
            # COMPLETE
            # ==================================

            await self.api.complete_task(
                worker_id=self.worker_id,
                task_id=str(task.id),
                attempt_id=task.attempt_id,
                execution_result=execution_result,
            )

            elapsed = time.perf_counter() - started_at
            print(f"[BaseWorker] DONE  {tag} ({elapsed:.1f}s)")

        # ======================================
        # FAILED
        # ======================================

        except Exception as e:

            elapsed = time.perf_counter() - started_at
            print(f"[BaseWorker] FAIL  {tag} ({elapsed:.1f}s): {e}")

            traceback.print_exc()

            if task:
                await self.api.fail_task(
                    worker_id=self.worker_id,
                    task_id=str(task.id),
                    attempt_id=task.attempt_id,
                    error_message=str(e),
                )

        # ======================================
        # CLEANUP
        # ======================================

        finally:

            if task:
                task_id_str = str(task.id)
                async with self.running_tasks_lock:
                    self.running_tasks.discard(task_id_str)
                    self.task_lease_tracker.pop(task_id_str, None)

            try:
                if workspace_dir:
                    self.workspace_manager.cleanup_workspace(workspace_dir)
            except Exception:
                traceback.print_exc()

            try:
                if runtime_context:
                    await runtime_context.close()
            except Exception:
                traceback.print_exc()

    # ======================================
    # LEASE LOOP
    # ======================================

    async def lease_loop(self):
        check_interval = 10  # Kiểm tra định kỳ mỗi 10s trong bộ nhớ (không gọi mạng nếu chưa đến hạn)

        while True:

            try:
                now = time.time()
                tasks_to_renew: list[str] = []

                async with self.running_tasks_lock:
                    for task_id in list(self.running_tasks):
                        last_renew = self.task_lease_tracker.get(task_id, now)
                        if (now - last_renew) >= self.lease_renew_threshold:
                            tasks_to_renew.append(task_id)

                if tasks_to_renew:
                    response = await self.api.renew_leases(
                        worker_id=self.worker_id,
                        task_ids=tasks_to_renew,
                    )

                    now_after_renew = time.time()
                    async with self.running_tasks_lock:
                        for task_id in tasks_to_renew:
                            if task_id in self.running_tasks:
                                self.task_lease_tracker[task_id] = now_after_renew

                    short_ids = ", ".join(t[:8] for t in tasks_to_renew)
                    print(
                        "[BaseWorker] "
                        f"Lease renewed: "
                        f"{response.get('renewed', 0)}/"
                        f"{response.get('requested', len(tasks_to_renew))} "
                        f"[{short_ids}] (lease: {self.task_lease_seconds}s, threshold: {self.lease_renew_threshold:.0f}s)"
                    )

                await asyncio.sleep(check_interval)

            except asyncio.CancelledError:

                break

            except Exception as e:

                print(
                    "[BaseWorker] "
                    f"Lease loop error: "
                    f"{str(e)}"
                )

                await asyncio.sleep(5)
