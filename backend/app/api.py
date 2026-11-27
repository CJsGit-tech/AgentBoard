from contextlib import asynccontextmanager
from datetime import datetime
from typing import Annotated, Any, Literal

from fastapi import Body, FastAPI, Query, Request
from fastapi.responses import JSONResponse, Response
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, ConfigDict, Field
from starlette.middleware.trustedhost import TrustedHostMiddleware

from uuid import UUID

from .canvas import asset_etag, read_asset
from .visuals import read_thumbnail
from .db import connect, migrate
from .models import Kind
from . import browser_workspace, canvas_viewer, reviews
from .store import Problem, project_deletion_preview, purge_project, state, write


@asynccontextmanager
async def lifespan(_app):
    migrate()
    reviews.initialize()
    from .assistant import runtime
    await runtime.start()
    try:
        yield
    finally:
        await runtime.stop()


app = FastAPI(title="AgentBoard", lifespan=lifespan)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost","127.0.0.1"])


@app.middleware("http")
async def protect_browser_api(request: Request, call_next):
    if request.url.path.startswith("/api/"):
        origin = request.headers.get("origin")
        if (origin and origin != f"http://{request.headers.get('host')}") or request.headers.get("x-agentboard-ui") != "1":
            return JSONResponse({"detail":"Use the local AgentBoard interface."},status_code=403)
    response = await call_next(request)
    if request.url.path.startswith(("/api/", "/canvas-content/")):
        response.headers.setdefault("Cache-Control", "no-store")
    return response


@app.exception_handler(RequestValidationError)
async def invalid_request(request, err):
    if request.url.path.startswith('/api/assistant/'):
        return JSONResponse({'detail':'Invalid Assistant request. Check the required fields and try again.'},status_code=422)
    from fastapi.exception_handlers import request_validation_exception_handler
    return await request_validation_exception_handler(request,err)


@app.exception_handler(Problem)
async def problem_handler(_request, err):
    return JSONResponse({"detail":str(err)}, status_code=err.status)


class Version(BaseModel):
    model_config = ConfigDict(extra="forbid")
    revision: Annotated[int, Field(strict=True, gt=0)]


class Patch(Version):
    changes: dict[str, Any]


class ProjectPurge(Version):
    confirmation: Annotated[str, Field(strict=True, min_length=1, max_length=240)]
    activity_version: Annotated[str, Field(strict=True, pattern=r"^[0-9]{1,19}$")]


class ReviewStart(Version):
    request: Annotated[str, Field(min_length=1, max_length=8000)]
    operation: str = 'Edit'


class ReviewAssessment(Version):
    assessment: reviews.Assessment


class ScopeDecision(Version):
    accept: bool = Field(strict=True)
    note: Annotated[str, Field(min_length=1, max_length=8000)]


@app.post('/api/reviews/start/{kind}/{key}')
def start_review(kind: Kind, key: str, payload: ReviewStart):
    return reviews.start('Human', kind, key, payload.revision, payload.request, payload.operation)


@app.post('/api/reviews/{key}/assess')
def assess_review(key: str, payload: ReviewAssessment):
    return reviews.submit('Human', key, payload.revision, payload.assessment.model_dump())


@app.post('/api/reviews/{key}/confirm')
def confirm_scope(key: str, payload: ScopeDecision):
    return reviews.confirm(key, payload.revision, payload.accept, payload.note)


@app.get("/healthz")
def health():
    with connect() as conn:
        conn.execute("SELECT 1 FROM schema_versions LIMIT 1")
    return {"status":"ok"}


@app.get("/api/workspace")
def workspace(request: Request, view: Literal["projects", "export"] | None = None,
              project: Annotated[str | None, Query(pattern=r"^[a-zA-Z0-9_-]{1,128}$")] = None):
    previous = request.headers.get("if-none-match")
    if view and project:
        raise Problem(422, "Choose a view or a single project.")
    if view == "export":
        etag, data = state(previous)
    elif view == "projects" or project:
        etag, data = browser_workspace.browser_state(project, previous)
    else:
        raise Problem(410, "Reload this tab to use the current version of AgentBoard.")
    headers = {"ETag":etag, "Cache-Control":"private, no-cache", "Vary":"X-AgentBoard-UI"}
    if data is None:
        return Response(status_code=304, headers=headers)
    return JSONResponse(data, headers=headers)


@app.get("/api/canvases/{key}/viewer")
def read_canvas_viewer(key: str):
    return canvas_viewer.viewer_state(key)


@app.get("/api/records/{kind}/{key}/project")
def record_owner(kind: Kind, key: str):
    return browser_workspace.owner(kind, key)


@app.get("/api/projects/{project}/reviews")
def project_reviews(project: str, subject: str,
                    offset: Annotated[int, Query(ge=0, le=2147483647)] = 0,
                    limit: Annotated[int, Query(ge=1, le=200)] = 20):
    return browser_workspace.review_history(project, subject, offset, limit)


