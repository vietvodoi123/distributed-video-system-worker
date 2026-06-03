import asyncio

from shared.orchestration.scheduling.resource_estimator import (
    ResourceEstimator
)

from shared.orchestration.scheduling.registry.register_estimators import (
    register_estimators
)

from apps.api.models.task import Task


async def main():

    register_estimators()

    task = Task(
        task_type="crawl_chapter"
    )

    estimator = ResourceEstimator()

    profile = await estimator.estimate(
        task=task,
        db=None
    )

    print(profile)

    print(profile.to_dict())

    print(profile.total_cost)


if __name__ == "__main__":

    asyncio.run(
        main()
    )