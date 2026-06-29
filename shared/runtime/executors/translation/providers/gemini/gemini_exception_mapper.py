from google.api_core.exceptions import (
    DeadlineExceeded,
    ResourceExhausted,
    ServiceUnavailable,
    TooManyRequests,
)


class GeminiExceptionMapper:

    @staticmethod
    def is_quota_error(ex: Exception) -> bool:
        if isinstance(ex, (ResourceExhausted, TooManyRequests)):
            return True

        text = str(ex).lower()

        return (
            "resource_exhausted" in text
            or "quota" in text
            or "429" in text
        )

    @staticmethod
    def is_network_error(ex: Exception) -> bool:
        if isinstance(
            ex,
            (
                ServiceUnavailable,
                DeadlineExceeded,
                TimeoutError,
                ConnectionError,
            ),
        ):
            return True

        text = str(ex).lower()

        return (
            "timeout" in text
            or "connection" in text
            or "503" in text
            or "service unavailable" in text
        )

    @staticmethod
    def is_permission_error(ex: Exception) -> bool:
        """
        API key hoặc Google Project không còn sử dụng được.
        Đây là lỗi vĩnh viễn, nên disable API key.
        """

        text = str(ex).lower()

        return (
            "permission_denied" in text
            or "403" in text
            or "api_key_invalid" in text
            or "invalid api key" in text
            or "your project has been denied access" in text
            or "api key not valid" in text
        )

    @staticmethod
    def is_retryable(ex: Exception) -> bool:
        return (
            GeminiExceptionMapper.is_quota_error(ex)
            or GeminiExceptionMapper.is_network_error(ex)
        )