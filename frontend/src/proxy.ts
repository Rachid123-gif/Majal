import { NextResponse, type NextRequest } from "next/server";

const BACKEND = process.env.BACKEND_INTERNAL_URL ?? "http://localhost:8000";
const SESSION_COOKIE = "majal_session";

/** Protected pages: the backend confirms the session before the page is rendered. */
export async function proxy(request: NextRequest) {
  const session = request.cookies.get(SESSION_COOKIE);
  if (session) {
    try {
      const response = await fetch(`${BACKEND}/api/auth/me`, {
        headers: { cookie: `${SESSION_COOKIE}=${session.value}` },
        cache: "no-store",
      });
      if (response.ok) return NextResponse.next();
    } catch {
      // Backend unreachable: treated as not logged in.
    }
  }
  const login = new URL("/connexion", request.url);
  login.searchParams.set("suite", request.nextUrl.pathname + request.nextUrl.search);
  return NextResponse.redirect(login);
}

export const config = {
  matcher: ["/tableau-de-bord/:path*", "/presentation/:path*", "/territoire/:path*"],
};
