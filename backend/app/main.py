import asyncio
import base64
from contextlib import asynccontextmanager
import json
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated
from urllib.parse import urlparse

from fastapi import Depends, FastAPI, Header, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy import or_, select, text, tuple_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.errors import ApiError, api_error_handler
from app.api.routes import router
from app.artifacts.routes import approval_router, router as artifacts_router
from app.sdk.routes import router as sdk_router
from app.db.session import SessionLocal, get_db
from app.db.models import ActivityEvent, Project, AgentRun
from app.artifacts.models import Ticket
from app.schemas.common import ActivityCreate
from app.services.activity import RETENTION_DAYS, record_activity, serialize_activity
from app.services.idempotency import reserve
from pydantic import BaseModel, Field
from app.settings import settings

from app.mcp.server import asgi_app as mcp_asgi_app, _transport_app as mcp_transport_app


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Runs are process-local tasks. Never replay provider calls after a restart.
    with SessionLocal() as db:
        interrupted = db.scalars(select(AgentRun).where(AgentRun.status.in_(["queued", "running"])))
        for run in interrupted:
            run.status = "failed"
            run.error = "Run interrupted by application restart. Submit a new prompt to retry."
            run.updated_at = datetime.now(timezone.utc)
        db.commit()
    async with mcp_transport_app.lifespan(_app):
        yield


app = FastAPI(title="AgentBoard API", version="0.1.0", lifespan=lifespan)
app.include_router(router)
app.include_router(artifacts_router)
app.include_router(approval_router)
app.include_router(sdk_router)
app.mount("/mcp", mcp_asgi_app)
app.add_exception_handler(ApiError, api_error_handler)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    fields = {".".join(str(part) for part in error["loc"] if part != "body"): error["msg"] for error in exc.errors()}
    return JSONResponse(status_code=422, content={"error": {"code": "invalid_input", "message": "Request fields are invalid", "fields": fields}, "request_id": getattr(request.state, "request_id", "")})


@app.middleware("http")
async def local_request_guard(request: Request, call_next):
    request.state.request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    if request.url.path.startswith("/api/") or request.url.path == "/events":
        host = (urlparse("//" + request.headers.get("host", "")).hostname or "").lower()
        configured_host = (urlparse(settings.agentboard_origin).hostname or "").lower()
        if host not in {"localhost", "127.0.0.1", "[::1]", "testserver", configured_host}:
            return JSONResponse(status_code=400, content={"error": {"code": "invalid_host", "message": "Host is not allowed", "fields": {}}, "request_id": request.state.request_id})
        origin = request.headers.get("origin")
        if origin and origin.rstrip("/") != settings.agentboard_origin.rstrip("/"):
            return JSONResponse(status_code=403, content={"error": {"code": "invalid_origin", "message": "Origin is not allowed", "fields": {}}, "request_id": request.state.request_id})
        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            if not origin or origin.rstrip("/") != settings.agentboard_origin.rstrip("/"):
                return JSONResponse(status_code=403, content={"error": {"code": "origin_required", "message": "A trusted Origin is required", "fields": {}}, "request_id": request.state.request_id})
            cookie = request.cookies.get("agentboard_csrf")
            header = request.headers.get("x-csrf-token")
            if not cookie or not header or not secrets.compare_digest(cookie, header):
                return JSONResponse(status_code=403, content={"error": {"code": "csrf_failed", "message": "Refresh the local session and retry", "fields": {}}, "request_id": request.state.request_id})
            # Bound the actual body too, including requests without Content-Length.
            body = bytearray()
            async for chunk in request.stream():
                body.extend(chunk)
                if len(body) > settings.max_request_bytes:
                    return JSONResponse(status_code=413, content={"error": {"code": "request_too_large", "message": "Request exceeds the configured limit", "fields": {}}, "request_id": request.state.request_id})
            request._body = bytes(body)
            if body and request.headers.get("content-type", "").split(";", 1)[0] != "application/json":
                return JSONResponse(status_code=415, content={"error": {"code": "content_type_required", "message": "Use application/json", "fields": {}}, "request_id": request.state.request_id})
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    return response


@app.get("/healthz")
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise ApiError(503, "database_unavailable", "Database is unavailable") from exc
    return {"status": "ok", "database": "ready"}


