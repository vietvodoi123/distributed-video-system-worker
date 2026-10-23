import aiohttp

from shared.config.settings import settings


class WorkerApiClient:

    def __init__(self):

        self.base_url = (
            getattr(settings, "API_BASE_URL", None)
            or getattr(settings.api, "base_url", "http://192.168.1.147:8000")
        ).rstrip("/")

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
    # HEARTBEAT
    # =====================================

    async def heartbeat(
        self,
        *,
        worker_id: str,
        worker_type: str,
        capabilities: list[str],
        max_concurrency: int,
        free_slots: int,
        ip_address: str | None = None,
        metadata: dict | None = None,
    ):
        """
        Send periodic heartbeat to Server Master to register online status and capacity.
        """
        payload = {
            "worker_id": worker_id,
            "worker_type": worker_type,
            "capabilities": capabilities,
            "max_concurrency": max_concurrency,
            "free_slots": free_slots,
            "metadata": metadata or {},
        }
        if ip_address:
            payload["ip_address"] = ip_address

        return await self._post(
            "/workers/heartbeat",
            payload,
        )

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
            available_slots: int,
            resource_capacity: dict | None = None,
    ):
        payload = {
            "worker_id": worker_id,
            "worker_type": worker_type,
            "capabilities": capabilities,
            "available_slots": available_slots,
            "resource_capacity": resource_capacity or {},
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
