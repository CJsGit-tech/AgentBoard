"""Convert one local image to a JPG copy and attach it through the configured AgentBoard stdio launcher.

The original file is left untouched; the JPG copy is written beside it (or to --out)."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import shutil
import subprocess


def to_jpeg(source, target, quality=85):
    """Write a genuine JPEG copy of source, flattening transparency onto white."""
    if source.read_bytes()[:3] == b"\xff\xd8\xff":
        if source.resolve() != target.resolve():
            shutil.copyfile(source, target)
        return target
    try:
        from PIL import Image
    except ImportError:
        if not shutil.which("sips"):
            raise SystemExit("Install Pillow (python3 -m pip install Pillow) to convert images to JPG.")
        subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", str(quality),
                        str(source), "--out", str(target)], check=True, capture_output=True)
    else:
        with Image.open(source) as image:
            image = image.convert("RGBA") if image.mode in ("P", "LA", "RGBA") else image
            if image.mode == "RGBA":
                background = Image.new("RGB", image.size, "white")
                background.paste(image, mask=image.getchannel("A"))
                image = background
            image.convert("RGB").save(target, format="JPEG", quality=quality, optimize=True)
    if target.read_bytes()[:3] != b"\xff\xd8\xff":
        raise SystemExit(f"Conversion did not produce a JPEG: {target}")
    return target


def request(process, message):
    process.stdin.write(json.dumps(message) + "\n")
    process.stdin.flush()
    if "id" not in message:
        return None
    for line in process.stdout:
        response = json.loads(line)
        if response.get("id") == message["id"]:
            if response.get("error"):
                raise RuntimeError(str(response["error"]))
            return response["result"]
    raise RuntimeError("AgentBoard closed the connection before replying.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("launcher", type=Path)
    parser.add_argument("client", choices=("Codex", "Claude"))
    parser.add_argument("document")
    parser.add_argument("revision", type=int)
    parser.add_argument("image", type=Path, help="JPG image (PNG uploads are blocked; convert to JPG first)")
    parser.add_argument("inventory_url", help="Verified inventory URL from native MCP")
    parser.add_argument("--out", type=Path, help="Where to write the JPG copy (default: beside the original)")
    parser.add_argument("--quality", type=int, default=85)
    args = parser.parse_args()
    if args.image.suffix.lower() == ".png" or args.image.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"):
        parser.error("PNG uploads are blocked. Convert to JPG format before uploading.")
    target = args.out or args.image.with_suffix(".jpg")
    if target.suffix.lower() not in (".jpg", ".jpeg"):
        parser.error("Use a .jpg filename for the uploaded image.")
    if target.resolve() == args.image.resolve() and args.image.read_bytes()[:3] != b"\xff\xd8\xff":
        parser.error("Choose --out so the original is not overwritten.")
    jpg = to_jpeg(args.image, target, args.quality)
    data = jpg.read_bytes()
    if len(data) > 8 * 1024**2:
        parser.error("JPG exceeds 8 MiB; lower --quality or resize.")
    print(json.dumps({"jpg": str(jpg), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}))
    process = subprocess.Popen([str(args.launcher.resolve()), args.client], stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE, text=True)
    try:
        request(process, {"jsonrpc":"2.0", "id":1, "method":"initialize", "params":{
            "protocolVersion":"2025-03-26","capabilities":{},
            "clientInfo":{"name":"agentbuild-visual","version":"1"}}})
        request(process, {"jsonrpc":"2.0","method":"notifications/initialized"})
        lookup = request(process, {"jsonrpc":"2.0","id":2,"method":"tools/call","params":{
            "name":"get_record","arguments":{"kind":"documents","id":args.document}}})
        target = lookup.get("structuredContent") or {}
        if lookup.get("isError") or target.get("record_url") != args.inventory_url or target.get("document_type") != "screen-inventory":
            raise RuntimeError("The launcher did not resolve the intended inventory URL. Check its instance settings.")
        result = request(process, {"jsonrpc":"2.0","id":3,"method":"tools/call","params":{
            "name":"attach_visual","arguments":{"document_id":args.document,"revision":args.revision,
            "filename":jpg.name,"image_base64":base64.b64encode(data).decode("ascii")}}})
        if result.get("isError"):
            raise RuntimeError(str(result["content"]))
        print(json.dumps(result.get("structuredContent") or result["content"], ensure_ascii=False))
    finally:
        process.stdin.close()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


if __name__ == "__main__":
    main()
