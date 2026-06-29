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

    free_slots: int = 1

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

        self.running_tasks = set()

        self.current_reserved_cost = 0

        self.max_pending_tasks = 20

        self.task_costs = {}

        self.general_semaphore = (
            asyncio.Semaphore(4)
        )

        self.refine_semaphore = (
            asyncio.Semaphore(1)
        )
        self.crawl_semaphore = asyncio.Semaphore(1)


    # ======================================
    # STORAGE
    # ======================================

    def create_artifact_storage(self):

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

    # ======================================
    # POLL
    # ======================================

    async def poll_once(self):
        # ==================================
        # RESERVE TASKS
        # ==================================
        if (

                len(self.running_tasks)

                >=

                self.max_pending_tasks
        ):
            print(

                "[BaseWorker]",

                "Pending task limit reached:",

                len(self.running_tasks)
            )

            await asyncio.sleep(
                self.poll_interval
            )

            return

        reservation = await self.api.claim_tasks(

            worker_id=self.worker_id,

            worker_type=
            self.__class__.__name__,

            capabilities=
            self.capabilities,

            available_capacity_cost=
            self.get_available_capacity_cost(),

            current_reserved_cost=
            self.current_reserved_cost,

            max_batch_size=
            self.max_pending_tasks,

            resource_capacity=
            self.resource_capacity.to_dict()
        )

        # ==================================
        # NO TASKS
        # ==================================

        if not reservation:

            await asyncio.sleep(
                self.poll_interval
            )

            return

        tasks = reservation["tasks"]
        reserved_cost = (
            reservation.get(
                "used_cost",
                0
            )
        )

        self.current_reserved_cost += (
            reserved_cost
        )

        print(

            "[BaseWorker]",

            f"ReservedCost="
            f"{reserved_cost}",

            f"CurrentCost="
            f"{self.current_reserved_cost}"
        )
        if not tasks:

            await asyncio.sleep(
                self.poll_interval
            )

            return

        print(
            "[BaseWorker] "
            f"Reserved {len(tasks)} tasks"
        )

        # ==================================
        # LOCAL EXECUTION QUEUE
        # ==================================

        for task_data in tasks:

            task_id = task_data["task_id"]

            task_cost = task_data.get(
                "task_cost",
                0
            )

            self.task_costs[
                task_id
            ] = task_cost

            future = asyncio.create_task(

                self.execute_with_limits(
                    task_data
                )
            )

            self.running_tasks.add(
                future
            )

            future.add_done_callback(

                lambda f:

                self.running_tasks.discard(
                    f
                )
            )

        print(

            "[BaseWorker]",

            f"Running={len(self.running_tasks)}"
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

        heartbeat_task = None

        runtime_context = None
        try:

            # ==================================
            # HYDRATE ORM TASK
            # ==================================

            serialized_task = task_data.get(
                "task_data"
            )

            if not serialized_task:
                raise ValueError(
                    f"Missing task_data for task "
                    f"{task_data.get('task_id')}"
                )

            task = TaskDto.from_dict(
                serialized_task
            )

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
            # START HEARTBEAT
            # ==================================

            heartbeat_task = (
                asyncio.create_task(
                    self.heartbeat_loop(
                        task.id
                    )
                )
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

            # ==================================
            # STOP HEARTBEAT
            # ==================================

            if heartbeat_task:

                heartbeat_task.cancel()

                try:

                    await heartbeat_task

                except asyncio.CancelledError:

                    pass

            # ==================================
            # CLEANUP WORKSPACE
            # ==================================

            if workspace_dir:

                self.workspace_manager.cleanup_workspace(
                    workspace_dir
                )

            if task:

                task_cost = (

                    self.task_costs.pop(

                        str(task.id),

                        0
                    )
                )

                self.current_reserved_cost -= (
                    task_cost
                )

                if (
                        self.current_reserved_cost < 0
                ):
                    self.current_reserved_cost = 0

                print(

                    "[BaseWorker]",

                    f"ReleasedCost="
                    f"{task_cost}",

                    f"CurrentCost="
                    f"{self.current_reserved_cost}"
                )

            if runtime_context:
                await runtime_context.close()
    # ======================================
    # HEARTBEAT LOOP
    # ======================================

    async def heartbeat_loop(
        self,
        task_id
    ):

        while True:

            try:
                await self.api.renew_leases(

                    worker_id=
                    self.worker_id,

                    task_ids=[
                        str(task_id)
                    ]
                )
                print(
                    "[BaseWorker] "
                    f"Lease renewed: "
                    f"{task_id}"
                )
                await asyncio.sleep(10)

            except asyncio.CancelledError:

                break

            except Exception as e:

                print(
                    "[BaseWorker] "
                    f"Heartbeat error: "
                    f"{str(e)}"
                )

                await asyncio.sleep(5)

    def get_available_capacity_cost(
            self
    ):

        return max(

            0,

            self.resource_capacity.total_cost()

            - self.current_reserved_cost
        )