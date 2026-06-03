from abc import (
    ABC,
    abstractmethod
)

from pathlib import Path

from shared.runtime.contexts.base_runtime_context import (
    BaseRuntimeContext
)
from typing import Any


class BaseTaskExecutor(ABC):

    task_type: str | None = None

    # ======================================
    # MAIN EXECUTION
    # ======================================

    @abstractmethod
    async def execute(
            self,
            task,
            runtime_context:BaseRuntimeContext,
    ) -> dict | None:
        raise NotImplementedError

    # ======================================
    # OPTIONAL HOOKS
    # ======================================

    async def before_execute(
        self,
        task,
        runtime_context: BaseRuntimeContext
    ):
        pass

    async def after_execute(
        self,
        task,
        runtime_context: BaseRuntimeContext
    ):
        pass

    async def on_failed(
        self,
        task,
        runtime_context: BaseRuntimeContext,
        exception: Exception
    ):
        pass

    # ======================================
    # HELPERS
    # ======================================

    def get_payload(
        self,
        task,
        key,
        default=None
    ):

        return task.payload.get(
            key,
            default
        )

    def require_payload(
        self,
        task,
        key
    ):

        value = task.payload.get(key)

        if value is None:

            raise ValueError(
                f"Missing payload field: {key}"
            )

        return value


    async def get_resource_requirements(
            self,
            task,
            runtime_context
    ) -> dict[str, float]:
        return {}

    def estimate_dynamic_cost(
            self,
            task
    ) -> float:
        requirements = (
            self.get_resource_requirements(
                task
            )
        )

        return sum(
            requirements.values()
        )

    def estimate_duration_seconds(
            self,
            task
    ) -> int:
        return 60