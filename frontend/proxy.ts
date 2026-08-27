import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const PUBLIC_PATHS = ["/login", "/auth/callback"];

// connect-src doit couvrir les trois façons dont le navigateur atteint l'API :
// même origine (prod/staging, Nginx route /api/* vers le backend), dev local
// (NEXT_PUBLIC_API_URL=http://localhost:8000), et le réseau Docker interne
// des tests E2E (docker-compose.test.yml pointe vers http://backend:8000).
//
// Next.js (App Router) injecte lui-même des <script> inline pour transporter
// les données d'hydratation (self.__next_f.push(...)) — un simple
// script-src 'self' les bloque et casse l'hydratation entièrement (React ne
// démarre jamais, aucun useEffect ne s'exécute). La solution officiellement
// documentée par Next.js est un nonce généré à chaque requête ici, dans le
// middleware, propagé à la fois vers la requête (pour que le rendu serveur
// l'utilise sur ses propres scripts) et vers la réponse (pour que le
// navigateur l'accepte). 'strict-dynamic' permet aux scripts chargés par un
// script nonce (chunks webpack) d'être eux-mêmes exécutés sans figurer
// explicitement dans script-src.
function buildCsp(nonce: string): string {
  const isProd = process.env.NODE_ENV === "production";
  return [
    "default-src 'self'",
    // 'unsafe-eval' : uniquement en dev — le devtool webpack de `next dev`
    // s'appuie sur eval() pour les source maps ; la build de production ne
    // l'utilise pas et reste strictement au nonce + strict-dynamic.
    isProd
      ? `script-src 'self' 'nonce-${nonce}' 'strict-dynamic'`
      : `script-src 'self' 'nonce-${nonce}' 'strict-dynamic' 'unsafe-eval'`,
    // 'unsafe-inline' requis par les styles inline générés par Recharts
    // (attribut style="" sur les éléments SVG) — un nonce ne s'applique pas
    // aux attributs, seulement aux éléments <style>/<script>.
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data: blob:",
    "font-src 'self' data:",
    "connect-src 'self' http://localhost:8000 http://backend:8000",
    "frame-ancestors 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "object-src 'none'",
  ].join("; ");
}

function withCsp(response: NextResponse): NextResponse {
  const nonce = Buffer.from(crypto.randomUUID()).toString("base64");
  const csp = buildCsp(nonce);
  response.headers.set("Content-Security-Policy", csp);
  response.headers.set("x-nonce", nonce);
  return response;
}

/**
 * Variante de NextResponse.next() qui propage aussi le nonce vers la requête
 * elle-même : c'est ce qui permet au rendu serveur de Next.js de savoir quel
 * nonce appliquer à SES propres scripts injectés (hydratation RSC).
 */
function nextWithCsp(request: NextRequest): NextResponse {
  const nonce = Buffer.from(crypto.randomUUID()).toString("base64");
  const csp = buildCsp(nonce);
  const requestHeaders = new Headers(request.headers);
  requestHeaders.set("x-nonce", nonce);
  requestHeaders.set("Content-Security-Policy", csp);
  const response = NextResponse.next({ request: { headers: requestHeaders } });
  response.headers.set("Content-Security-Policy", csp);
  response.headers.set("x-nonce", nonce);
  return response;
}

interface JwtPayload {
  role?: string;
  exp?: number;
}

function parseJwtPayload(token: string): JwtPayload | null {
  try {
    const payload = token.split(".")[1];
    if (!payload) return null;
    const decoded = atob(payload.replaceAll("-", "+").replaceAll("_", "/"));
    return JSON.parse(decoded) as JwtPayload;
  } catch {
    return null;
  }
}

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Filet de sécurité indépendant du matcher ci-dessous : sur cet environnement,
  // le matcher seul ne suffit pas toujours à exclure les assets internes
  // (observé : /_next/static/chunks/*.js redirigé vers /login, ce qui casse le
  // <script> correspondant côté navigateur — "Unexpected token '<'").
  if (
    pathname.startsWith("/_next/") ||
    pathname.startsWith("/api/") ||
    pathname === "/favicon.ico"
  ) {
    return nextWithCsp(request);
  }

  // Always allow public paths
  if (PUBLIC_PATHS.some((p) => pathname.startsWith(p))) {
    return nextWithCsp(request);
  }

  const token = request.cookies.get("auth_token")?.value;

  if (!token) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("next", pathname);
    return withCsp(NextResponse.redirect(loginUrl));
  }

  const payload = parseJwtPayload(token);

  // Token présent mais illisible (corrompu, format inattendu) — traiter comme
  // une absence de session plutôt que de laisser passer sans rôle connu.
  if (!payload) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("next", pathname);
    const response = withCsp(NextResponse.redirect(loginUrl));
    response.cookies.delete("auth_token");
    return response;
  }

  // Expired token
  if (payload?.exp && payload.exp < Date.now() / 1000) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("next", pathname);
    const response = withCsp(NextResponse.redirect(loginUrl));
    response.cookies.delete("auth_token");
    return response;
  }

  const role = payload?.role;

  // Rôle absent ou inattendu (ni "admin" ni "student") — traiter comme une
  // absence de session plutôt que de laisser passer sans zone d'appartenance
  // connue (ce qui reviendrait à laisser passer implicitement via next()).
  if (role !== "admin" && role !== "student") {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("next", pathname);
    const response = withCsp(NextResponse.redirect(loginUrl));
    response.cookies.delete("auth_token");
    return response;
  }

  const homePath = role === "student" ? "/student/tableau-de-bord" : "/admin/analytiques";

  // Root redirect based on role
  if (pathname === "/") {
    return withCsp(NextResponse.redirect(new URL(homePath, request.url)));
  }

  // Étanchéité stricte entre les deux zones : un rôle ne peut jamais accéder
  // à l'espace de l'autre, dans un sens comme dans l'autre.
  if (
    (role === "student" && pathname.startsWith("/admin")) ||
    (role === "admin" && pathname.startsWith("/student"))
  ) {
    return withCsp(NextResponse.redirect(new URL(homePath, request.url)));
  }

  return nextWithCsp(request);
}

export const config = {
  // Chaîne littérale, pas de tagged template : le pipeline de build de
  // Next.js analyse ce champ statiquement et ne sait pas évaluer un
  // String.raw`...` ("Unsupported node type TaggedTemplateExpression").
  matcher: ["/((?!api|_next/static|_next/image|favicon\\.ico).*)"], // NOSONAR (S7780)
};
