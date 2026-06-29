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

    @staticmethod
    def _is_available(
            key: GeminiApiKey,
            now: datetime,
    ) -> bool:

        if key.state == ApiKeyState.DISABLED:
            return False

        if key.state == ApiKeyState.BUSY:
            return False

        if key.state == ApiKeyState.FREE:
            return True

        if key.state != ApiKeyState.COOLDOWN:
            return False

        if key.cooldown_until is None:
            return False

        if key.cooldown_until <= now:
            key.state = ApiKeyState.FREE
            key.cooldown_until = None
            return True

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

        cooldowns = [

            (
                    key.cooldown_until - now
            ).total_seconds()

            for key in self._keys

            if (
                    key.state == ApiKeyState.COOLDOWN
                    and key.cooldown_until is not None
            )

        ]

        if cooldowns:
            return max(
                min(cooldowns),
                0.1,
            )

        return None