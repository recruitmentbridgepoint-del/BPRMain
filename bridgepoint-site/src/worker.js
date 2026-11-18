// Bridgepoint Recruitment — Cloudflare Worker
// Serves the static site from /public, redirects old Wix URLs, and emails form submissions.

import redirects from "./redirects.json";

const TO = "info@bridgepointrecruitment.com";       // where every form is delivered
const FROM = "website@bridgepointrecruitment.com";  // sender; domain must be set up in Cloudflare Email
const MAX_FILE = 4 * 1024 * 1024;                   // keeps uploads small; Resend allows up to 40MB per email

// Base64-encode an ArrayBuffer (Resend expects attachment content as a Base64 string)
function toBase64(buf) {
  const bytes = new Uint8Array(buf);
  let bin = "";
  for (let i = 0; i < bytes.length; i += 0x8000) bin += String.fromCharCode.apply(null, bytes.subarray(i, i + 0x8000));
  return btoa(bin);
}

// Send through Resend (https://resend.com). The API key is stored as a secret named RESEND_API_KEY.
async function sendEmail(env, m) {
  const body = {
    from: `${m.from.name} <${m.from.email}>`,
    to: [m.to],
    subject: m.subject,
    html: m.html,
    text: m.text,
  };
  if (m.replyTo) body.reply_to = m.replyTo;
  if (m.attachments) body.attachments = m.attachments.map((a) => ({ filename: a.filename, content: toBase64(a.content) }));
  const res = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: { Authorization: `Bearer ${env.RESEND_API_KEY}`, "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`Resend ${res.status}: ${await res.text()}`);
}

const FORMS = {
  "/api/brief": {
    subject: (f) => `New role brief: ${f.get("role") || "Untitled"} (${f.get("company") || ""})`,
    required: ["name", "company", "email", "role"],
    fields: [["Name", "name"], ["Company", "company"], ["Email", "email"], ["Phone", "phone"], ["Role title", "role"],
             ["Hiring type", "hiring_type"], ["Roles to fill", "roles"], ["Location", "location"], ["Notes", "message"]],
    thanks: "brief",
  },
  "/api/apply": {
    subject: (f) => `Application: ${f.get("job_title") || ""} [${f.get("job_ref") || ""}] from ${f.get("name") || ""}`,
    required: ["name", "email", "phone"],
    fields: [["Role", "job_title"], ["Reference", "job_ref"], ["Name", "name"], ["Email", "email"], ["Phone", "phone"], ["Cover note", "message"]],
    file: "resume",
    thanks: "apply",
  },
  "/api/register": {
    subject: (f) => `Resume registration: ${f.get("name") || ""} (${f.get("sector") || ""})`,
    required: ["name", "email", "phone"],
    fields: [["Name", "name"], ["Email", "email"], ["Phone", "phone"], ["Area of work", "sector"], ["Work type", "work_type"]],
    file: "resume",
    thanks: "register",
  },
};

const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const back = (url, q) => Response.redirect(new URL(`/thanks/?${q}`, url).toString(), 303);

async function handleForm(request, env, form) {
  if (request.method !== "POST") return new Response("Method not allowed", { status: 405 });
  let data;
  try { data = await request.formData(); } catch { return back(request.url, "error=1"); }

  // Honeypot: real visitors never fill this hidden field
  if (data.get("website")) return back(request.url, `f=${form.thanks}`);

  for (const k of form.required) if (!String(data.get(k) || "").trim()) return back(request.url, `error=1&f=${form.thanks}`);

  const rows = form.fields.map(([label, key]) => [label, String(data.get(key) || "").trim()]).filter(([, v]) => v);
  const text = rows.map(([l, v]) => `${l}: ${v}`).join("\n");
  const html = `<table style="font-family:Arial,sans-serif;font-size:14px;border-collapse:collapse">${rows
    .map(([l, v]) => `<tr><td style="padding:6px 14px 6px 0;color:#5d6b72;vertical-align:top">${esc(l)}</td><td style="padding:6px 0">${esc(v).replace(/\n/g, "<br>")}</td></tr>`)
    .join("")}</table>`;

  const message = {
    to: TO,
    from: { email: FROM, name: "Bridgepoint website" },
    replyTo: String(data.get("email") || "").trim() || undefined,
    subject: form.subject(data),
    text,
    html,
  };

  if (form.file) {
    const file = data.get(form.file);
    if (!file || typeof file === "string" || file.size === 0) return back(request.url, `error=1&f=${form.thanks}`);
    if (file.size > MAX_FILE) return back(request.url, `error=size&f=${form.thanks}`);
    const ok = /\.(pdf|doc|docx)$/i.test(file.name);
    if (!ok) return back(request.url, `error=type&f=${form.thanks}`);
    message.attachments = [{ content: await file.arrayBuffer(), filename: file.name, type: file.type || "application/octet-stream", disposition: "attachment" }];
  }

  try {
    await sendEmail(env, message);
  } catch (err) {
    console.error("Email send failed", err);
    return back(request.url, `error=send&f=${form.thanks}`);
  }
  return back(request.url, `f=${form.thanks}`);
}

// ---------- Staff onboarding ----------
// Submissions are stored in the ONBOARDING KV namespace (encrypted at rest by Cloudflare), never emailed.
// Secrets required (Cloudflare > Worker > Settings > Variables and Secrets):
//   ONBOARD_CODE   — code given to new starters; the form is rejected without it
//   ADMIN_PASSWORD — password for /staff-admin, where submissions are viewed
const DOC_MAX = 8 * 1024 * 1024;
const DOC_OK = /\.(pdf|jpe?g|png|heic)$/i;
const OB_FIELDS = [
  ["Personal details", [["Given name(s)", "given_names"], ["Surname", "surname"], ["Preferred name", "preferred_name"], ["Mobile", "mobile"], ["Email", "email"]]],
  ["Emergency contact", [["Name", "ec_name"], ["Relationship", "ec_relationship"], ["Phone", "ec_phone"]]],
  ["Right to work", [["Status", "work_status"], ["Passport number", "passport_no"], ["Passport country", "passport_country"],
    ["Visa subclass", "visa_subclass"], ["Visa expiry", "visa_expiry"], ["VEVO check consent", "vevo_consent"]]],
  ["Work details", [["Days available", "days"], ["Availability notes", "availability_notes"], ["Transport", "transport"], ["Driver licence", "driver_licence"],
    ["Other licences / tickets", "licences"], ["Boot size", "boot_size"], ["Shirt size", "shirt_size"], ["Adjustments", "adjustments"]]],
  ["Declarations", [["Received Fair Work Information Statement", "ack_fwis"], ["Received Casual Employment Information Statement", "ack_ceis"],
    ["Privacy notice accepted", "ack_privacy"], ["Information true and correct", "ack_true"], ["Signature (typed name)", "signature"]]],
];
const OB_REQUIRED = ["given_names", "surname", "mobile", "email", "ec_name", "ec_relationship", "ec_phone",
  "work_status", "transport", "driver_licence", "boot_size", "shirt_size",
  "ack_fwis", "ack_ceis", "ack_privacy", "ack_true", "signature"];

async function same(a, b) {
  const e = new TextEncoder();
  const [x, y] = await Promise.all([crypto.subtle.digest("SHA-256", e.encode(a)), crypto.subtle.digest("SHA-256", e.encode(b))]);
  return crypto.subtle.timingSafeEqual(x, y);
}

async function handleOnboarding(request, env) {
  if (request.method !== "POST") return new Response("Method not allowed", { status: 405 });
  const isFetch = request.headers.get("X-Requested-With") === "fetch";
  const reply = (error) => isFetch
    ? new Response(JSON.stringify(error ? { ok: false, error } : { ok: true }), { headers: { "Content-Type": "application/json", "Cache-Control": "no-store" } })
    : back(request.url, error ? `error=${error}&f=onboard` : "f=onboard");

  if (!env.ONBOARDING || !env.ONBOARD_CODE) return reply("closed");
  let data;
  try { data = await request.formData(); } catch { return reply("missing"); }
  if (data.get("website")) return reply(null);
  if (!(await same(String(data.get("code") || "").trim(), env.ONBOARD_CODE))) return reply("code");

  const val = (k) => data.getAll(k).map((v) => String(v).trim()).filter(Boolean).join(", ");
  const req = [...OB_REQUIRED];
  if (val("work_status") === "Visa holder") req.push("passport_no", "passport_country", "visa_subclass", "visa_expiry", "vevo_consent");
  for (const k of req) if (!val(k)) return reply("missing");

  const files = [["Photo ID", "id_doc", true]];
  const docs = [];
  for (const [label, key, needed] of files) {
    const f = data.get(key);
    const has = f && typeof f !== "string" && f.size > 0;
    if (!has) { if (needed) return reply("missing"); continue; }
    if (f.size > DOC_MAX) return reply("docsize");
    if (!DOC_OK.test(f.name)) return reply("doctype");
    docs.push({ label, key, name: f.name, type: f.type || "application/octet-stream", body: await f.arrayBuffer() });
  }

  const name = `${val("given_names")} ${val("surname")}`;
  const id = `${new Date().toISOString().replace(/[:.]/g, "-")}_${name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "")}`;
  const record = {
    id, name, submitted: new Date().toISOString(),
    sections: OB_FIELDS.map(([title, rows]) => [title, rows.map(([l, k]) => [l, val(k)]).filter(([, v]) => v)]).filter(([, rows]) => rows.length),
    files: docs.map(({ label, key, name, type }) => ({ label, key, name, type })),
  };
  try {
    for (const d of docs) await env.ONBOARDING.put(`file:${id}:${d.key}`, d.body, { metadata: { name: d.name, type: d.type } });
    await env.ONBOARDING.put(`sub:${id}`, JSON.stringify(record), { metadata: { name, submitted: record.submitted } });
  } catch (err) {
    console.error("Onboarding save failed", err);
    return reply("save");
  }

  // Notification: contact details needed to send the Xero onboarding invite (no ID, visa or other personal details)
  try {
    if (env.RESEND_API_KEY) {
      const email = val("email"), mobile = val("mobile");
      await sendEmail(env, {
        to: TO, from: { email: FROM, name: "Bridgepoint website" },
        subject: `Staff onboarding step 1 received: ${name} - send Xero invite`,
        text: `${name} has completed step 1 of onboarding.\n\nSend the Xero payroll onboarding invite (Xero > Payroll > Employees):\nName: ${name}\nEmail: ${email}\nMobile: ${mobile}\n\nFull submission: https://bridgepointrecruitment.com/staff-admin`,
        html: `<div style="font-family:Arial,sans-serif;font-size:14px;line-height:1.6"><p>${esc(name)} has completed step 1 of onboarding.</p><p><b>Send the Xero payroll onboarding invite</b> (Xero &gt; Payroll &gt; Employees):<br>Name: ${esc(name)}<br>Email: ${esc(email)}<br>Mobile: ${esc(mobile)}</p><p><a href="https://bridgepointrecruitment.com/staff-admin">View full submission</a></p></div>`,
      });
    }
  } catch (err) { console.error("Onboarding notification failed", err); }
  return reply(null);
}

// ---------- /staff-admin: password-protected viewer ----------
const ADMIN_HEADERS = { "Cache-Control": "no-store", "X-Robots-Tag": "noindex, nofollow", "Referrer-Policy": "no-referrer", "X-Frame-Options": "DENY" };

async function adminAuthorised(request, env) {
  if (!env.ADMIN_PASSWORD) return false;
  const h = request.headers.get("Authorization") || "";
  if (!h.startsWith("Basic ")) return false;
  let pass = "";
  try { const d = atob(h.slice(6)); pass = d.slice(d.indexOf(":") + 1); } catch { return false; }
  return same(pass, env.ADMIN_PASSWORD);
}

function adminPage(title, body) {
  return new Response(`<!doctype html><html lang="en-AU"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex">
<title>${esc(title)} | Bridgepoint staff admin</title><link rel="stylesheet" href="/assets/site.css"><style>
main{max-width:900px;margin:0 auto;padding:40px 24px 80px}h1{font-size:28px}h2{font-size:17px;font-weight:600;margin-top:30px}
table{width:100%;border-collapse:collapse;margin-top:10px;font-size:14px}td,th{text-align:left;padding:9px 10px;border-bottom:1px solid var(--line);vertical-align:top}
th{font-size:12px;color:var(--muted);font-weight:600}td:first-child{color:var(--muted);width:40%}a.u{color:var(--a);border-bottom:1px solid var(--line)}.back{font-size:13px;color:var(--muted)}
</style></head><body><main>${body}</main></body></html>`, { headers: { "Content-Type": "text/html; charset=utf-8", ...ADMIN_HEADERS } });
}

async function handleAdmin(request, env, url) {
  if (!env.ONBOARDING) return new Response("Not configured", { status: 503, headers: ADMIN_HEADERS });
  if (!(await adminAuthorised(request, env)))
    return new Response("Authentication required", { status: 401, headers: { "WWW-Authenticate": 'Basic realm="Bridgepoint staff admin", charset="UTF-8"', ...ADMIN_HEADERS } });

  const id = url.searchParams.get("id");
  const file = url.searchParams.get("file");
  if (id && file) {
    const { value, metadata } = await env.ONBOARDING.getWithMetadata(`file:${id}:${file}`, { type: "arrayBuffer" });
    if (!value) return new Response("Not found", { status: 404, headers: ADMIN_HEADERS });
    const fname = String(metadata?.name || file).replace(/[^\w.\- ]/g, "_");
    return new Response(value, { headers: { "Content-Type": metadata?.type || "application/octet-stream", "Content-Disposition": `attachment; filename="${fname}"`, ...ADMIN_HEADERS } });
  }
  if (id) {
    const rec = await env.ONBOARDING.get(`sub:${id}`, { type: "json" });
    if (!rec) return new Response("Not found", { status: 404, headers: ADMIN_HEADERS });
    const when = new Date(rec.submitted).toLocaleString("en-AU", { timeZone: "Australia/Sydney" });
    const secs = rec.sections.map(([t, rows]) => `<h2>${esc(t)}</h2><table>${rows.map(([l, v]) => `<tr><td>${esc(l)}</td><td>${esc(v).replace(/\n/g, "<br>")}</td></tr>`).join("")}</table>`).join("");
    const docs = rec.files.length ? `<h2>Documents</h2><table>${rec.files.map((f) => `<tr><td>${esc(f.label)}</td><td><a class="u" href="/staff-admin?id=${encodeURIComponent(id)}&file=${encodeURIComponent(f.key)}">${esc(f.name)}</a></td></tr>`).join("")}</table>` : "";
    return adminPage(rec.name, `<a class="back" href="/staff-admin">&larr; All submissions</a><h1 style="margin-top:12px">${esc(rec.name)}</h1><p class="back">Submitted ${esc(when)}</p>${secs}${docs}`);
  }
  const keys = [];
  let cursor;
  do { const r = await env.ONBOARDING.list({ prefix: "sub:", cursor }); keys.push(...r.keys); cursor = r.list_complete ? null : r.cursor; } while (cursor);
  keys.sort((a, b) => (b.metadata?.submitted || "").localeCompare(a.metadata?.submitted || ""));
  const rows = keys.map((k) => {
    const sid = k.name.slice(4);
    const when = k.metadata?.submitted ? new Date(k.metadata.submitted).toLocaleString("en-AU", { timeZone: "Australia/Sydney" }) : "";
    return `<tr><td><a class="u" href="/staff-admin?id=${encodeURIComponent(sid)}">${esc(k.metadata?.name || sid)}</a></td><td>${esc(when)}</td></tr>`;
  }).join("");
  return adminPage("Onboarding submissions", `<h1>Onboarding submissions</h1><table><tr><th>Name</th><th>Submitted</th></tr>${rows || '<tr><td colspan="2">No submissions yet.</td></tr>'}</table>`);
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname.replace(/\/+$/, "") || "/";

    if (FORMS[path]) return handleForm(request, env, FORMS[path]);
    if (path === "/api/onboarding") return handleOnboarding(request, env);
    if (path === "/staff-admin") return handleAdmin(request, env, url);

    if (redirects[path]) return Response.redirect(new URL(redirects[path], url).toString(), 301);
    // Wix encoded the slash in one job URL
    const decoded = decodeURIComponent(path);
    if (redirects[decoded]) return Response.redirect(new URL(redirects[decoded], url).toString(), 301);

    return env.ASSETS.fetch(request);
  },
};
