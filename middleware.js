// Gate for everything under /internal/. Runs before Vercel serves the static
// file, so the page is never sent to anyone without a valid session cookie.
// Sign-in itself lives in api/auth/.
import { SESSION_COOKIE, getCookie, verify } from "./api/_lib/session.mjs";

export const config = { matcher: ["/internal", "/internal/:path*"] };

export default async function middleware(request) {
  const session = await verify(getCookie(request, SESSION_COOKIE), process.env.SESSION_SECRET);
  if (session) {
    // Same as next() from @vercel/functions, without adding a dependency.
    return new Response(null, { headers: { "x-middleware-next": "1" } });
  }
  const url = new URL(request.url);
  const login = new URL("/api/auth/login", url);
  login.searchParams.set("next", url.pathname);
  return Response.redirect(login, 302);
}
