import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger


class LoggingMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):

        start = time.perf_counter()

        response = await call_next(request)

        duration = (time.perf_counter() - start) * 1000

        logger.info(
            "{} {} -> {} ({:.2f} ms)",
            request.method,
            request.url.path,
            response.status_code,
            duration,
        )

        return response
