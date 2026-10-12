"""Generate /thanks, /privacy and /terms using the same header and footer as the jobs pages.
Run after build_jobs.py:  python3 build_pages.py
"""
import os, re

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "public")
src = open(os.path.join(OUT, "jobs", "index.html")).read()
header = src[src.index("<header"):src.index("</header>") + 9].replace(' aria-current="page"', "")
footer = src[src.index('<footer class="foot">'):src.index("</body>")]

def page(slug, title, desc, body, css=""):
    html = f"""<!doctype html>
<html lang="en-AU">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} | Bridgepoint Recruitment</title>
<meta name="description" content="{desc}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/site.css">
<style>
.doc .in{{display:grid;grid-template-columns:240px 1fr;gap:60px;padding-top:46px;padding-bottom:80px}}
.doc nav{{position:sticky;top:96px;align-self:start;display:grid;gap:8px;font-size:13px;color:var(--muted)}}
.doc nav a:hover{{color:var(--ink)}}
.doc article{{max-width:720px}}
.doc h1{{margin-top:12px}}
.doc .upd{{margin-top:10px;font-size:12.5px;color:var(--muted)}}
.doc h2{{margin-top:38px;font-size:19px;font-weight:600;letter-spacing:-.01em}}
.doc p,.doc li{{margin-top:10px;font-size:14.5px;color:#33434b;line-height:1.65}}
.doc ul{{padding-left:20px}}
.doc a.u{{border-bottom:1px solid var(--line)}}
@media (max-width:860px){{.doc .in{{grid-template-columns:1fr;gap:20px}}.doc nav{{position:static}}}}
{css}
</style>
</head>
<body>
{header}
{body}
{footer}</body>
</html>
"""
    d = os.path.join(OUT, slug)
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "index.html"), "w").write(html)

def legal(slug, title, desc, updated, sections):
    toc = "".join(f'<a href="#{re.sub("[^a-z0-9]+","-",h.lower()).strip("-")}">{h}</a>' for h, _ in sections)
    body = "".join(f'<h2 id="{re.sub("[^a-z0-9]+","-",h.lower()).strip("-")}">{h}</h2>{c}' for h, c in sections)
    page(slug, title, desc, f"""<main class="doc"><div class="in">
  <nav aria-label="On this page">{toc}</nav>
  <article><p class="meta"><a href="/">Home</a> <i></i> {title}</p><h1>{title}</h1><p class="upd">Last updated {updated}</p>{body}</article>
</div></main>""")

# ---------- Thank-you page ----------
page("thanks", "Thank you", "Thank you for contacting Bridgepoint Recruitment.", """
<main><section style="min-height:60vh;display:flex;align-items:center"><div class="in" style="text-align:center;padding-top:80px;padding-bottom:80px">
  <div id="ok">
    <svg viewBox="0 0 48 48" width="56" height="56" fill="none" stroke="#23414f" stroke-width="1.6" style="margin:0 auto"><circle cx="24" cy="24" r="21"/><path d="M15 24.5l6 6 12-13"/></svg>
    <h1 id="t" style="margin-top:20px">Thank you</h1>
    <p class="lead" id="m" style="margin:12px auto 0">We have received your details.</p>
  </div>
  <div style="margin-top:30px;display:flex;gap:12px;justify-content:center;flex-wrap:wrap">
    <a class="cta" href="/">Back to home</a><a class="cta cta--ghost" href="/jobs">View current roles</a>
  </div>
</div></section></main>
<script>
  const q=new URLSearchParams(location.search),f=q.get('f'),e=q.get('error');
  const msg={brief:["Brief received","A consultant will contact you to confirm the role, timing and fees. Suitable candidate profiles are shared within 24 hours."],
             apply:["Application received","Thank you for applying. A consultant will contact you if your experience matches the role."],
             register:["Resume registered","We will contact you when a role that fits your experience comes in."]};
  const err={size:"Your resume is larger than 4 MB. Please reduce the file size and try again.",type:"Please upload your resume as a PDF or Word document.",
             send:"Your details could not be sent. Please try again, or call us on (02) 9248 7294.",1:"Some required details were missing. Please go back and complete the form."};
  if(e){document.getElementById('t').textContent='Something went wrong';document.getElementById('m').textContent=err[e]||err[1];
        document.querySelector('#ok svg').style.display='none';}
  else if(msg[f]){document.getElementById('t').textContent=msg[f][0];document.getElementById('m').textContent=msg[f][1];}
</script>""")

