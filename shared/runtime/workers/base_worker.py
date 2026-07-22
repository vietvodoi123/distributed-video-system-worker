import asyncio
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

    poll_interval: int = settings.worker.poll_interval

    max_batch_size: int = 1


    # ======================================
    # INIT
    # ======================================

    def __init__(self):

        self.worker_id = str(
            uuid.uuid4()
        )
        self.resource_capacity = (
            WorkerResourceProfiler
            .detect()
        )
        self.api = WorkerApiClient()
        print(

            "[BaseWorker] Resource Capacity:",

            self.resource_capacity.to_dict()
        )

        print(

            "[BaseWorker] Max Cost:",

            self.resource_capacity.total_cost()
        )

        self.workspace_manager = (
            WorkspaceManager()
        )

        self.artifact_storage = (
            self.create_artifact_storage()
        )

        register_executors()

        # ==================================
        # CONCURRENCY CONTROL
        # ==================================

        self.running_tasks: set[str] = set()
        self.running_tasks_lock = asyncio.Lock()

        self.general_semaphore = (
            asyncio.Semaphore(2)
        )

        self.refine_semaphore = (
            asyncio.Semaphore(1)
        )
        self.crawl_semaphore = asyncio.Semaphore(1)

        self.inflight_tasks: set[asyncio.Task] = set()
        self.max_slots = 10

    def available_slots(self) -> int:
        return max(
            0,
            self.max_slots - len(self.inflight_tasks)
        )
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

        lease_task = asyncio.create_task(
            self.lease_loop()
        )

        try:

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

            lease_task.cancel()

            try:
                await lease_task

            except asyncio.CancelledError:
                pass

    # ======================================
    # POLL
    # ======================================

    async def poll_once(self):

        response = await self.api.claim_tasks(
            worker_id=self.worker_id,
            worker_type=self.__class__.__name__,
            capabilities=self.capabilities,
            available_slots=self.available_slots(),
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

        print(

            "[BaseWorker]",

            f"Claimed {len(tasks)} tasks",
        )

        for task_data in tasks:
            future = asyncio.create_task(
                self.execute_with_limits(task_data)
            )

            self.inflight_tasks.add(future)

            future.add_done_callback(
                self.inflight_tasks.discard
            )

        print(
            "[BaseWorker]",
            f"InFlight={len(self.inflight_tasks)} "
            f"Available={self.available_slots()}"
        )

    # ======================================
    # TASK LIMITS
    # ======================================

    def get_semaphore_for_task(
            self,
            task_type
    ):
        if task_type == "crawl_chapter":
            return self.crawl_semaphore

        if task_type == "refine_text":
            return self.refine_semaphore

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

    async def execute_reserved_task(
        self,
        task_data: dict
    ):

        workspace_dir = None

        task = None

        runtime_context = None
        try:

            # ==================================
            # HYDRATE ORM TASK
            # ==================================
            if not task_data:
                raise ValueError("Missing task payload")

            task = TaskDto.from_dict(task_data)
            async with self.running_tasks_lock:
                self.running_tasks.add(str(task.id))

            print(
                "[BaseWorker] "
                f"Claimed task: "
                f"{task.id}"
            )

            print(
                "[BaseWorker] "
                f"Task type: "
                f"{task.task_type}"
            )

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

            runtime_context = (
                await create_runtime_context(

                    task=task,

                    worker_id=self.worker_id,

                    workspace_dir=workspace_dir,

                    artifact_storage=self.artifact_storage,

                    api_client=self.api
                )
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

                worker_id=
                self.worker_id,

                task_id=
                str(task.id),

                execution_result=
                execution_result
            )

            print(
                "[BaseWorker] "
                f"Task completed: "
                f"{task.id}"
            )

        # ======================================
        # FAILED
        # ======================================

        except Exception as e:

            print(

                "[BaseWorker] "

                f"Task failed: "

                f"{task.id if task else 'unknown'}"

            )

            traceback.print_exc()

            if task:
                await self.api.fail_task(

                    worker_id=
                    self.worker_id,

                    task_id=
                    str(task.id),

                    error_message=
                    str(e)
                )

        # ======================================
        # CLEANUP
        # ======================================

        finally:

            if task:
                async with self.running_tasks_lock:
                    self.running_tasks.discard(str(task.id))

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

        while True:

            try:

                async with self.running_tasks_lock:
                    task_ids = list(self.running_tasks)

                if task_ids:
                    response = await self.api.renew_leases(

                        worker_id=self.worker_id,

                        task_ids=task_ids,
                    )

                    print(
                        "[BaseWorker] "
                        f"Lease renewed: "
                        f"{response.get('renewed', 0)}/"
                        f"{response.get('requested', len(task_ids))}"
                    )

                await asyncio.sleep(30)

            except asyncio.CancelledError:

                break

            except Exception as e:

                print(
                    "[BaseWorker] "
                    f"Lease loop error: "
                    f"{str(e)}"
                )

                await asyncio.sleep(5)

