"""Serve only a Canvas manifest's files on loopback for local visual review."""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit
import json
import mimetypes

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('directory', type=Path)
parser.add_argument('--port', type=int, default=8766)
args = parser.parse_args()
root = args.directory.resolve(strict=True)
paths = json.loads((root / 'canvas-files.json').read_text())
if not isinstance(paths, list) or not paths or 'gallery.html' not in paths:
    raise SystemExit('The manifest must list gallery.html and its supporting files.')
allowed = {}
for path in paths:
    if not isinstance(path, str):
        raise SystemExit('Manifest paths must be strings.')
    file = (root / path).resolve(strict=True)
    if not file.is_relative_to(root) or not file.is_file():
        raise SystemExit('Manifest paths must point to files inside the Canvas directory.')
    allowed['/' + path] = file

class Preview(BaseHTTPRequestHandler):
    def do_GET(self):
        path = unquote(urlsplit(self.path).path)
        file = allowed.get('/gallery.html' if path == '/' else path)
        if file is None:
            self.send_error(404, 'This preview serves only the Canvas bundle.')
            return
        data = file.read_bytes()
        self.send_response(200)
        self.send_header('Content-Type', mimetypes.guess_type(file.name)[0] or 'application/octet-stream')
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(data)

server = ThreadingHTTPServer(('127.0.0.1', args.port), Preview)
print(f'Local Canvas review: http://127.0.0.1:{args.port}/gallery.html', flush=True)
server.serve_forever()
