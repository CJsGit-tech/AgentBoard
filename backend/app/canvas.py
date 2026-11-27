"""Immutable, project-owned HTML design canvas publications."""
import base64
import binascii
import hashlib
import re
from pathlib import PurePosixPath
from uuid import UUID, uuid4

from psycopg.types.json import Jsonb
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .db import connect
from .store import Problem, get_row, public
from . import reviews

MEDIA = {".html": "text/html", ".css": "text/css", ".js": "text/javascript",
         ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp",
         ".svg": "image/svg+xml", ".woff2": "font/woff2"}
MAX_BYTES = 12 * 1024 * 1024


def unpack(files):
    if not 1 <= len(files) <= 200 or not files.get("gallery.html"):
        raise Problem(422, "Include gallery.html and up to 199 supporting files.")
    total = 0
    decoded = {}
    digest = hashlib.sha256()
    for path, encoded in sorted(files.items()):
        if (len(path) > 240 or not re.fullmatch(r"(?:[A-Za-z0-9_-][A-Za-z0-9_.-]*/)*[A-Za-z0-9_-][A-Za-z0-9_.-]*", path)
                or PurePosixPath(path).suffix.lower() not in MEDIA):
            raise Problem(422, "Use relative canvas asset paths with supported file types.")
        if len(encoded) > 4 * ((MAX_BYTES - total + 2) // 3):
            raise Problem(422, "Canvas files exceed 12 MiB.")
        try:
            data = base64.b64decode(encoded, validate=True)
        except (ValueError, binascii.Error) as err:
            raise Problem(422, "A canvas file has invalid base64.") from err
        total += len(data)
        if total > MAX_BYTES or not data:
            raise Problem(422, "Use non-empty files totaling at most 12 MiB.")
        digest.update(path.encode() + b"\0" + hashlib.sha256(data).digest())
        decoded[path] = data
    return decoded, digest.hexdigest()


class SourceRevision(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    document_id: str = Field(min_length=1, max_length=240)
    revision: int = Field(gt=0)


class Publication(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    change_note: str = Field(min_length=1, max_length=2000)
    sources: list[SourceRevision] = Field(min_length=1, max_length=40)
    screen_count: int | None = Field(default=None, gt=0, le=2147483647)


def publish(actor, document_id, revision, files, change_note, sources, screen_count=None):
    try:
        metadata = Publication.model_validate({"change_note": change_note, "sources": sources, "screen_count": screen_count})
        if not metadata.change_note.strip():
            raise ValueError("Enter a change note.")
        source_ids = [source.document_id for source in metadata.sources]
        if len(set(source_ids)) != len(source_ids):
            raise ValueError("List each source document once.")
    except (ValidationError, ValueError) as err:
        raise Problem(422, str(err)) from err
    contents, digest = unpack(files)
    with connect() as conn:
        conn.execute("SELECT pg_advisory_xact_lock(625016)")
        row = get_row(conn, "documents", document_id)
        if row["data"].get("document_type") not in ("design-canvas", "design-topic"):
            raise Problem(422, "Select a Design Profile document.")
        if row["revision"] != revision:
            raise Problem(409, "The document changed. Reload before publishing.")
        previous = row["canvas_versions"] or []
        requested = sorted([source.model_dump() for source in metadata.sources], key=lambda item: item["document_id"])
        if (previous and previous[0]["digest"] == digest
                and previous[0]["change_note"] == metadata.change_note.strip()
                and previous[0]["screen_count"] == metadata.screen_count
                and sorted([{"document_id": item["document_id"], "revision": item["revision"]}
                            for item in previous[0]["sources"]], key=lambda item: item["document_id"]) == requested):
            return public(row)
        reviews.require_ready(conn, document_id)
        snapshot = []
        for source in requested:
            current = get_row(conn, "documents", source["document_id"])
            if current["project"] != row["project"]:
                raise Problem(422, "Canvas sources must belong to the same project.")
            if current["revision"] != source["revision"]:
                raise Problem(409, "A source document changed. Review it before publishing.")
            reviews.require_ready(conn, source['document_id'])
            snapshot.append({**source, "name": current["data"]["name"]})
        version = previous[0]["version"] + 1 if previous else 1
        asset_key = uuid4()
        conn.execute("""INSERT INTO canvas_versions(document_id,version,asset_key,digest,change_note,sources,publisher,screen_count)
                     VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
                     (document_id, version, asset_key, digest, metadata.change_note.strip(), Jsonb(snapshot), actor, metadata.screen_count))
        with conn.cursor() as cursor:
            cursor.executemany("INSERT INTO canvas_files(asset_key,path,content) VALUES (%s,%s,%s)",
                               [(asset_key, path, data) for path, data in contents.items()])
        conn.execute("UPDATE records SET revision=revision+1 WHERE id=%s", (document_id,))
        conn.execute("""INSERT INTO activity(project,actor,action,kind,record,name,changes)
                     VALUES (%s,%s,'Updated','documents',%s,%s,%s)""",
                     (row["project"], actor, document_id, row["data"]["name"],
                      Jsonb([["Canvas version", version - 1 or None, version]])))
        return public(get_row(conn, "documents", document_id))


def read_asset(asset_key: UUID, path: str, *, include_content: bool):
    with connect() as conn:
        row = conn.execute("""SELECT CASE WHEN %s THEN f.content END AS content,
                   octet_length(f.content) AS size FROM canvas_files f
            JOIN canvas_versions v USING(asset_key) JOIN records r ON r.id=v.document_id
            WHERE f.asset_key=%s AND f.path=%s AND NOT r.deleted""", (include_content, asset_key, path)).fetchone()
        if not row:
            raise Problem(404, "Canvas file unavailable.")
        return row["content"], row["size"], MEDIA[PurePosixPath(path).suffix.lower()]


def asset_etag(asset_key: UUID, path: str):
    # Publishing assigns a new immutable key each time. Identify one file within that publication.
    return '"' + hashlib.sha256(asset_key.bytes + path.encode("utf-8")).hexdigest() + '"'
