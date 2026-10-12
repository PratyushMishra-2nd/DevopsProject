import logging
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.config import get_settings
from app.logging_config import configure_logging
from app.routers import dispatches, donors, lots, system

settings = get_settings()
configure_logging(settings.log_level)
log = logging.getLogger("pantrypulse")

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Stock, expiry and dispatch tracking for community food banks.",
)

if settings.cors_origin_list:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Content-Type"],
    )

QUIET_PATHS = {"/health", "/ready", "/metrics"}


@app.middleware("http")
async def request_log(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    if request.url.path not in QUIET_PATHS:
        log.info(
            "request",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": round((time.perf_counter() - start) * 1000, 2),
            },
        )
    return response


app.include_router(system.router)
app.include_router(lots.router)
app.include_router(donors.router)
app.include_router(dispatches.router)

Instrumentator(
    should_group_status_codes=False,
    excluded_handlers=["/metrics"],
).instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)
