// Zoho Mail (hello@luxuryphuket.net) <-> Telegram topic "Почта".
//
// * Every minute (cron) new inbox messages are posted to TG_MAIL_CHAT ("chat_id:topic").
// * A Telegram reply (Reply) to such a post is sent back to the sender from hello@luxuryphuket.net.
//
// Secrets (Cloudflare -> thaivillas -> Settings): ZOHO_CLIENT_ID, ZOHO_CLIENT_SECRET (Zoho API console,
// "Server-based application", redirect https://luxuryphuket.net/api/zoho/callback), TG_BOT_TOKEN, TG_MAIL_CHAT.
// Connect once: open https://luxuryphuket.net/api/zoho/connect and approve; the refresh token is kept in KV (STATE).

const ACCOUNTS = "https://accounts.zoho.com";
const API = "https://mail.zoho.com/api";
const REDIRECT = "https://luxuryphuket.net/api/zoho/callback";
const SCOPES = "ZohoMail.messages.ALL,ZohoMail.accounts.READ,ZohoMail.folders.READ";
const DOMAIN = "@luxuryphuket.net";
const WEBHOOK_VERSION = "1";

const html = (body, status = 200) =>
  new Response(`<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width">` +
    `<body style="font:16px system-ui;max-width:560px;margin:40px auto;padding:0 16px">${body}</body>`,
    { status, headers: { "content-type": "text/html; charset=utf-8" } });

function phuketTime(ms) {
  const d = new Date(Number(ms || Date.now()) + 7 * 3600 * 1000);
  const z = (n) => String(n).padStart(2, "0");
  return `${z(d.getUTCDate())}.${z(d.getUTCMonth() + 1)}.${d.getUTCFullYear()} ${z(d.getUTCHours())}:${z(d.getUTCMinutes())}`;
}

function htmlToText(h) {
  return String(h || "")
    .replace(/<(style|script|head)[^>]*>[\s\S]*?<\/\1>/gi, "")
    .replace(/<br\s*\/?>/gi, "\n").replace(/<\/(p|div|tr|li|h\d|blockquote)>/gi, "\n")
    .replace(/<[^>]+>/g, "")
    .replace(/&nbsp;/g, " ").replace(/&amp;/g, "&").replace(/&lt;/g, "<").replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"').replace(/&#39;|&apos;/g, "'")
    .replace(/[ \t]+\n/g, "\n").replace(/\n{3,}/g, "\n\n").trim();
}

const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

// ---------------- Telegram ----------------
async function tg(env, method, body) {
  const r = await fetch(`https://api.telegram.org/bot${env.TG_BOT_TOKEN}/${method}`, {
    method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body),
  });
  return r.json().catch(() => ({ ok: false }));
}
function mailChat(env) {
  const [chat_id, topic] = String(env.TG_MAIL_CHAT || "").split(":");
  return { chat_id, ...(topic ? { message_thread_id: Number(topic) } : {}) };
}
async function webhookSecret(env) {
  const d = await crypto.subtle.digest("SHA-256", new TextEncoder().encode("lp-webhook:" + env.TG_BOT_TOKEN));
  return [...new Uint8Array(d)].slice(0, 16).map((b) => b.toString(16).padStart(2, "0")).join("");
}

// ---------------- Zoho OAuth ----------------
export async function zohoConnect(request, env) {
  if (!env.ZOHO_CLIENT_ID || !env.ZOHO_CLIENT_SECRET) return html("Сначала добавьте ZOHO_CLIENT_ID и ZOHO_CLIENT_SECRET в Cloudflare.", 503);
  if (await env.STATE.get("zoho_refresh")) return html("Почта уже подключена ✅. Чтобы подключить заново, удалите ключ <b>zoho_refresh</b> в KV.");
  const state = crypto.randomUUID();
  await env.STATE.put("zoho_state:" + state, "1", { expirationTtl: 600 });
  const u = new URL(ACCOUNTS + "/oauth/v2/auth");
  u.search = new URLSearchParams({
    scope: SCOPES, client_id: env.ZOHO_CLIENT_ID, response_type: "code",
    access_type: "offline", prompt: "consent", redirect_uri: REDIRECT, state,
  });
  return Response.redirect(u.toString(), 302);
}

