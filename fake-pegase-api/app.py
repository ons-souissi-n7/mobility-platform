import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

DATA_DIR = Path(__file__).resolve().parent / "data"


class FakePegaseHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/health":
            self.respond({"status": "ok"})
            return

        if path in ("/departments", "/api/departments"):
            self.respond(load_json("departments.json"))
            return

        if path in ("/students", "/api/students"):
            self.respond(load_json("students.json"))
            return

        if path in ("/enrollments", "/api/enrollments"):
            self.respond(load_json("enrollments.json"))
            return

        if path in ("/inscriptions", "/api/inscriptions"):
            annee = parse_qs(urlparse(self.path).query).get("annee", [None])[0]
            filename = _inscriptions_filename(annee)
            self.respond(load_json(filename))
            return

        if path in ("/gpa-records", "/api/gpa-records"):
            self.respond(load_json("gpa_records.json"))
            return

        if path in ("/levels", "/api/levels"):
            self.respond(load_json("levels.json"))
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


def _inscriptions_filename(annee: str | None) -> str:
    """Retourne le fichier d'inscriptions correspondant à l'année donnée.

    Ex: annee="2025/2026" → "inscriptions_2025_2026.json"
    Si le fichier n'existe pas, retourne "inscriptions.json" (fallback).
    """
    if annee:
        slug = annee.replace("/", "_").replace("-", "_")
        specific = f"inscriptions_{slug}.json"
        if (DATA_DIR / specific).exists():
            return specific
    return "inscriptions.json"


def load_json(filename):
    with (DATA_DIR / filename).open(encoding="utf-8") as file:
        return json.load(file)


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", 8181), FakePegaseHandler)
    server.serve_forever()
