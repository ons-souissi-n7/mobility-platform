import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const PUBLIC_PATHS = ["/login", "/auth/callback"];

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
    return NextResponse.next();
  }

  // Always allow public paths
  if (PUBLIC_PATHS.some((p) => pathname.startsWith(p))) {
    return NextResponse.next();
  }

  const token = request.cookies.get("auth_token")?.value;

  if (!token) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("next", pathname);
    return NextResponse.redirect(loginUrl);
  }

  const payload = parseJwtPayload(token);

  // Token présent mais illisible (corrompu, format inattendu) — traiter comme
  // une absence de session plutôt que de laisser passer sans rôle connu.
  if (!payload) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("next", pathname);
    const response = NextResponse.redirect(loginUrl);
    response.cookies.delete("auth_token");
    return response;
  }

  // Expired token
  if (payload?.exp && payload.exp < Date.now() / 1000) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("next", pathname);
    const response = NextResponse.redirect(loginUrl);
    response.cookies.delete("auth_token");
    return response;
  }

  const role = payload?.role;

  // Root redirect based on role
  if (pathname === "/") {
    if (role === "student") {
      return NextResponse.redirect(
        new URL("/student/tableau-de-bord", request.url),
      );
    }
    return NextResponse.redirect(new URL("/admin/analytiques", request.url));
  }

  // Students cannot access admin routes
  if (role === "student" && pathname.startsWith("/admin")) {
    return NextResponse.redirect(
      new URL("/student/tableau-de-bord", request.url),
    );
  }

  return NextResponse.next();
}

export const config = {
  // Chaîne littérale, pas de tagged template : le pipeline de build de
  // Next.js analyse ce champ statiquement et ne sait pas évaluer un
  // String.raw`...` ("Unsupported node type TaggedTemplateExpression").
  matcher: ["/((?!api|_next/static|_next/image|favicon\\.ico).*)"],
};
