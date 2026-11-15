// luxuryphuket.net — static site (assets in dist/) + one endpoint: POST /api/enquiry.
// The enquiry form (thb-enquiry.js) posts JSON here; the request is emailed through Cloudflare Email
// Routing to the address in the LEAD_TO secret. If anything is missing or fails, the endpoint answers
// with an error and the form falls back to WhatsApp, so no request is lost.
//
// Cloudflare setup (dashboard):
//   1. luxuryphuket.net -> Email -> Email Routing: enable, add + verify the destination Gmail address.
//   2. Workers & Pages -> thaivillas -> Settings -> Variables and Secrets: secret LEAD_TO = that Gmail address.
import { EmailMessage } from "cloudflare:email";

const MAX_BODY = 20000;

function json(obj, status = 200) {
  return new Response(JSON.stringify(obj), { status, headers: { "content-type": "application/json" } });
}

function b64(str) {
  const bytes = new TextEncoder().encode(str);
  let bin = "";
  for (let i = 0; i < bytes.length; i += 0x8000) bin += String.fromCharCode(...bytes.subarray(i, i + 0x8000));
  return btoa(bin);
}

const oneLine = (v, n = 200) => String(v ?? "").replace(/[\r\n]+/g, " ").trim().slice(0, n);

const LABELS = {
  villa: "Listing", url: "Listing page", checkin: "Check-in", checkout: "Check-out", nights: "Nights",
  adults: "Adults", children: "Children", name: "Name", email: "Email", phone: "Phone", note: "Message", page: "Sent from",
};

async function enquiry(request, env) {
  if (request.method !== "POST") return json({ ok: false, error: "method" }, 405);
  if (!env.LEADS || !env.LEAD_TO) return json({ ok: false, error: "email not configured" }, 503);
  let p;
  try {
    const text = await request.text();
    if (text.length > MAX_BODY) throw new Error("too big");
    p = JSON.parse(text);
    if (!p || typeof p !== "object") throw new Error("bad");
  } catch {
    return json({ ok: false, error: "bad request" }, 400);
  }
  if (p.website) return json({ ok: true }); // honeypot field, if a form adds one
  if (!oneLine(p.name) && !oneLine(p.phone) && !oneLine(p.email)) return json({ ok: false, error: "empty" }, 400);

  const from = env.LEAD_FROM || "leads@luxuryphuket.net";
  const subject = `New request: ${oneLine(p.villa || "website", 90)} — ${oneLine(p.name, 60)}`;
  const lines = [];
  for (const [k, label] of Object.entries(LABELS)) {
    const v = p[k];
    if (v === undefined || v === null || v === "" || (k === "phone" && !String(v).replace(/^\+\d+\s*/, ""))) continue;
    lines.push(`${label}: ${k === "note" ? String(v).slice(0, 4000) : oneLine(v, 500)}`);
  }
  lines.push("", `Country (by IP): ${request.cf?.country || "?"}`, `Received: ${new Date().toISOString()}`);
  const email = oneLine(p.email, 120);
  const headers = [
    `From: Luxury Phuket website <${from}>`,
    `To: <${env.LEAD_TO}>`,
    /^[^\s@<>]+@[^\s@<>]+\.[^\s@<>]+$/.test(email) ? `Reply-To: <${email}>` : null,
    `Subject: =?UTF-8?B?${b64(subject)}?=`,
    `Message-ID: <${crypto.randomUUID()}@luxuryphuket.net>`,
    `Date: ${new Date().toUTCString()}`,
    "MIME-Version: 1.0",
    "Content-Type: text/plain; charset=UTF-8",
    "Content-Transfer-Encoding: base64",
  ].filter(Boolean);
  const raw = headers.join("\r\n") + "\r\n\r\n" + b64(lines.join("\r\n")).replace(/.{76}/g, "$&\r\n");
  try {
    await env.LEADS.send(new EmailMessage(from, env.LEAD_TO, raw));
    return json({ ok: true });
  } catch (e) {
    return json({ ok: false, error: "send failed" }, 502);
  }
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname === "/api/enquiry") return enquiry(request, env);
    return env.ASSETS.fetch(request);
  },
};
