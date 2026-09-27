// Google sends people back here. Swap the code for an ID token, check the
// account is a verified @emr-inc.net Workspace user, then set the session.
import {
  ALLOWED_DOMAIN, SESSION_COOKIE, SESSION_SECONDS, STATE_COOKIE,
  callbackUrl, decodeJwtPayload, getCookie, now, sign, verify,
} from "../_lib/session.mjs";

function deny(message, status) {
  const headers = new Headers({ "Content-Type": "text/plain; charset=utf-8", "Cache-Control": "no-store" });
  headers.append("Set-Cookie", `${STATE_COOKIE}=; Path=/api/auth; HttpOnly; Secure; SameSite=Lax; Max-Age=0`);
  return new Response(`${message}\n\nBack to emr-inc.net: /`, { status, headers });
}

export async function GET(request) {
  const { GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, SESSION_SECRET } = process.env;
  if (!GOOGLE_CLIENT_ID || !GOOGLE_CLIENT_SECRET || !SESSION_SECRET) {
    return new Response("Internal sign-in is not configured yet.", { status: 500 });
  }

  const params = new URL(request.url).searchParams;
  const pending = await verify(getCookie(request, STATE_COOKIE), SESSION_SECRET);
  const code = params.get("code");
  if (!pending || !code || params.get("state") !== pending.state) {
    return deny("That sign-in link expired. Open the research page and try again.", 400);
  }

  const tokenRes = await fetch("https://oauth2.googleapis.com/token", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      code,
      client_id: GOOGLE_CLIENT_ID,
      client_secret: GOOGLE_CLIENT_SECRET,
      redirect_uri: callbackUrl(request),
      grant_type: "authorization_code",
    }),
  });
  if (!tokenRes.ok) return deny("Google sign-in failed. Try again.", 502);
  const { id_token } = await tokenRes.json();
  if (!id_token) return deny("Google sign-in failed. Try again.", 502);

  // This token came straight from Google's token endpoint over TLS, which
  // Google's OpenID docs accept in place of checking its signature. Every
  // claim that decides access is still checked.
  const c = decodeJwtPayload(id_token);
  const email = String(c.email || "").toLowerCase();
  const allowed =
    c.aud === GOOGLE_CLIENT_ID &&
    (c.iss === "https://accounts.google.com" || c.iss === "accounts.google.com") &&
    c.exp > now() &&
    c.email_verified === true &&
    c.hd === ALLOWED_DOMAIN &&
    email.endsWith(`@${ALLOWED_DOMAIN}`);
  if (!allowed) {
    return deny(`This page is for EMR Inc. staff. Sign in with an @${ALLOWED_DOMAIN} Google account.`, 403);
  }

  const session = await sign({ email, exp: now() + SESSION_SECONDS }, SESSION_SECRET);
  const headers = new Headers({ Location: pending.next, "Cache-Control": "no-store" });
  headers.append("Set-Cookie", `${SESSION_COOKIE}=${session}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=${SESSION_SECONDS}`);
  headers.append("Set-Cookie", `${STATE_COOKIE}=; Path=/api/auth; HttpOnly; Secure; SameSite=Lax; Max-Age=0`);
  return new Response(null, { status: 302, headers });
}