@app.get("/api/v1/session")
def create_local_session(request: Request):
    token = request.cookies.get("agentboard_csrf") or secrets.token_urlsafe(32)
    response = JSONResponse({"csrf_token": token})
    response.set_cookie("agentboard_csrf", token, httponly=False, secure=False, samesite="strict", path="/")
    return response


@app.get("/api/v1/projects/{project_id}/activity")
def list_activity(
    project_id: uuid.UUID,
    limit: int = Query(50, ge=1, le=100),
    cursor: str | None = None,
    ticket_id: uuid.UUID | None = None,
    agent_client_id: uuid.UUID | None = None,
    agent: str | None = None,
    event_type: str | None = None,
    outcome: str | None = None,
    labels: list[str] | None = Query(None),
    since: datetime | None = None,
    until: datetime | None = None,
    provenance: str | None = None,
    db: Session = Depends(get_db),
):
    if db.get(Project, project_id) is None:
        raise ApiError(404, "not_found", "Project not found")
    cutoff = datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)
    stmt = select(ActivityEvent).where(ActivityEvent.project_id == project_id, ActivityEvent.received_at > cutoff)
    if ticket_id:
        stmt = stmt.where(ActivityEvent.ticket_id == ticket_id)
    if agent_client_id:
        stmt = stmt.where(ActivityEvent.client_id == agent_client_id)
    if agent:
        stmt = stmt.where(ActivityEvent.agent_name == agent)
    if event_type:
        stmt = stmt.where(ActivityEvent.event_type == event_type)
    if outcome:
        stmt = stmt.where(ActivityEvent.outcome == outcome)
    if labels:
        if len(labels) > 16 or any(not label or len(label) > 64 for label in labels):
            raise ApiError(422, "invalid_labels", "Provide up to 16 labels of at most 64 characters")
        stmt = stmt.where(or_(*(ActivityEvent.labels.contains([label]) for label in labels)))
    if since:
        stmt = stmt.where(ActivityEvent.occurred_at >= since)
    if until:
        stmt = stmt.where(ActivityEvent.occurred_at <= until)
    if provenance:
        stmt = stmt.where(ActivityEvent.provenance == provenance)
    if cursor:
        try:
            raw = base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4)).decode()
            timestamp, event_id = raw.split("|", 1)
            cursor_time, cursor_id = datetime.fromisoformat(timestamp), uuid.UUID(event_id)
        except (ValueError, UnicodeDecodeError):
            raise ApiError(422, "invalid_cursor", "Cursor is invalid")
        stmt = stmt.where(tuple_(ActivityEvent.received_at, ActivityEvent.id) < tuple_(cursor_time, cursor_id))
    rows = list(db.scalars(stmt.order_by(ActivityEvent.received_at.desc(), ActivityEvent.id.desc()).limit(limit + 1)))
    more = len(rows) > limit
    rows = rows[:limit]
    
    next_cursor = None
    if more and rows:
        raw = f"{rows[-1].received_at.isoformat()}|{rows[-1].id}"
        next_cursor = base64.urlsafe_b64encode(raw.encode()).decode().rstrip("=")
    return {"items": [serialize_activity(row) for row in rows], "next_cursor": next_cursor}


@app.post("/api/v1/projects/{project_id}/activity", status_code=201)
def append_activity(
    project_id: uuid.UUID, body: ActivityCreate,
    key: Annotated[str, Header(alias="Idempotency-Key")],
    db: Session = Depends(get_db),
):
    if db.get(Project, project_id) is None:
        raise ApiError(404, "not_found", "Project not found")
    if body.ticket_id and not db.scalar(select(Ticket.id).where(Ticket.project_id == project_id, Ticket.id == body.ticket_id)):
        raise ApiError(404, "not_found", "Ticket not found in this project")
    if body.event_type not in {"dispatch", "tool_call", "ticket_update", "work"}:
        raise ApiError(422, "invalid_event_type", "Unsupported agent-reported event type")
    if body.outcome not in {"started", "success", "failed", "pending", "rejected", "cancelled"}:
        raise ApiError(422, "invalid_outcome", "Unsupported activity outcome")
    operation, fresh = reserve(db, f"projects:{project_id}:activity:append", key, body.model_dump(mode="json"))
    if not fresh:
        event = db.get(ActivityEvent, uuid.UUID(operation.result_json["id"]))
        if not event or event.received_at <= datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS):
            raise ApiError(404, "activity_expired", "This activity record is no longer retained")
        return serialize_activity(event)
    try:
        event = record_activity(db, project_id=project_id, ticket_id=body.ticket_id,
            agent_name=body.agent_name, action=body.action, event_type=body.event_type,
            outcome=body.outcome, dedupe_key=f"browser:{key}", summary=body.summary,
            labels=body.labels, occurred_at=body.occurred_at, provenance="agent_reported")
    except ValueError as exc:
        raise ApiError(422, "invalid_activity", str(exc)) from exc
    result = serialize_activity(event)
    operation.result_json = {"id": result["id"]}
    db.commit()
    return result


