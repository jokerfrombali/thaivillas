// luxuryphuket.net — static site (assets in dist/) + one endpoint: POST /api/enquiry.
// The enquiry form (thb-enquiry.js) posts JSON here and the request is delivered to:
//   * Telegram — secrets TG_BOT_TOKEN (from @BotFather) and TG_CHAT_ID (one or more ids, comma-separated; "chat:topic" posts into a forum topic);
//   * email (optional) — Cloudflare Email Routing + secret LEAD_TO.
// If no channel is configured or every channel fails, the endpoint answers with an error and the form
// falls back to WhatsApp, so no request is lost.
// Secrets live in Cloudflare: Workers & Pages -> thaivillas -> Settings -> Variables and Secrets.
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

async function telegram(env, text) {
  const ids = String(env.TG_CHAT_ID).split(",").map((x) => x.trim()).filter(Boolean);
  let ok = 0;
  for (const id of ids) {
    // "chat_id:topic" sends into a forum topic, e.g. -1004370261657:3
    const [chat_id, topic] = id.split(":");
    const r = await fetch(`https://api.telegram.org/bot${env.TG_BOT_TOKEN}/sendMessage`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ chat_id, ...(topic ? { message_thread_id: Number(topic) } : {}), text: text.slice(0, 4000), disable_web_page_preview: true }),
    });
    if (r.ok) ok++;
  }
  return ok > 0;
}

async function enquiry(request, env) {
  if (request.method !== "POST") return json({ ok: false, error: "method" }, 405);
  const hasTg = !!(env.TG_BOT_TOKEN && env.TG_CHAT_ID);
  const hasMail = !!(env.LEADS && env.LEAD_TO);
  if (!hasTg && !hasMail) return json({ ok: false, error: "not configured" }, 503);
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

  let delivered = false;
  if (hasTg) {
    try {
      delivered = (await telegram(env, `🏝 ${subject}\n\n${lines.join("\n")}`)) || delivered;
    } catch {}
  }
  if (!hasMail) return delivered ? json({ ok: true }) : json({ ok: false, error: "send failed" }, 502);
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
    delivered = true;
  } catch {}
  return delivered ? json({ ok: true }) : json({ ok: false, error: "send failed" }, 502);
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname === "/api/enquiry") return enquiry(request, env);
    return env.ASSETS.fetch(request);
  },
};