export async function zohoCallback(request, env) {
  const q = new URL(request.url).searchParams;
  const state = q.get("state") || "";
  if (!state || !(await env.STATE.get("zoho_state:" + state))) return html("Ссылка устарела. Откройте /api/zoho/connect ещё раз.", 400);
  await env.STATE.delete("zoho_state:" + state);
  if (q.get("error")) return html("Zoho вернул ошибку: " + esc(q.get("error")), 400);
  const r = await fetch(ACCOUNTS + "/oauth/v2/token", {
    method: "POST",
    body: new URLSearchParams({
      code: q.get("code") || "", grant_type: "authorization_code",
      client_id: env.ZOHO_CLIENT_ID, client_secret: env.ZOHO_CLIENT_SECRET, redirect_uri: REDIRECT,
    }),
  });
  const t = await r.json().catch(() => ({}));
  if (!t.refresh_token) return html("Не получилось получить доступ: " + esc(t.error || r.status), 400);
  await env.STATE.put("zoho_access", t.access_token, { expirationTtl: 3000 });
  // which mailbox? must be ours
  const acc = await zohoGet(env, "/accounts", t.access_token);
  const a = (acc.data || []).find((x) => String(x.primaryEmailAddress || x.mailboxAddress || "").endsWith(DOMAIN)) || (acc.data || [])[0];
  if (!a) return html("Доступ получен, но Zoho не отдал ящик через API (ответ: " + esc(JSON.stringify(acc).slice(0, 300)) + "). Возможно, API недоступен на бесплатном тарифе.", 400);
  const email = a.primaryEmailAddress || a.mailboxAddress || "";
  if (!email.endsWith(DOMAIN)) return html("Подключён чужой ящик (" + esc(email) + "). Войдите в Zoho как hello" + DOMAIN + ".", 400);
  await env.STATE.put("zoho_refresh", t.refresh_token);
  await env.STATE.put("zoho_account", JSON.stringify({ id: a.accountId, email }));
  await env.STATE.put("mail_since", String(Date.now()));
  await ensureWebhook(env, true);
  if (env.TG_MAIL_CHAT) await tg(env, "sendMessage", { ...mailChat(env), text: `✅ Почта ${email} подключена. Новые письма будут приходить сюда, ответ — через «Ответить» на сообщение бота.` });
  return html(`Готово ✅ Почта <b>${esc(email)}</b> подключена к Telegram.`);
}

async function accessToken(env) {
  const cached = await env.STATE.get("zoho_access");
  if (cached) return cached;
  const refresh = await env.STATE.get("zoho_refresh");
  if (!refresh) return null;
  const r = await fetch(ACCOUNTS + "/oauth/v2/token", {
    method: "POST",
    body: new URLSearchParams({
      refresh_token: refresh, grant_type: "refresh_token",
      client_id: env.ZOHO_CLIENT_ID, client_secret: env.ZOHO_CLIENT_SECRET,
    }),
  });
  const t = await r.json().catch(() => ({}));
  if (!t.access_token) return null;
  await env.STATE.put("zoho_access", t.access_token, { expirationTtl: Math.max(300, (t.expires_in || 3600) - 300) });
  return t.access_token;
}

async function zohoGet(env, path, token) {
  token = token || (await accessToken(env));
  const r = await fetch(API + path, { headers: { Authorization: "Zoho-oauthtoken " + token } });
  const t = await r.text();
  try { return JSON.parse(t.replace(/([:\[,]\s*)(\d{16,})(?=\s*[,\]}])/g, '$1"$2"')); } catch { return { status: { code: r.status } }; }
}

// ---------------- inbox -> Telegram (cron) ----------------
export async function pollMail(env) {
  if (!env.TG_BOT_TOKEN || !env.TG_MAIL_CHAT || !env.STATE) return;
  await ensureWebhook(env);
  const acc = JSON.parse((await env.STATE.get("zoho_account")) || "null");
  if (!acc) return;
  const since = Number((await env.STATE.get("mail_since")) || Date.now());
  const list = await zohoGet(env, `/accounts/${acc.id}/messages/view?limit=25&sortorder=false`);
  const msgs = (list.data || []).filter((m) => Number(m.receivedTime) > since).sort((a, b) => a.receivedTime - b.receivedTime);
  let newest = since;
  for (const m of msgs) {
    const from = m.fromAddress || "";
    if (from.toLowerCase() === acc.email.toLowerCase()) { newest = Math.max(newest, Number(m.receivedTime)); continue; }
    const c = await zohoGet(env, `/accounts/${acc.id}/folders/${m.folderId}/messages/${m.messageId}/content`);
    let body = htmlToText(c.data?.content || m.summary || "");
    if (body.length > 3000) body = body.slice(0, 3000) + "\n…(обрезано, полностью — в Zoho Mail)";
    const name = htmlToText(m.sender || "");
    const head =
      `📧 Письмо на ${acc.email}\n` +
      `🕒 ${phuketTime(m.receivedTime)} (Пхукет)\n\n` +
      `👤 ${name && name !== from ? name + " <" + from + ">" : from}\n` +
      `📝 ${htmlToText(m.subject || "(без темы)")}` +
      (m.hasAttachment === "1" || m.hasAttachment === true ? "\n📎 Есть вложения — смотрите в Zoho Mail" : "");
    const text = `${head}\n\n${body}\n\n↩️ Чтобы ответить клиенту — нажмите «Ответить» на это сообщение и напишите текст.`;
    const sent = await tg(env, "sendMessage", { ...mailChat(env), text: text.slice(0, 4090), disable_web_page_preview: true });
    if (sent.ok) {
      await env.STATE.put("tgmail:" + sent.result.message_id,
        JSON.stringify({ id: m.messageId, folder: m.folderId, from, subject: m.subject || "" }),
        { expirationTtl: 60 * 60 * 24 * 60 });
      newest = Math.max(newest, Number(m.receivedTime));
    } else break; // retry next minute
  }
  if (newest > since) await env.STATE.put("mail_since", String(newest));
}

