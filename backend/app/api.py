from contextlib import asynccontextmanager
from typing import Annotated, Any

from fastapi import Body, FastAPI, Query, Request
from fastapi.responses import JSONResponse, Response
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, ConfigDict, Field
from starlette.middleware.trustedhost import TrustedHostMiddleware

from uuid import UUID

from .canvas import read_asset
from .db import connect, migrate
from .models import Kind
from . import reviews
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
    if request.url.path.startswith("/api/"):
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
def workspace(request: Request):
    etag, data = state(request.headers.get("if-none-match"))
    headers = {"ETag":etag, "Cache-Control":"private, no-cache", "Vary":"X-AgentBoard-UI"}
    if data is None:
        return Response(status_code=304, headers=headers)
    return JSONResponse(data, headers=headers)


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


@app.get("/api/visuals/{document_id}/{filename}")
def visual(document_id: str, filename: str):
    with connect() as conn:
        row = conn.execute("""SELECT a.image FROM visual_assets a JOIN records r ON r.id=a.document_id
                              WHERE r.id=%s AND NOT r.deleted AND a.filename=%s""",
                           (document_id, filename)).fetchone()
        if not row:
            raise Problem(404, "Preview unavailable.")
        return Response(bytes(row["image"]), media_type="image/png",
                        headers={"X-Content-Type-Options":"nosniff"})


@app.get("/canvas-content/{asset_key}/{path:path}")
def canvas_content(request: Request, asset_key: UUID, path: str):
    data, media = read_asset(asset_key, path)
    # Browser subresources cannot send the UI header. Limit them to one immutable bundle.
    source = f"{str(request.base_url).rstrip('/')}/canvas-content/{asset_key}/"
    policy = (f"sandbox allow-scripts allow-forms; default-src 'none'; script-src 'unsafe-inline' {source}; "
              f"style-src 'unsafe-inline' {source}; frame-src {source}; img-src data: {source}; "
              f"font-src data: {source}; connect-src 'none'; base-uri 'none'; form-action 'none'")
    return Response(data, media_type=media, headers={"Content-Security-Policy": policy,
                    "X-Content-Type-Options": "nosniff", "Referrer-Policy": "no-referrer",
                    "Cache-Control": "private, no-store"})
