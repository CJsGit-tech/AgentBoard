"""Stream one local PNG through the configured AgentBoard stdio launcher."""
import argparse
import base64
import json
from pathlib import Path
import subprocess


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
    parser.add_argument("png", type=Path)
    parser.add_argument("inventory_url", help="Verified inventory URL from native MCP")
    args = parser.parse_args()
    if args.png.stat().st_size > 8 * 1024**2:
        parser.error("PNG exceeds 8 MiB.")
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
            "filename":args.png.name,"png_base64":base64.b64encode(args.png.read_bytes()).decode("ascii")}}})
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
