"""Publish the reviewed files listed in a local canvas manifest via AgentBoard MCP."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import subprocess

from attach_visual import request


def package(manifest):
    root = manifest.resolve().parent
    paths = json.loads(manifest.read_text(encoding="utf-8"))
    if (not isinstance(paths, list) or not 1 <= len(paths) <= 200
            or not all(isinstance(path, str) for path in paths)
            or len(set(paths)) != len(paths) or "gallery.html" not in paths):
        raise ValueError("List gallery.html and each supporting file exactly once in the manifest.")
    files = {}
    digest = hashlib.sha256()
    total = 0
    for path in sorted(paths):
        source = (root / path).resolve(strict=True)
        if not source.is_relative_to(root) or source.relative_to(root).as_posix() != path or not source.is_file():
            raise ValueError(f"Choose a regular file in the canvas folder: {path}")
        total += source.stat().st_size
        if total > 12 * 1024**2:
            raise ValueError("The complete canvas must fit within 12 MiB.")
        data = source.read_bytes()
        digest.update(path.encode() + b"\0" + hashlib.sha256(data).digest())
        files[path] = base64.b64encode(data).decode("ascii")
    return files, digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("launcher", type=Path)
    parser.add_argument("client", choices=("Codex", "Claude"))
    parser.add_argument("document")
    parser.add_argument("revision", type=int)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("document_url")
    parser.add_argument("--publication", required=True, type=Path,
                        help="JSON containing change_note and source document_id/revision pairs used to build the draft")
    args = parser.parse_args()
    publication = json.loads(args.publication.read_text(encoding="utf-8"))
    if not isinstance(publication, dict) or set(publication) != {"change_note", "sources"}:
        raise ValueError("Publication metadata must contain change_note and sources.")

    files, digest = package(args.manifest)
    with subprocess.Popen([str(args.launcher.resolve()), args.client], stdin=subprocess.PIPE,
                          stdout=subprocess.PIPE, text=True) as process:
        try:
            request(process, {"jsonrpc":"2.0", "id":1, "method":"initialize", "params":{
                "protocolVersion":"2025-03-26", "capabilities":{}, "clientInfo":{"name":"agentbuild-canvas","version":"1"}}})
            request(process, {"jsonrpc":"2.0","method":"notifications/initialized"})

            def call(seq, name, arguments):
                result = request(process, {"jsonrpc":"2.0","id":seq,"method":"tools/call",
                                           "params":{"name":name, "arguments":arguments}})
                if result.get("isError"):
                    raise RuntimeError(str(result["content"]))
                return result["structuredContent"]

            target = {"kind":"documents", "id":args.document}
            before = call(2, "get_record", target)
            if before.get("record_url") != args.document_url or before["document_type"] not in ("design-topic", "design-canvas"):
                raise ValueError("The launcher does not point to the selected Design Profile.")
            call(3, "publish_canvas", {"document_id":args.document, "revision":args.revision, "files":files, **publication})
            saved = call(4, "get_record", target)
            latest = saved["canvas_versions"][0]
            references = sorted([{"document_id": source["document_id"], "revision": source["revision"]}
                                 for source in latest["sources"]], key=lambda source: source["document_id"])
            expected = sorted(publication["sources"], key=lambda source: source["document_id"])
            if latest["digest"] != digest or latest["change_note"] != publication["change_note"].strip() or references != expected:
                raise RuntimeError("The latest saved canvas differs from the reviewed files. Check its history.")
            print(f"{saved['name']} · Version {latest['version']} · {len(files)} files\n{saved['record_url']}")
        finally:
            process.stdin.close()


if __name__ == "__main__":
    main()
