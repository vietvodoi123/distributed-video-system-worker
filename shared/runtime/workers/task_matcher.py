def can_execute_task(
    worker_capabilities,
    required_capabilities
):

    return all(

        capability
        in worker_capabilities

        for capability
        in required_capabilities
    )