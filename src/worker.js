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

// ---------- lead formatting (Russian, for the managers' Telegram topic) ----------
const SOURCES = [
  [/chatgpt|openai/i, "ChatGPT"], [/perplexity/i, "Perplexity"], [/gemini\.google|bard/i, "Gemini"],
  [/copilot|bing\.com\/chat/i, "Copilot"], [/claude\.ai/i, "Claude"], [/google\./i, "Google"],
  [/bing\./i, "Bing"], [/yandex|ya\.ru/i, "Яндекс"], [/duckduckgo/i, "DuckDuckGo"],
  [/instagram/i, "Instagram"], [/facebook|fb\.com|fb\.me/i, "Facebook"], [/t\.me|telegram/i, "Telegram"],
  [/youtube|youtu\.be/i, "YouTube"], [/tiktok/i, "TikTok"], [/whatsapp|wa\.me/i, "WhatsApp"],
];
const SEARCH = ["Google", "Bing", "Яндекс", "DuckDuckGo"];

function sourceOf(p) {
  const land = String(p.land || p.page || "");
  let utm = "", medium = "";
  try {
    const u = new URL(land);
    utm = u.searchParams.get("utm_source") || "";
    medium = u.searchParams.get("utm_medium") || "";
  } catch {}
  let refHost = "";
  try { refHost = p.ref ? new URL(String(p.ref)).hostname.replace(/^www\./, "") : ""; } catch {}
  if (/(^|\.)luxuryphuket\.net$/.test(refHost)) refHost = "";
  const probe = utm || refHost;
  if (!probe) return "Прямой заход / закладка";
  const hit = SOURCES.find(([re]) => re.test(probe));
  let name = hit ? hit[1] : probe;
  if (hit && SEARCH.includes(name) && !utm) name += " (поиск)";
  if (/cpc|ppc|paid/i.test(medium)) name += " · реклама";
  return utm ? `${name} · utm_source=${oneLine(utm, 60)}` : `${name} · ${refHost}`;
}

function countryRu(code) {
  try { return code ? new Intl.DisplayNames(["ru"], { type: "region" }).of(code) || code : ""; } catch { return code || ""; }
}
function place(cf) {
  if (!cf) return "";
  return [...new Set([cf.city, cf.region, countryRu(cf.country)].filter(Boolean))].join(", ");
}
function device(ua) {
  ua = String(ua || "");
  const type = /iPad|Tablet/i.test(ua) ? "планшет" : /Mobi|iPhone|Android/i.test(ua) ? "телефон" : "компьютер";
  const os = /iPhone|iPad|iOS/i.test(ua) ? "iOS" : /Android/i.test(ua) ? "Android" : /Windows/i.test(ua) ? "Windows"
    : /Mac OS X|Macintosh/i.test(ua) ? "macOS" : /Linux/i.test(ua) ? "Linux" : "";
  const br = /YaBrowser/i.test(ua) ? "Яндекс Браузер" : /Edg\//i.test(ua) ? "Edge" : /OPR\//i.test(ua) ? "Opera"
    : /SamsungBrowser/i.test(ua) ? "Samsung" : /Instagram/i.test(ua) ? "Instagram (встроенный)" : /FBAN|FBAV/i.test(ua) ? "Facebook (встроенный)"
    : /Chrome|CriOS/i.test(ua) ? "Chrome" : /Firefox|FxiOS/i.test(ua) ? "Firefox" : /Safari/i.test(ua) ? "Safari" : "";
  return [type, os, br].filter(Boolean).join(" · ");
}
function visitorBlock(request) {
  const cf = request.cf || {};
  const L = [];
  const pl = place(cf);
  if (pl) L.push(`📍 ${pl}`);
  const extra = [cf.postalCode ? `индекс ${cf.postalCode}` : "", cf.timezone ? `пояс ${cf.timezone}` : ""].filter(Boolean);
  if (extra.length) L.push(`🗺 ${extra.join(" · ")}`);
  if (cf.asOrganization) L.push(`🌐 Провайдер: ${oneLine(cf.asOrganization, 80)}`);
  const dev = device(request.headers.get("user-agent"));
  if (dev) L.push(`📱 ${dev}`);
  const lang = (request.headers.get("accept-language") || "").split(",")[0].trim();
  if (lang) L.push(`🗣 Язык браузера: ${oneLine(lang, 20)}`);
  return L;
}

