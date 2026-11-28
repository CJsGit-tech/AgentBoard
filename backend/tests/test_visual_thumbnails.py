"""Gallery derivatives are generated lazily. Original evidence remains digest-pinned."""
import base64
from hashlib import sha256
from io import BytesIO
import unittest
from unittest.mock import patch

from PIL import Image

from app.db import connect
from app.visuals import attach
from tests import test_contracts as fixtures


def png(color):
    output = BytesIO()
    Image.new("RGBA", (800, 1200), color).save(output, format="PNG")
    return output.getvalue()


class VisualThumbnailIntegration(unittest.TestCase):
    setUp = fixtures.WorkspaceIntegration.setUp
    create = fixtures.WorkspaceIntegration.create
    finish_reviews = fixtures.WorkspaceIntegration.finish_reviews

    def test_existing_capture_thumbnail_cache_and_original_replacement(self):
        project = self.create("projects", name="Screens")["id"]
        self.create("documents", project=project, name="Product Brief", document_type="product-vision", content="Review the screen.")
        inventory = self.create("documents", project=project, name="Captures", document_type="screen-inventory", content="Review evidence.")
        self.finish_reviews(project)
        key = inventory["id"]
        old = png("blue")
        original = sha256(old).hexdigest()
        with connect() as conn:
            conn.execute("INSERT INTO visual_assets(document_id,filename,digest,image) VALUES (%s,'example.png',%s,%s)",
                         (key, original, old))
        path = f"/api/visuals/{key}/example.png"
        thumb = path + "/thumbnail"
        self.assertEqual(self.http.get(thumb + "?v=" + "0" * 64).status_code, 404)
        self.assertEqual(self.http.get(thumb + "?v=" + original, headers={"X-AgentBoard-UI": ""}).status_code, 403)
        response = self.http.get(thumb + "?v=" + original)
        self.assertEqual(response.status_code, 200)
        with Image.open(BytesIO(response.content)) as image:
            self.assertEqual((image.format, image.size), ("WEBP", (256, 384)))
        with patch("app.visuals._thumbnail", side_effect=AssertionError("Cached thumbnail regenerated")):
            self.assertEqual(self.http.get(thumb + "?v=" + original).content, response.content)
        self.assertEqual(self.http.get(path + "?v=" + original).content, old)
        new = png("red")
        attach("Codex", key, inventory["revision"], "example.png", base64.b64encode(new).decode())
        latest = sha256(new).hexdigest()
        self.assertEqual(self.http.get(thumb + "?v=" + original).status_code, 404)
        self.assertEqual(self.http.get(path + "?v=" + original).status_code, 404)
        self.assertNotEqual(self.http.get(thumb + "?v=" + latest).content, response.content)
        self.assertEqual(self.http.get(path + "?v=" + latest).content, new)
        with connect() as conn:
            conn.execute("UPDATE records SET deleted=true WHERE id=%s", (key,))
        self.assertEqual(self.http.get(thumb + "?v=" + latest).status_code, 404)


def jpeg(color):
    output = BytesIO()
    Image.new("RGB", (800, 1200), color).save(output, format="JPEG", quality=85)
    return output.getvalue()


class JpegVisualIntegration(unittest.TestCase):
    setUp = fixtures.WorkspaceIntegration.setUp
    create = fixtures.WorkspaceIntegration.create
    finish_reviews = fixtures.WorkspaceIntegration.finish_reviews

    def test_jpeg_upload_is_served_as_jpeg_and_mismatches_are_rejected(self):
        from app.store import Problem
        project = self.create("projects", name="Jpeg screens")["id"]
        self.create("documents", project=project, name="Product Brief", document_type="product-vision", content="Review the screen.")
        inventory = self.create("documents", project=project, name="Captures", document_type="screen-inventory", content="Review evidence.")
        self.finish_reviews(project)
        key, data = inventory["id"], jpeg("green")
        encoded = base64.b64encode(data).decode()
        for name, payload in (("wrong.png", encoded), ("wrong.jpg", base64.b64encode(png("red")).decode()),
                              ("cut.jpg", base64.b64encode(data[:len(data)//2]).decode()), ("shot.gif", encoded)):
            with self.assertRaises(Problem, msg=name):
                attach("Codex", key, inventory["revision"], name, payload)
        attach("Codex", key, inventory["revision"], "shot.jpg", encoded)
        digest = sha256(data).hexdigest()
        response = self.http.get(f"/api/visuals/{key}/shot.jpg?v={digest}")
        self.assertEqual((response.status_code, response.headers["content-type"], response.content), (200, "image/jpeg", data))
        thumb = self.http.get(f"/api/visuals/{key}/shot.jpg/thumbnail?v={digest}")
        with Image.open(BytesIO(thumb.content)) as image:
            self.assertEqual(image.format, "WEBP")
