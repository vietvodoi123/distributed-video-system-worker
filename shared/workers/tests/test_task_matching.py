from shared.contracts.capabilities.capabilities import (
    MINI_PC_CAPABILITIES,
    MAIN_PC_CAPABILITIES
)

from shared.runtime.workers.task_matcher import (
    can_execute_task
)

from shared.orchestration.chapter_pipeline import (
    CHAPTER_PIPELINE
)


for task in CHAPTER_PIPELINE:

    print("=" * 50)

    print(
        task["task_type"]
    )

    print(
        "MINI PC:",
        can_execute_task(

            MINI_PC_CAPABILITIES,

            task[
                "required_capabilities"
            ]
        )
    )

    print(
        "MAIN PC:",
        can_execute_task(

            MAIN_PC_CAPABILITIES,

            task[
                "required_capabilities"
            ]
        )
    )