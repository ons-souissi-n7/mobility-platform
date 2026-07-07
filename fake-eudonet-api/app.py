import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

DATA_DIR = Path(__file__).resolve().parent / "data"


class FakeEudonetHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/health":
            self.respond({"status": "ok"})
            return

        if path == "/api/internships":
            self.respond(load_json("internships.json"))
            return

        self.respond({"detail": "Not found"}, status=404)

    def log_message(self, format, *args):
        return

    def respond(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def load_json(filename):
    with (DATA_DIR / filename).open(encoding="utf-8") as file:
        return json.load(file)


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", 8282), FakeEudonetHandler)
    server.serve_forever()
