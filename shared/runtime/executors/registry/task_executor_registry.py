from shared.runtime.exceptions import (
    ExecutorNotFoundError
)

class TaskExecutorRegistry:

    _executors = {}

    @classmethod
    def register(
        cls,
        task_type: str,
        executor
    ):

        cls._executors[
            task_type
        ] = executor

    @classmethod
    def get_executor(
        cls,
        task_type: str
    ):

        executor = (
            cls._executors.get(
                task_type
            )
        )

        if not executor:

            raise ExecutorNotFoundError(
                f"No executor registered "
                f"for task type: {task_type}"
            )

        return executor