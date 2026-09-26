// Signed-cookie session for the internal pages, shared by middleware.js and
// the api/auth/* functions. Web Crypto only, so the same file runs in the
// Edge middleware and in Node functions. The leading underscore keeps Vercel
// from treating this file as a route.

export const ALLOWED_DOMAIN = "emr-inc.net";
export const SESSION_COOKIE = "emr_internal";
export const STATE_COOKIE = "emr_oauth_state";
export const SESSION_SECONDS = 8 * 60 * 60;
export const DEFAULT_NEXT = "/internal/research";

const enc = new TextEncoder();

function toB64url(bytes) {
  let bin = "";
  for (const b of new Uint8Array(bytes)) bin += String.fromCharCode(b);
  return btoa(bin).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function fromB64url(s) {
  s = s.replace(/-/g, "+").replace(/_/g, "/");
  while (s.length % 4) s += "=";
  return Uint8Array.from(atob(s), (c) => c.charCodeAt(0));
}

function hmacKey(secret) {
  return crypto.subtle.importKey(
    "raw", enc.encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign", "verify"],
  );
}

export const now = () => Math.floor(Date.now() / 1000);

export async function sign(payload, secret) {
  const body = toB64url(enc.encode(JSON.stringify(payload)));
  const sig = await crypto.subtle.sign("HMAC", await hmacKey(secret), enc.encode(body));
  return `${body}.${toB64url(sig)}`;
}

// Returns the payload, or null for anything missing, forged, malformed or
// expired. With no secret configured nothing verifies, so a misconfigured
// deploy fails closed.
export async function verify(token, secret) {
  if (!token || !secret) return null;
  const [body, sig] = token.split(".");
  if (!body || !sig) return null;
  try {
    const ok = await crypto.subtle.verify(
      "HMAC", await hmacKey(secret), fromB64url(sig), enc.encode(body),
    );
    if (!ok) return null;
    const payload = JSON.parse(new TextDecoder().decode(fromB64url(body)));
    return typeof payload.exp === "number" && payload.exp > now() ? payload : null;
  } catch {
    return null;
  }
}

export function decodeJwtPayload(jwt) {
  return JSON.parse(new TextDecoder().decode(fromB64url(jwt.split(".")[1])));
}

export function getCookie(request, name) {
  for (const part of (request.headers.get("cookie") || "").split(/;\s*/)) {
    const i = part.indexOf("=");
    if (i > 0 && part.slice(0, i) === name) return decodeURIComponent(part.slice(i + 1));
  }
  return null;
}

// Only ever send people back into /internal/, never to another site.
export function safeNext(next) {
  return typeof next === "string" && /^\/internal(\/|$)/.test(next) ? next : DEFAULT_NEXT;
}

export function callbackUrl(request) {
  return `${new URL(request.url).origin}/api/auth/callback`;
}