function phuketTime() {
  const d = new Date(Date.now() + 7 * 3600 * 1000);
  const z = (n) => String(n).padStart(2, "0");
  return `${z(d.getUTCDate())}.${z(d.getUTCMonth() + 1)}.${d.getUTCFullYear()} ${z(d.getUTCHours())}:${z(d.getUTCMinutes())}`;
}

function guestsLine(p) {
  if (Number(p.adults)) return `${p.adults} взр.` + (Number(p.children) ? ` + ${p.children} дет.` : "");
  return p.guests ? `${oneLine(p.guests, 20)} гост.` : "";
}

function leadText(p, request, kind) {
  const L = [`🏝 Заявка · ${kind}`, `🕒 ${phuketTime()} (Пхукет)`, ""];
  if (oneLine(p.villa)) L.push(`🏠 ${oneLine(p.villa, 200)}`);
  if (oneLine(p.checkin)) {
    const n = Number(p.nights) ? ` · ${p.nights} ноч.` : "";
    L.push(`📅 ${oneLine(p.checkin, 40)} → ${oneLine(p.checkout, 40)}${n}`);
  }
  const g = guestsLine(p);
  if (g) L.push(`👥 ${g}`);
  if (oneLine(p.name)) L.push(`👤 ${oneLine(p.name, 120)}`);
  const phone = oneLine(p.phone, 60);
  if (phone && phone.replace(/^\+\d+\s*/, "")) L.push(`📞 ${phone}`);
  if (oneLine(p.email)) L.push(`✉️ ${oneLine(p.email, 120)}`);
  const msg = String(p.note || p.text || "").trim();
  if (msg) L.push("", "💬 Текст обращения:", msg.slice(0, 2500));
  L.push("", `🔎 Источник: ${sourceOf(p)}`);
  if (oneLine(p.page)) L.push(`🔗 ${oneLine(p.page, 400)}`);
  L.push(...visitorBlock(request));
  return L.join("\n");
}

async function readJson(request) {
  const text = await request.text();
  if (text.length > MAX_BODY) throw new Error("too big");
  const p = JSON.parse(text);
  if (!p || typeof p !== "object") throw new Error("bad");
  return p;
}

// WhatsApp click from thb-bot.js: the guest is about to message us; log it as a lead.
async function waLead(request, env) {
  if (request.method !== "POST") return json({ ok: false }, 405);
  if (!(env.TG_BOT_TOKEN && env.TG_CHAT_ID)) return json({ ok: false, error: "not configured" }, 503);
  let p;
  try { p = await readJson(request); } catch { return json({ ok: false }, 400); }
  try { await telegram(env, leadText(p, request, "WhatsApp")); } catch {}
  return json({ ok: true });
}

async function enquiry(request, env) {
  if (request.method !== "POST") return json({ ok: false, error: "method" }, 405);
  const hasTg = !!(env.TG_BOT_TOKEN && env.TG_CHAT_ID);
  const hasMail = !!(env.LEADS && env.LEAD_TO);
  if (!hasTg && !hasMail) return json({ ok: false, error: "not configured" }, 503);
  let p;
  try { p = await readJson(request); } catch { return json({ ok: false, error: "bad request" }, 400); }
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
  lines.push("", `Source: ${sourceOf(p)}`, `Location: ${place(request.cf) || "?"}`, `Received: ${new Date().toISOString()}`);

  let delivered = false;
  if (hasTg) {
    try {
      delivered = (await telegram(env, leadText(p, request, "Форма бронирования"))) || delivered;
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
    if (url.pathname === "/api/lead") return waLead(request, env);
    // thb-bot.js also pings these; accepted and dropped so the script stays on
    if (url.pathname === "/api/hit" || url.pathname === "/api/alert") return new Response(null, { status: 204 });
    return env.ASSETS.fetch(request);
  },
};
