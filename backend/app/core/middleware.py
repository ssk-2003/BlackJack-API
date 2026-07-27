import time
import uuid
import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = structlog.get_logger()

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        start_time = time.perf_counter()
        
        # Log request receipt
        logger.info(
            "http_request_received",
            method=request.method,
            path=request.url.path,
            client_host=request.client.host if request.client else "unknown",
        )

        try:
            response = await call_next(request)
        except Exception as exc:
            duration = time.perf_counter() - start_time
            logger.exception(
                "http_request_failed",
                method=request.method,
                path=request.url.path,
                duration_seconds=duration,
                error=str(exc),
            )
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error. Reference ID: " + request_id},
            )

        duration = time.perf_counter() - start_time
        response.headers["X-Request-ID"] = request_id
        
        logger.info(
            "http_request_completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_seconds=duration,
        )
        return response
