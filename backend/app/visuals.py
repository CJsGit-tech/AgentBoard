"""Store PNG previews on the inventory they illustrate."""
import base64
import binascii
from hashlib import sha256
import re
import struct
import zlib

from psycopg.types.json import Jsonb

from .db import connect
from .store import Problem, get_row, public
from . import reviews


def decode_png(encoded):
    if len(encoded) > 12_000_000:
        raise Problem(422, "Use a PNG below 8 MiB.")
    try:
        image = base64.b64decode(encoded, validate=True)
    except (ValueError, binascii.Error) as err:
        raise Problem(422, "Invalid base64 image.") from err
    if len(image) > 8 * 1024**2 or not image.startswith(b"\x89PNG\r\n\x1a\n"):
        raise Problem(422, "Use a PNG below 8 MiB.")
    pos = 8
    has_data = False
    while pos + 12 <= len(image):
        size, kind = struct.unpack_from(">I4s", image, pos)
        end = pos + 8 + size
        if end + 4 > len(image) or zlib.crc32(image[pos+4:end]) != struct.unpack_from(">I", image, end)[0]:
            break
        if pos == 8:
            if kind != b"IHDR" or size != 13:
                break
            width, height = struct.unpack_from(">II", image, pos + 8)
            if not width or not height or width * height > 24_000_000:
                raise Problem(422, "Use a preview up to 24 megapixels.")
        has_data |= kind == b"IDAT" and size > 0
        pos = end + 4
        if kind == b"IEND" and size == 0 and has_data and pos == len(image):
            return image
    raise Problem(422, "The PNG is incomplete or damaged.")


def attach(actor, document_id, revision, filename, png_base64):
    if not re.fullmatch(r"[\w .-]{1,120}\.png", filename, flags=re.ASCII | re.IGNORECASE):
        raise Problem(422, "Use a simple PNG filename.")
    image = decode_png(png_base64)
    digest = sha256(image).hexdigest()
    with connect() as conn:
        conn.execute("SELECT pg_advisory_xact_lock(625016)")
        row = get_row(conn, "documents", document_id)
        if row["data"].get("document_type") != "screen-inventory":
            raise Problem(422, "Choose a screen inventory.")
        if row["revision"] != revision:
            raise Problem(409, "This inventory changed. Reload its latest revision.")
        old = conn.execute("SELECT digest FROM visual_assets WHERE document_id=%s AND filename=%s",
                           (document_id, filename)).fetchone()
        if old and old["digest"] == digest:
            return public(row)
        reviews.sync_project(conn, row['project'], actor)
        reviews.require_ready(conn, document_id)
        conn.execute("""INSERT INTO visual_assets VALUES (%s,%s,%s,%s)
                        ON CONFLICT (document_id,filename) DO UPDATE
                        SET digest=excluded.digest,image=excluded.image""",
                     (document_id, filename, digest, image))
        conn.execute("UPDATE records SET revision=revision+1 WHERE id=%s", (document_id,))
        changes = [[filename, old["digest"] if old else None, digest]]
        conn.execute("""INSERT INTO activity(project,actor,action,kind,record,name,changes)
                        VALUES (%s,%s,'Updated','documents',%s,%s,%s)""",
                     (row["project"], actor, document_id, row["data"]["name"], Jsonb(changes)))
        return public(get_row(conn, "documents", document_id))
