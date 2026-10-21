"""FastAPI entry point for the neighbourhood recommender backend."""

from __future__ import annotations

import asyncio
import json
from contextlib import asynccontextmanager
from typing import Any

from app.api import handlers
from app.bootstrap import AppContext, buildContext
from app.core.serialization import toJsonable

try:
    from fastapi import FastAPI, Query
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import FileResponse, JSONResponse

    FASTAPI_AVAILABLE = True
except ImportError:  # pragma: no cover - exercised only in minimal environments
    FASTAPI_AVAILABLE = False
    FastAPI = None  # type: ignore[assignment]
    Query = None  # type: ignore[assignment]
    CORSMiddleware = None  # type: ignore[assignment]
    FileResponse = None  # type: ignore[assignment]
    JSONResponse = None  # type: ignore[assignment]


def createApp(context: AppContext | None = None) -> Any:
    """Create the FastAPI application.

    Raises:
        RuntimeError: If FastAPI and its transitive dependencies are not installed.
    """
    if not FASTAPI_AVAILABLE:
        raise RuntimeError(
            "FastAPI dependencies are not installed. Install fastapi, starlette and "
            "pydantic before running the API."
        )

    context = context or buildContext()

    @asynccontextmanager
    async def lifespan(_: Any):
        if context.settings.APP_ENV.lower() != "test":
            asyncio.create_task(asyncio.to_thread(context.datasetService.refreshIfStale))
        yield

    app = FastAPI(title="SG Property Finder API", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    def respond(envelope: Any, headers: dict[str, str] | None = None) -> Any:
        return JSONResponse(content=toJsonable(envelope), headers=headers or {})

    def dataHeaders(dataset: str = "subzones") -> dict[str, str]:
        status = context.datasetService.status().get(dataset, {})
        headers = {
            "Cache-Control": "public, max-age=86400",
            "X-Data-Source": str(status.get("source", "unknown")),
        }
        if status.get("dataAsOf"):
            headers["X-Data-As-Of"] = str(toJsonable(status["dataAsOf"]))
        if status.get("dataSnapshotId"):
            headers["ETag"] = f'"{status["dataSnapshotId"]}"'
        if status.get("isStale"):
            headers["X-Data-Stale"] = "true"
        return headers

    @app.get("/api/v1/health")
    def health() -> Any:
        return respond(handlers.health())

    @app.get("/api/v1/ready")
    def ready() -> Any:
        return respond(handlers.ready(context))

    @app.get("/api/v1/criteria")
    def criteria() -> Any:
        return respond(handlers.criteria(context), {"Cache-Control": "public, max-age=86400"})

    @app.get("/api/v1/data/status")
    def data_status() -> Any:
        return respond(handlers.dataStatus(context), {"Cache-Control": "no-store"})

    @app.post("/api/v1/data/refresh")
    def data_refresh() -> Any:
        return respond(handlers.refreshData(context), {"Cache-Control": "no-store"})

    @app.post("/api/v1/address/search")
    def address_search(body: dict[str, Any]) -> Any:
        return respond(handlers.searchAddress(str(body.get("query", "")), context))

    @app.post("/api/v1/recommendations")
    def recommendations(body: dict[str, Any]) -> Any:
        return respond(handlers.recommendations(body, context), {"Cache-Control": "no-store"})

    @app.get("/api/v1/subzones/geometry")
    def subzone_geometry() -> Any:
        return respond(handlers.geometry(context), dataHeaders("subzones"))

    @app.get("/api/v1/subzones/{code}/factsheet")
    def factsheet(
        code: str,
        share: str | None = Query(default=None),
        profile: str | None = Query(default=None),
    ) -> Any:
        payload: dict[str, Any] = {}
        if share:
            try:
                payload, _ = handlers.decodeShare(share)
            except ValueError as exc:
                return respond(handlers.fail("INVALID_SHARE_LINK", str(exc)))
        elif profile:
            try:
                payload = json.loads(profile)
            except json.JSONDecodeError:
                return respond(handlers.fail("INVALID_PROFILE", "Profile query is not valid JSON"))
        else:
            return respond(handlers.fail("PROFILE_REQUIRED", "A share link or profile query is required"))
        headers = {
            **dataHeaders("hdb"),
            "Cache-Control": "private, max-age=300",
        }
        return respond(handlers.factsheet(code, payload, context), headers)

    @app.post("/api/v1/comparison")
    def compare(body: dict[str, Any]) -> Any:
        return respond(
            handlers.comparison(
                body.get("profile", {}),
                [str(item) for item in body.get("subzoneCodes", [])],
                context,
            )
        )

    @app.post("/api/v1/reports/pdf")
    def report(body: dict[str, Any]) -> Any:
        return respond(
            handlers.generateReport(
                body.get("profile", {}),
                [str(item) for item in body.get("subzoneCodes", [])],
                context,
            )
        )

    @app.get("/api/v1/reports/download/{report_id}")
    def download(report_id: str) -> Any:
        path = handlers.reportPath(report_id, context)
        if path is None or not path.exists():
            return JSONResponse(
                status_code=404,
                content=toJsonable(handlers.fail("REPORT_NOT_FOUND", "Report not found or expired")),
            )
        return FileResponse(path, media_type="application/pdf", filename=path.name)

    return app


try:
    app = createApp() if FASTAPI_AVAILABLE else None
except Exception:  # pragma: no cover - startup configuration is environment-specific
    app = None