@app.get("/events")
async def stream_events(request: Request, project_id: uuid.UUID | None = None):
    cursor = request.headers.get("last-event-id")
    after_time, after_id = datetime.now(timezone.utc), uuid.UUID(int=0)
    needs_resync = False
    if cursor:
        try:
            raw = base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4)).decode()
            timestamp, event_id = raw.split("|", 1)
            parsed_time = datetime.fromisoformat(timestamp)
            if parsed_time.utcoffset() is None:
                raise ValueError("Event cursor timestamp must include a timezone")
            after_time, after_id = parsed_time, uuid.UUID(event_id)
            if after_time < datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS):
                needs_resync = True
        except (ValueError, UnicodeDecodeError):
            needs_resync = True
    async def generate():
        nonlocal after_time, after_id
        yield "retry: 1500\n\n"
        if needs_resync:
            after_time, after_id = datetime.now(timezone.utc), uuid.UUID(int=0)
            fresh_cursor = base64.urlsafe_b64encode(f"{after_time.isoformat()}|{after_id}".encode()).decode().rstrip("=")
            yield f"id: {fresh_cursor}\nevent: resync\ndata: {{}}\n\n"
        while not await request.is_disconnected():
            cutoff = datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)
            with SessionLocal() as session:
                stmt = select(ActivityEvent).where(ActivityEvent.received_at > cutoff,
                    tuple_(ActivityEvent.received_at, ActivityEvent.id) > tuple_(after_time, after_id))
                if project_id:
                    stmt = stmt.where(ActivityEvent.project_id == project_id)
                events = list(session.scalars(stmt.order_by(ActivityEvent.received_at, ActivityEvent.id).limit(100)))
                payloads = [{"id": e.id, "project_id": e.project_id, "ticket_id": e.ticket_id, "event_type": e.event_type,
                             "outcome": e.outcome, "received_at": e.received_at.isoformat().replace("+00:00", "Z")} for e in events]
                if events:
                    last = events[-1]
                    after_time, after_id = last.received_at, last.id
            for event, payload in zip(events, payloads):
                event_cursor = base64.urlsafe_b64encode(f"{event.received_at.isoformat()}|{event.id}".encode()).decode().rstrip("=")
                yield f"id: {event_cursor}\nevent: activity\ndata: {json.dumps(payload, default=str)}\n\n"
            if not events:
                yield ": keepalive\n\n"
            await asyncio.sleep(1.5)
    return StreamingResponse(generate(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.exception_handler(SQLAlchemyError)
async def database_error_handler(request: Request, exc: SQLAlchemyError):
    return JSONResponse(status_code=503, content={"error": {"code": "database_unavailable", "message": "Database is temporarily unavailable", "fields": {}}, "request_id": getattr(request.state, "request_id", "")})


# Keep unknown API paths as JSON 404s for every supported API method.
@app.api_route("/api", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
@app.api_route("/api/{api_path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
def api_not_found(request: Request, api_path: str = ""):
    return JSONResponse(status_code=404, content={
        "error": {"code": "not_found", "message": "Endpoint not found", "fields": {}},
        "request_id": getattr(request.state, "request_id", ""),
    })


# Register the SPA last so application endpoints retain their own errors.
from pathlib import Path
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

_static = Path(__file__).resolve().parents[1] / "static"
if _static.is_dir():
    if (_static / "assets").is_dir():
        app.mount("/assets", StaticFiles(directory=_static / "assets"), name="assets")

    @app.get("/{frontend_path:path}")
    def frontend(frontend_path: str):
        if frontend_path.split("/", 1)[0] in {"api", "mcp", "events", "healthz", "assets"}:
            return JSONResponse(status_code=404, content={"error": {"code": "not_found", "message": "Endpoint not found"}})
        return FileResponse(_static / "index.html")
