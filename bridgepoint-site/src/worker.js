// Bridgepoint Recruitment — Cloudflare Worker
// Serves the static site from /public, redirects old Wix URLs, and emails form submissions.

import redirects from "./redirects.json";

const TO = "info@bridgepointrecruitment.com";       // where every form is delivered
const FROM = "website@bridgepointrecruitment.com";  // sender; domain must be set up in Cloudflare Email
const MAX_FILE = 4 * 1024 * 1024;                   // Email Service limit is 5 MiB per message in total

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
    await env.EMAIL.send(message);
  } catch (err) {
    console.error("Email send failed", err);
    return back(request.url, `error=send&f=${form.thanks}`);
  }
  return back(request.url, `f=${form.thanks}`);
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname.replace(/\/+$/, "") || "/";

    if (FORMS[path]) return handleForm(request, env, FORMS[path]);

    if (redirects[path]) return Response.redirect(new URL(redirects[path], url).toString(), 301);
    // Wix encoded the slash in one job URL
    const decoded = decodeURIComponent(path);
    if (redirects[decoded]) return Response.redirect(new URL(redirects[decoded], url).toString(), 301);

    return env.ASSETS.fetch(request);
  },
};
