// Starts Google sign-in. `hd` only pre-selects the emr-inc.net account in
// Google's picker; the domain is actually enforced in callback.mjs.
import { ALLOWED_DOMAIN, STATE_COOKIE, callbackUrl, now, safeNext, sign } from "../_lib/session.mjs";

export async function GET(request) {
  const { GOOGLE_CLIENT_ID, SESSION_SECRET } = process.env;
  if (!GOOGLE_CLIENT_ID || !SESSION_SECRET) {
    return new Response("Internal sign-in is not configured yet.", { status: 500 });
  }

  const state = crypto.randomUUID();
  const next = safeNext(new URL(request.url).searchParams.get("next"));

  const auth = new URL("https://accounts.google.com/o/oauth2/v2/auth");
  auth.search = new URLSearchParams({
    client_id: GOOGLE_CLIENT_ID,
    redirect_uri: callbackUrl(request),
    response_type: "code",
    scope: "openid email",
    hd: ALLOWED_DOMAIN,
    prompt: "select_account",
    state,
  }).toString();

  const stateToken = await sign({ state, next, exp: now() + 600 }, SESSION_SECRET);
  return new Response(null, {
    status: 302,
    headers: {
      Location: auth.toString(),
      "Set-Cookie": `${STATE_COOKIE}=${stateToken}; Path=/api/auth; HttpOnly; Secure; SameSite=Lax; Max-Age=600`,
      "Cache-Control": "no-store",
    },
  });
}
