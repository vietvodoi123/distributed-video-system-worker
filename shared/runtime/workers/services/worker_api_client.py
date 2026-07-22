import aiohttp

from shared.config.settings import settings


class WorkerApiClient:

    def __init__(self):

        self.base_url = (
            settings.api.base_url.rstrip("/")
        )

        self.timeout = aiohttp.ClientTimeout(
            total=300
        )


    # =====================================
    # INTERNAL
    # =====================================

    async def _get(
        self,
        endpoint: str
    ):

        url = (
            f"{self.base_url}{endpoint}"
        )

        async with aiohttp.ClientSession(
            timeout=self.timeout
        ) as session:

            async with session.get(
                url
            ) as response:

                response.raise_for_status()

                return await response.json()


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


    async def _patch(
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

            async with session.patch(
                url,
                json=payload
            ) as response:

                response.raise_for_status()

                return await response.json()


    # =====================================
    # CHAPTER DATA
    # =====================================

    async def get_chapter_text(
        self,
        chapter_id: str
    ):

        return await self._get(

            f"/chapters/{chapter_id}/text"
        )


    async def update_chapter_text(
        self,
        *,
        chapter_id: str,
        data: dict
    ):

        return await self._patch(

            f"/chapters/{chapter_id}/text",

            data
        )


    # =====================================
    # CLAIM TASKS
    # =====================================

    async def claim_tasks(
            self,
            *,
            worker_id: str,
            worker_type: str,
            capabilities: list[str],
            available_slots:int
    ):
        payload = {

            "worker_id": worker_id,

            "worker_type": worker_type,

            "capabilities": capabilities,

            "available_slots": available_slots
        }

        return await self._post(
            "/workers/claim-tasks",
            payload,
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


        return await self._post(

            "/workers/complete-task",

            payload
        )


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
    ):
        """
        Renew leases for all running tasks currently owned by this worker.

        The lease duration is determined by the server.
        Workers are only responsible for periodically proving liveness.
        """

        payload = {

            "worker_id": worker_id,

            "task_ids": [
                str(task_id)
                for task_id in task_ids
            ]
        }

        return await self._post(

            "/workers/renew-leases",

            payload,
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