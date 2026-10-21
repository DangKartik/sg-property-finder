"""FastAPI entry point for the neighbourhood recommender backend."""

from __future__ import annotations

import json
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
    app = FastAPI(title="SG Property Finder API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    def respond(envelope: Any) -> Any:
        return JSONResponse(content=toJsonable(envelope))

    @app.get("/api/v1/health")
    def health() -> Any:
        return respond(handlers.health())

    @app.get("/api/v1/ready")
    def ready() -> Any:
        return respond(handlers.ready(context))

    @app.get("/api/v1/criteria")
    def criteria() -> Any:
        return respond(handlers.criteria(context))

    @app.post("/api/v1/address/search")
    def address_search(body: dict[str, Any]) -> Any:
        return respond(handlers.searchAddress(str(body.get("query", "")), context))

    @app.post("/api/v1/recommendations")
    def recommendations(body: dict[str, Any]) -> Any:
        return respond(handlers.recommendations(body, context))

    @app.get("/api/v1/subzones/geometry")
    def subzone_geometry() -> Any:
        return respond(handlers.geometry(context))

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
        return respond(handlers.factsheet(code, payload, context))

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
