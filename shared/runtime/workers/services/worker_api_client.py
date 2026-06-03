import aiohttp

from shared.config.settings import settings


class WorkerApiClient:

    def __init__(self):

        self.base_url = (
            settings.API_BASE_URL.rstrip("/")
        )

        self.timeout = aiohttp.ClientTimeout(
            total=60
        )

    # =====================================
    # INTERNAL
    # =====================================

    async def _post(
        self,
        endpoint: str,
        payload: dict
    ):

        url = (
            f"{self.base_url}{endpoint}"
        )

        async with aiohttp.ClientSession(
            timeout=self.timeout
        ) as session:

            async with session.post(
                url,
                json=payload
            ) as response:

                response.raise_for_status()

                return await response.json()

    # =====================================
    # CLAIM TASKS
    # =====================================

    async def claim_tasks(
        self,
        *,
        worker_id: str,
        worker_type: str,
        capabilities: list[str],
        available_capacity_cost: float,
        current_reserved_cost: float,
        max_batch_size: int,
        resource_capacity: dict,
    ):

        payload = {

            "worker_id":
                worker_id,

            "worker_type":
                worker_type,

            "capabilities":
                capabilities,

            "available_capacity_cost":
                available_capacity_cost,

            "current_reserved_cost":
                current_reserved_cost,

            "max_batch_size":
                max_batch_size,

            "resource_capacity":
                resource_capacity
        }

        return await self._post(

            "/workers/claim-tasks",

            payload
        )

    # =====================================
    # COMPLETE TASK
    # =====================================

    async def complete_task(
            self,
            *,
            worker_id: str,
            task_id: str,
            execution_result: dict,
    ):
        payload = {

            "worker_id":
                worker_id,

            "task_id":
                str(task_id),

            "result":
                execution_result
        }



        response = await self._post(

            "/workers/complete-task",

            payload
        )

        return response

    # =====================================
    # FAIL TASK
    # =====================================

    async def fail_task(
        self,
        *,
        worker_id: str,
        task_id: str,
        error_message: str
    ):

        payload = {

            "worker_id":
                worker_id,

            "task_id":
                str(task_id),

            "error_message":
                error_message
        }

        return await self._post(

            "/workers/fail-task",

            payload
        )

    # =====================================
    # RENEW LEASES
    # =====================================

    async def renew_leases(
        self,
        *,
        worker_id: str,
        task_ids: list[str],
        lease_seconds: int = 300
    ):

        payload = {

            "worker_id":
                worker_id,

            "task_ids":
                [str(x) for x in task_ids],

            "lease_seconds":
                lease_seconds
        }

        return await self._post(

            "/workers/renew-leases",

            payload
        )

    # =====================================
    # WORKER STATE
    # =====================================

    async def update_worker_state(
        self,
        *,
        worker_id: str,
        active_tasks: int,
        queued_tasks: int,
        metadata: dict | None = None,
    ):

        payload = {

            "worker_id":
                worker_id,

            "active_tasks":
                active_tasks,

            "queued_tasks":
                queued_tasks,

            "metadata":
                metadata or {}
        }

        return await self._post(

            "/workers/worker-state",

            payload
        )