@app.get("/api/projects/{project}/reviews/{key}")
def review_detail(project: str, key: str):
    return browser_workspace.review_detail(project, key)


@app.get("/api/projects/{project}/activity")
def project_history(project: str, before: Annotated[int | None, Query(gt=0, le=9223372036854775807)] = None,
                    limit: Annotated[int, Query(ge=1, le=200)] = 50,
                    record: str = "", actor: str = "", action: str = "", kind: Kind | None = None,
                    search: Annotated[str, Query(max_length=2000)] = "", start: datetime | None = None,
                    end: datetime | None = None):
    return browser_workspace.history_page(project, before, limit, record, actor, action, kind, search, start, end)


@app.get("/api/projects/{key}/deletion-preview")
def preview_project_removal(key: str):
    return project_deletion_preview(key)


@app.post("/api/projects/{key}/purge", status_code=204)
def permanently_remove_project(key: str, payload: ProjectPurge):
    purge_project(key, payload.revision, payload.confirmation, payload.activity_version)


# Specific Assistant routes must precede the generic record-kind routes.
from .assistant_provider import ProviderError


@app.exception_handler(ProviderError)
async def provider_error(_request, err):
    return JSONResponse({'detail':err.message,**err.public()}, status_code={'rate_limited':429,'provider_timeout':504,'provider_unavailable':503}.get(err.code,422))


from .assistant import router as assistant_router
app.include_router(assistant_router)


@app.post("/api/{kind}", status_code=201)
def create(kind: Kind, data: Annotated[dict[str, Any], Body()], editor_role_id: str | None = None):
    return write(kind, "Created", "Human", data, editor_role_id=editor_role_id)


@app.patch("/api/{kind}/{key}")
def edit(kind: Kind, key: str, payload: Patch, editor_role_id: str | None = None):
    return write(kind, "Updated", "Human", payload.changes, key, payload.revision, editor_role_id)


@app.delete("/api/{kind}/{key}")
def remove(kind: Kind, key: str, revision: Annotated[int, Query(gt=0)]):
    return write(kind, "Deleted", "Human", key=key, revision=revision)


@app.post("/api/{kind}/{key}/restore")
def restore(kind: Kind, key: str, payload: Version):
    return write(kind, "Restored", "Human", key=key, revision=payload.revision)


@app.get("/api/visuals/{document_id}/{filename}/thumbnail")
def visual_thumbnail(document_id: str, filename: str, v: Annotated[str, Query(pattern=r"^[a-f0-9]{64}$")]):
    return Response(read_thumbnail(document_id, filename, v), media_type="image/webp",
                    headers={"X-Content-Type-Options": "nosniff"})


@app.get("/api/visuals/{document_id}/{filename}")
def visual(document_id: str, filename: str, v: Annotated[str | None, Query(pattern=r"^[a-f0-9]{64}$")] = None):
    with connect() as conn:
        row = conn.execute("""SELECT a.image FROM visual_assets a JOIN records r ON r.id=a.document_id
                              WHERE r.id=%s AND NOT r.deleted AND a.filename=%s
                              AND (%s::text IS NULL OR a.digest=%s)""",
                           (document_id, filename, v, v)).fetchone()
        if not row:
            raise Problem(404, "This screenshot version is unavailable." if v else "Preview unavailable.")
        return Response(bytes(row["image"]), media_type="image/png",
                        headers={"X-Content-Type-Options":"nosniff"})


@app.get("/canvas-content/{asset_key}/{path:path}")
@app.head("/canvas-content/{asset_key}/{path:path}")
def canvas_content(request: Request, asset_key: UUID, path: str):
    etag = asset_etag(asset_key, path)
    validators = request.headers.get("if-none-match", "")
    unchanged = validators.strip() == "*" or any(
        value.strip().removeprefix("W/") == etag for value in validators.split(",")
    )
    data, size, media = read_asset(asset_key, path, include_content=request.method == "GET" and not unchanged)
    # Browser subresources cannot send the UI header. Limit them to one immutable bundle.
    source = f"{str(request.base_url).rstrip('/')}/canvas-content/{asset_key}/"
    policy = (f"sandbox allow-scripts allow-forms; default-src 'none'; script-src 'unsafe-inline' {source}; "
              f"style-src 'unsafe-inline' {source}; frame-src {source}; img-src data: {source}; "
              f"font-src data: {source}; connect-src 'none'; base-uri 'none'; form-action 'none'")
    headers = {"Content-Security-Policy": policy, "X-Content-Type-Options": "nosniff",
               "Referrer-Policy": "no-referrer", "Cache-Control": "private, no-cache", "ETag": etag}
    if unchanged:
        return Response(status_code=304, headers=headers)
    headers["Content-Length"] = str(size)
    return Response(data, media_type=media, headers=headers)
