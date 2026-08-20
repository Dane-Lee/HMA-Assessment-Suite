from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from fastapi.responses import JSONResponse


class UploadBodyTooLarge(Exception):
    pass


class UploadSizeLimitMiddleware:
    """Reject oversized capture requests as their ASGI body chunks arrive."""

    MULTIPART_OVERHEAD_BYTES = 64 * 1024

    def __init__(self, app: Any, *, max_upload_bytes: int) -> None:
        self.app = app
        self.max_request_bytes = max_upload_bytes + self.MULTIPART_OVERHEAD_BYTES

    @staticmethod
    def _is_capture_upload(scope: dict[str, Any]) -> bool:
        if scope.get("type") != "http" or scope.get("method") != "POST":
            return False
        path = scope.get("path", "")
        return path.startswith("/api/assessments/") and (
            path.endswith("/captures") or path.endswith("/draft-captures")
        )

    async def __call__(
        self,
        scope: dict[str, Any],
        receive: Callable[[], Awaitable[dict[str, Any]]],
        send: Callable[[dict[str, Any]], Awaitable[None]],
    ) -> None:
        if not self._is_capture_upload(scope):
            await self.app(scope, receive, send)
            return

        headers = {key.lower(): value for key, value in scope.get("headers", [])}
        content_length = headers.get(b"content-length")
        if content_length:
            try:
                if int(content_length) > self.max_request_bytes:
                    await self._reject(scope, receive, send)
                    return
            except ValueError:
                pass

        received_bytes = 0

        async def limited_receive() -> dict[str, Any]:
            nonlocal received_bytes
            message = await receive()
            if message.get("type") == "http.request":
                received_bytes += len(message.get("body", b""))
                if received_bytes > self.max_request_bytes:
                    raise UploadBodyTooLarge
            return message

        try:
            await self.app(scope, limited_receive, send)
        except UploadBodyTooLarge:
            await self._reject(scope, receive, send)

    @staticmethod
    async def _reject(scope: dict[str, Any], receive, send) -> None:
        response = JSONResponse(
            {"detail": "Video file is too large."},
            status_code=413,
        )
        await response(scope, receive, send)
