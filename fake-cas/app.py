import json
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, urlencode, urlparse

USERS_FILE = Path(__file__).resolve().parent / "users.json"

# In-memory ticket store: {ticket_id: {service, username, attributes}}
_tickets: dict[str, dict] = {}


def _load_users() -> list[dict]:
    with USERS_FILE.open(encoding="utf-8") as f:
        return json.load(f)


class CASHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)

        if parsed.path == "/health":
            self._json({"status": "ok"})

        elif parsed.path == "/cas/login":
            service = qs.get("service", [""])[0]
            self._html(_login_form(service))

        elif parsed.path in ("/cas/serviceValidate", "/cas/p3/serviceValidate"):
            service = qs.get("service", [""])[0]
            ticket = qs.get("ticket", [""])[0]
            _validate(self, ticket, service)

        elif parsed.path == "/cas/logout":
            target = qs.get("service", ["/"])[0]
            self._redirect(target)

        else:
            self._json({"detail": "Not found"}, 404)

    def do_POST(self):
        parsed = urlparse(self.path)
        length = int(self.headers.get("Content-Length", 0))
        body = parse_qs(self.rfile.read(length).decode("utf-8"))

        if parsed.path == "/cas/login":
            username = body.get("username", [""])[0]
            password = body.get("password", [""])[0]
            service = body.get("service", [""])[0]
            _handle_login(self, username, password, service)
        else:
            self._json({"detail": "Not found"}, 404)

    def _json(self, data: dict, status: int = 200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _html(self, content: str, status: int = 200):
        body = content.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _xml(self, content: str, status: int = 200):
        body = content.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/xml; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _redirect(self, url: str, status: int = 302):
        self.send_response(status)
        self.send_header("Location", url)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def log_message(self, format, *args):
        return


def _handle_login(handler: CASHandler, username: str, password: str, service: str):
    users = _load_users()
    user = next(
        (u for u in users if u["username"] == username and u["password"] == password),
        None,
    )
    if not user:
        handler._html(_login_form(service, error="Identifiants invalides"), 401)
        return

    ticket = f"ST-{uuid.uuid4().hex[:24]}"
    _tickets[ticket] = {
        "service": service,
        "username": username,
        "attributes": user["attributes"],
    }
    # CAS spec: append ticket to service URL preserving existing query params
    sep = "&" if "?" in service else "?"
    handler._redirect(f"{service}{sep}ticket={ticket}")


def _validate(handler: CASHandler, ticket: str, service: str):
    data = _tickets.pop(ticket, None)
    if not data or data["service"] != service:
        handler._xml(
            '<cas:serviceResponse xmlns:cas="http://www.yale.edu/tp/cas">'
            '<cas:authenticationFailure code="INVALID_TICKET">Ticket invalide ou expiré</cas:authenticationFailure>'
            "</cas:serviceResponse>"
        )
        return

    attrs = data["attributes"]
    attr_xml = "".join(
        f"<cas:{k}>{v}</cas:{k}>" for k, v in attrs.items() if v is not None
    )
    handler._xml(
        f'<cas:serviceResponse xmlns:cas="http://www.yale.edu/tp/cas">'
        f"<cas:authenticationSuccess>"
        f"<cas:user>{data['username']}</cas:user>"
        f"<cas:attributes>{attr_xml}</cas:attributes>"
        f"</cas:authenticationSuccess>"
        f"</cas:serviceResponse>"
    )


def _login_form(service: str, error: str = "") -> str:
    error_html = f'<p class="error">{error}</p>' if error else ""
    safe_service = service.replace('"', "&quot;")
    return f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Connexion — CAS ENSEEIHT (dev)</title>
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
       background:#f0f4f8;display:flex;justify-content:center;align-items:center;
       min-height:100vh}}
  .card{{background:#fff;border-radius:10px;padding:2.25rem;
         box-shadow:0 4px 16px rgba(0,0,0,.1);width:360px}}
  .badge{{display:inline-block;background:#fff3cd;color:#856404;border:1px solid #ffc107;
          font-size:.72rem;padding:.2rem .6rem;border-radius:4px;margin-bottom:1.25rem;
          font-weight:600;letter-spacing:.02em}}
  h1{{font-size:1.15rem;color:#1a2b4a;margin-bottom:1.5rem;font-weight:700}}
  label{{display:block;font-size:.82rem;color:#4a5568;margin-bottom:.3rem;margin-top:.9rem}}
  input{{width:100%;padding:.55rem .75rem;border:1px solid #cbd5e0;border-radius:6px;
         font-size:.88rem;outline:none;transition:border .2s}}
  input:focus{{border-color:#1a2b4a}}
  button{{width:100%;margin-top:1.4rem;padding:.7rem;background:#1a2b4a;color:#fff;
          border:none;border-radius:6px;font-size:.9rem;font-weight:600;cursor:pointer}}
  button:hover{{background:#243d65}}
  .error{{color:#c00;font-size:.83rem;margin-top:.9rem;padding:.5rem .75rem;
          background:#fff0f0;border-left:3px solid #c00;border-radius:4px}}
  details{{margin-top:1.5rem;font-size:.78rem;color:#718096}}
  summary{{cursor:pointer;user-select:none}}
  ul{{margin:.5rem 0 0 1.1rem;line-height:1.8}}
  code{{background:#f1f5f9;padding:.05rem .3rem;border-radius:3px;font-size:.88em}}
</style>
</head>
<body>
<div class="card">
  <span class="badge">⚠ Environnement de développement</span>
  <h1>Connexion CAS — ENSEEIHT</h1>
  {error_html}
  <form method="post" action="/cas/login">
    <input type="hidden" name="service" value="{safe_service}" />
    <label for="username">Identifiant (email N7)</label>
    <input id="username" name="username" type="text" autocomplete="username"
           placeholder="admin@n7.fr" />
    <label for="password">Mot de passe</label>
    <input id="password" name="password" type="password" autocomplete="current-password" />
    <button type="submit">Se connecter</button>
  </form>
  <details>
    <summary>Comptes de test disponibles</summary>
    <ul>
      <li><code>admin@n7.fr</code> / <code>admin123</code> — Administrateur RI</li>
      <li><code>etudiant@etud.n7.fr</code> / <code>etudiant123</code> — Étudiant (INE: 1234567890A)</li>
      <li><code>etudiant2@etud.n7.fr</code> / <code>etudiant123</code> — Étudiant (INE: 0987654321B)</li>
    </ul>
  </details>
</div>
</body>
</html>"""


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", 8380), CASHandler)
    server.serve_forever()
