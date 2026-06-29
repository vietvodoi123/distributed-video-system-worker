import asyncio
import logging

from datetime import datetime, timedelta

from shared.runtime.executors.translation.models.api_key import (
    GeminiApiKey,ApiKeyState
)


logger = logging.getLogger(__name__)


class GeminiKeyPool:

    def __init__(
        self,
        *,
        api_keys: list[str],
        cooldown_seconds: int,
        network_error_cooldown_seconds: int = 10,
        min_request_interval_seconds: float = 1.0,
    ):

        if not api_keys:
            raise ValueError("Gemini API key list is empty.")

        self._keys = [

            GeminiApiKey(
                id=i + 1,
                api_key=key,
            )

            for i, key in enumerate(api_keys)

        ]

        self._cooldown_seconds = cooldown_seconds
        self._network_error_cooldown_seconds = (
            network_error_cooldown_seconds
        )

        self._lock = asyncio.Lock()

        self._condition = asyncio.Condition(self._lock)

        self._current_index = 0
        self._min_request_interval_seconds = (
            min_request_interval_seconds
        )
        logger.info(
            "[GeminiKeyPool] Loaded %d API keys.",
            len(self._keys),
        )

    async def acquire(self) -> GeminiApiKey:

        while True:

            async with self._condition:

                now = datetime.utcnow()

                for _ in range(len(self._keys)):

                    key = self._next_key()

                    if self._is_available(
                            key,
                            now,
                    ):
                        key.state = ApiKeyState.BUSY

                        key.last_request_at = now

                        return key

                timeout = self._next_available_time(now)

                if timeout is None:

                    await self._condition.wait()

                else:

                    try:

                        await asyncio.wait_for(
                            self._condition.wait(),
                            timeout=timeout,
                        )

                    except asyncio.TimeoutError:
                        pass

    async def report_success(
            self,
            key: GeminiApiKey,
    ):

        async with self._condition:
            key.total_requests += 1

            key.consecutive_errors = 0

            key.cooldown_until = None

            key.state = ApiKeyState.FREE

            self._condition.notify()

    async def report_quota_error(
        self,
        key: GeminiApiKey,
    ):

        async with self._condition:
            key.total_errors += 1
            key.consecutive_errors += 1

            key.state = ApiKeyState.COOLDOWN

            key.cooldown_until = (
                    datetime.utcnow()
                    + timedelta(seconds=self._cooldown_seconds)
            )

            self._condition.notify()

    async def report_error(
        self,
        key: GeminiApiKey,
    ):

        async with self._condition:
            key.total_errors += 1

            key.consecutive_errors += 1

            key.state = ApiKeyState.COOLDOWN

            key.cooldown_until = (
                    datetime.utcnow()
                    + timedelta(
                seconds=self._network_error_cooldown_seconds
            )
            )
            self._condition.notify()


    def _next_key(self) -> GeminiApiKey:

        key = self._keys[self._current_index]

        self._current_index = (
            self._current_index + 1
        ) % len(self._keys)

        return key

    def _is_available(
            self,
            key: GeminiApiKey,
            now: datetime,
    ) -> bool:

        if key.state == ApiKeyState.DISABLED:
            return False

        if key.state == ApiKeyState.BUSY:
            return False

        if key.state == ApiKeyState.COOLDOWN:

            if key.cooldown_until is None:
                return False

            if key.cooldown_until > now:
                return False

            key.state = ApiKeyState.FREE
            key.cooldown_until = None

        if key.state == ApiKeyState.FREE:

            if key.last_request_at is None:
                return True

            elapsed = (
                    now - key.last_request_at
            ).total_seconds()

            return (
                    elapsed
                    >= self._min_request_interval_seconds
            )

        return False

    async def disable(
            self,
            key: GeminiApiKey,
    ):

        async with self._condition:
            key.state = ApiKeyState.DISABLED

            key.cooldown_until = None

            self._condition.notify()

    def _next_available_time(
            self,
            now: datetime,
    ) -> float | None:

        wait_times = []

        for key in self._keys:

            # Đang cooldown
            if (
                    key.state == ApiKeyState.COOLDOWN
                    and key.cooldown_until is not None
            ):
                wait_times.append(
                    max(
                        (
                                key.cooldown_until - now
                        ).total_seconds(),
                        0.1,
                    )
                )
                continue

            # FREE nhưng đang rate limit
            if (
                    key.state == ApiKeyState.FREE
                    and key.last_request_at is not None
            ):

                elapsed = (
                        now - key.last_request_at
                ).total_seconds()

                remaining = (
                        self._min_request_interval_seconds
                        - elapsed
                )

                if remaining > 0:
                    wait_times.append(
                        max(
                            remaining,
                            0.1,
                        )
                    )

        if wait_times:
            return min(wait_times)

        return None