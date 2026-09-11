"""Small same-origin web server for the Tuhame investigation UI."""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from main import parse_request
from agent_loop import run
from schemas import to_jsonable


WEB_ROOT = Path(__file__).parent / "web"


class TuhameHandler(BaseHTTPRequestHandler):
    def _send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/api/health":
            self._send_json(200, {"status": "ok"})
            return
        if path in {"/", "/index.html"}:
            self._serve_file(WEB_ROOT / "index.html", "text/html; charset=utf-8")
            return
        if path.startswith("/assets/"):
            asset = WEB_ROOT / "assets" / path.removeprefix("/assets/")
            content_type = {".css": "text/css; charset=utf-8", ".js": "text/javascript; charset=utf-8"}.get(asset.suffix)
            if content_type and asset.is_file() and asset.resolve().parent == (WEB_ROOT / "assets").resolve():
                self._serve_file(asset, content_type)
                return
        self._send_json(404, {"error": "Not found"})

    def do_POST(self) -> None:  # noqa: N802
        if urlparse(self.path).path != "/api/search":
            self._send_json(404, {"error": "Not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length))
            request = str(payload.get("request", "")).strip()
            if not request:
                raise ValueError("Enter a property search before starting an investigation.")
            result = run(parse_request(request))
            self._send_json(200, {"result": to_jsonable(result)})
        except ValueError as error:
            self._send_json(400, {"error": str(error)})
        except Exception:
            self._send_json(502, {"error": "The listing sources could not be checked right now."})

    def _serve_file(self, path: Path, content_type: str) -> None:
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        return


RouteGuardHandler = TuhameHandler


def serve(host: str = "127.0.0.1", port: int = 8000) -> None:
    server = ThreadingHTTPServer((host, port), TuhameHandler)
    print(f"Tuhame web app: http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    serve()