async function ensureWebhook(env, force) {
  if (!force && (await env.STATE.get("tg_webhook")) === WEBHOOK_VERSION) return;
  const r = await tg(env, "setWebhook", {
    url: "https://luxuryphuket.net/api/tg/webhook",
    secret_token: await webhookSecret(env),
    allowed_updates: ["message"],
  });
  if (r.ok) await env.STATE.put("tg_webhook", WEBHOOK_VERSION);
}

// ---------------- Telegram reply -> email ----------------
export async function tgWebhook(request, env) {
  if (request.headers.get("x-telegram-bot-api-secret-token") !== (await webhookSecret(env))) return new Response("no", { status: 403 });
  const u = await request.json().catch(() => ({}));
  const msg = u.message;
  const ok = () => new Response("ok");
  await env.STATE.put("bridge_error", "last update " + new Date().toISOString() + ": chat " + (msg && msg.chat && msg.chat.id) +
    ", reply_to " + (msg && msg.reply_to_message && msg.reply_to_message.message_id) + ", text " + !!(msg && msg.text), { expirationTtl: 86400 });
  if (!msg || !msg.reply_to_message || !msg.text) return ok();
  const { chat_id } = mailChat(env);
  if (String(msg.chat.id) !== String(chat_id)) return ok();
  const ref = JSON.parse((await env.STATE.get("tgmail:" + msg.reply_to_message.message_id)) || "null");
  if (!ref) {
    await env.STATE.put("bridge_error", "no mail mapped to tg message " + msg.reply_to_message.message_id, { expirationTtl: 86400 });
    if (msg.reply_to_message.from && msg.reply_to_message.from.is_bot)
      await tg(env, "sendMessage", { chat_id: msg.chat.id, message_thread_id: msg.message_thread_id, reply_to_message_id: msg.message_id,
        text: String(msg.reply_to_message.text || "").startsWith("📧")
          ? "⏳ Письмо только что пришло, бот ещё не готов на него ответить. Подождите минуту и нажмите «Ответить» ещё раз."
          : "ℹ️ Это не письмо. Чтобы ответить клиенту, нажмите «Ответить» на сообщение бота, которое начинается с «📧 Письмо»." });
    return ok();
  }
  const acc = JSON.parse((await env.STATE.get("zoho_account")) || "null");
  const token = acc && (await accessToken(env));
  const reply = (text) => tg(env, "sendMessage", { chat_id: msg.chat.id, message_thread_id: msg.message_thread_id, reply_to_message_id: msg.message_id, text });
  if (!token) { await reply("❌ Почта не подключена к боту — ответ не отправлен."); return ok(); }
  const subject = /^re:/i.test(ref.subject) ? ref.subject : "Re: " + ref.subject;
  const r = await fetch(`${API}/accounts/${acc.id}/messages/${ref.id}`, {
    method: "POST",
    headers: { Authorization: "Zoho-oauthtoken " + token, "content-type": "application/json" },
    body: JSON.stringify({
      fromAddress: acc.email, toAddress: ref.from, action: "reply", subject,
      content: msg.text, mailFormat: "plaintext",
    }),
  });
  const res = await r.json().catch(() => ({}));
  await env.STATE.put("bridge_error", "zoho send " + r.status + " " + JSON.stringify(res).slice(0, 400), { expirationTtl: 86400 });
  if (r.ok && (res.status?.code ?? 200) < 300) await reply(`✅ Ответ отправлен на ${ref.from}`);
  else { await env.STATE.put("bridge_error", "zoho send " + r.status + " " + JSON.stringify(res).slice(0, 400), { expirationTtl: 86400 }); }
  if (!(r.ok && (res.status?.code ?? 200) < 300)) await reply(`❌ Не отправилось (${res.status?.code || r.status}: ${res.data?.errorCode || res.status?.description || ""}). Ответьте из Zoho Mail.`);
  return ok();
}

// Diagnostics without secrets: Telegram webhook state + last bridge error.
export async function bridgeStatus(env) {
  const info = await tg(env, "getWebhookInfo", {});
  const w = info.result || {};
  const out = {
    webhook_set: !!w.url, webhook_url_ok: w.url === "https://luxuryphuket.net/api/tg/webhook",
    pending: w.pending_update_count, last_error: w.last_error_message || null,
    last_error_at: w.last_error_date ? new Date(w.last_error_date * 1000).toISOString() : null,
    allowed_updates: w.allowed_updates || null,
    mail_connected: !!(await env.STATE.get("zoho_account")),
    last_bridge_error: await env.STATE.get("bridge_error"),
    mapped_tg_messages: (await env.STATE.list({ prefix: "tgmail:" })).keys.map((k) => k.name),
    mail_since: await env.STATE.get("mail_since"),
  };
  return new Response(JSON.stringify(out, null, 1), { headers: { "content-type": "application/json" } });
}