# ---------- Privacy policy ----------
legal("privacy", "Privacy policy", "How Bridgepoint Recruitment collects, uses and protects personal information.", "October 2026", [
 ("About this policy", "<p>This policy explains how Bridgepoint Recruitment (“we”, “us”) collects, holds, uses and discloses personal information. We handle personal information in line with the Australian Privacy Principles in the <em>Privacy Act 1988</em> (Cth).</p>"),
 ("Information we collect", "<p>Depending on how you deal with us, we may collect:</p><ul><li>contact details such as your name, email address, phone number and location;</li><li>for candidates: your resume, employment history, qualifications, licences, work preferences, referee details and reference outcomes, and notes from interviews;</li><li>for employers: your name, company, role and the details of the positions you ask us to fill;</li><li>information you send us by email, phone or through forms on this website.</li></ul><p>We do not ask for sensitive information unless it is needed for a specific role and you consent to providing it.</p>"),
 ("How we collect it", "<p>We collect personal information directly from you when you submit a form on this website, send us your resume, speak with a consultant, or apply for a role. With your consent, we may also collect information from referees and from publicly available professional profiles.</p>"),
 ("How we use it", "<ul><li>to assess candidates for current and future roles;</li><li>to present suitable candidates to employers, with the candidate’s consent;</li><li>to respond to enquiries and manage our relationship with clients;</li><li>to meet our legal and administrative obligations.</li></ul>"),
 ("Who we share it with", "<p>We disclose candidate information to prospective employers only with the candidate’s consent. We use third-party service providers to run this website and deliver email, and they may process personal information on our behalf. We do not sell personal information.</p>"),
 ("Storage and security", "<p>We take reasonable steps to protect personal information from misuse, loss and unauthorised access. Information submitted through this website is sent to us by email and stored in our business systems. We keep information only as long as it is needed for the purposes above or as required by law.</p>"),
 ("Access and correction", "<p>You can ask to access or correct the personal information we hold about you, or ask us to remove your resume from our records, by contacting us using the details below.</p>"),
 ("Complaints", "<p>If you have a concern about how we have handled your personal information, please contact us first. If you are not satisfied with our response, you can contact the Office of the Australian Information Commissioner at <a class=\"u\" href=\"https://www.oaic.gov.au\">oaic.gov.au</a>.</p>"),
 ("Contact us", "<p>Bridgepoint Recruitment<br>55 Pyrmont Bridge Road, Pyrmont NSW 2009<br><a class=\"u\" href=\"mailto:info@bridgepointrecruitment.com\">info@bridgepointrecruitment.com</a> &middot; <a class=\"u\" href=\"tel:+61292487294\">(02) 9248 7294</a></p>"),
])

# ---------- Terms of business ----------
legal("terms", "Terms of business", "Bridgepoint Recruitment terms of business for employers.", "October 2026", [
 ("Application", "<p>These terms apply to all recruitment services Bridgepoint Recruitment provides to a client. They are accepted when the client briefs us on a role, interviews or engages a candidate we introduce, or confirms an assignment. Any variation must be agreed in writing.</p>"),
 ("Permanent placements", "<p>A placement fee is payable when a candidate introduced by us accepts employment with the client. The fee is calculated as the percentage of first-year remuneration set out in our written fee confirmation for the role. No fee is payable if no placement is made. Advertising, screening, interviews and reference checks are included in the fee.</p><p>Where a client fills two or more roles with us, the volume rate set out in our fee confirmation applies.</p>"),
 ("Introductions", "<p>A fee is payable if the client, or a related entity, engages a candidate introduced by us in any capacity within 12 months of the introduction, whether for the advertised role or another position.</p>"),
 ("Payment", "<p>Invoices are issued on the candidate’s start date and are payable within 14 days. All fees are exclusive of GST.</p>"),
 ("Replacement guarantee", "<p>If a permanent candidate leaves or is dismissed within six months of their start date, we will find a replacement at no additional fee, provided that:</p><ul><li>the original invoice was paid within 14 days;</li><li>the replacement is for the same role, on substantially the same terms;</li><li>the departure is not due to redundancy, restructure or a material change to the role;</li><li>the client notifies us in writing within 7 days of the candidate’s departure.</li></ul><p>One replacement is provided per placement. The guarantee does not apply to replacement candidates, executive search assignments with separate terms, or temporary workers converted to permanent employment.</p>"),
 ("Executive search", "<p>Executive search assignments are conducted under a separate written proposal setting out the fee, payment stages and scope of the search.</p>"),
 ("Temporary staff", "<p>Temporary workers are employed by Bridgepoint Recruitment and supplied to the client at the hourly charge rate confirmed in writing for each assignment. Timesheets are approved by the client weekly, and invoices are payable within 14 days. The client is responsible for providing a safe workplace, site induction and any required personal protective equipment.</p>"),
 ("Temp-to-perm conversion", "<p>If the client wishes to employ a temporary worker directly, a conversion fee applies as set out in the assignment confirmation. The conversion terms are agreed before the assignment begins.</p>"),
 ("Liability", "<p>We take reasonable care in assessing candidates, but the client is responsible for its own hiring decisions, including verifying any qualifications or licences required by law. To the extent permitted by law, our liability is limited to the fees paid for the relevant placement or assignment. Nothing in these terms excludes rights that cannot be excluded under the Australian Consumer Law.</p>"),
 ("Contact", "<p>Bridgepoint Recruitment<br>55 Pyrmont Bridge Road, Pyrmont NSW 2009<br><a class=\"u\" href=\"mailto:info@bridgepointrecruitment.com\">info@bridgepointrecruitment.com</a> &middot; <a class=\"u\" href=\"tel:+61292487294\">(02) 9248 7294</a></p>"),
])
print("built thanks, privacy, terms")
