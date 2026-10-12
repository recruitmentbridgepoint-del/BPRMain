"""Generate /jobs/index.html and /jobs/<slug>/index.html from data/jobs.json.
Run from the site root:  python3 build_jobs.py
"""
import json, html, os

ROOT = os.path.dirname(os.path.abspath(__file__))
jobs = json.load(open(os.path.join(ROOT, "data", "jobs.json")))
e = html.escape

HEAD = """<!doctype html>
<html lang="en-AU">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/site.css">
<style>{css}</style>
</head>
<body>
<header class="top">
  <div class="in">
    <a class="logo" href="/"><img src="/images/mark-black.png" alt="">Bridgepoint Recruitment</a>
    <nav class="links" aria-label="Main"><a href="/#sectors">Sectors</a><a href="/#how">How it works</a><a href="/#guarantee">Guarantee</a><a href="/#services">Services</a><a href="/jobs" aria-current="page">Jobs</a></nav>
    <div class="right"><a href="tel:+61292487294">(02) 9248 7294</a><a class="cta cta--sm" href="/#brief">Brief us on a role</a>
      <button class="burger" aria-label="Open menu" aria-expanded="false" id="burger"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M3 8h18M3 16h18"/></svg></button></div>
  </div>
  <nav class="drawer" id="drawer" aria-label="Mobile"><a href="/#sectors">Sectors</a><a href="/#how">How it works</a><a href="/#guarantee">Guarantee</a><a href="/#services">Services</a><a href="/jobs">Jobs</a><a href="/#brief">Brief us on a role</a></nav>
</header>
"""

FOOT = """<footer class="foot">
  <div class="in">
    <div class="foot__top">
      <div class="foot__brand"><img src="/images/mark-white.png" alt=""><p>Bridgepoint Recruitment</p></div>
      <div><h4>Employers</h4><ul><li><a href="/#brief">Brief us on a role</a></li><li><a href="/#services">Services</a></li><li><a href="/#guarantee">Our guarantee</a></li><li><a href="/#faq">FAQ</a></li></ul></div>
      <div><h4>Job seekers</h4><ul><li><a href="/jobs">Search jobs</a></li><li><a href="/jobs#register">Register your resume</a></li></ul></div>
      <div><h4>Contact</h4><ul><li><a href="tel:+61292487294">(02) 9248 7294</a></li><li><a href="mailto:info@bridgepointrecruitment.com">info@bridgepointrecruitment.com</a></li><li>55 Pyrmont Bridge Road<br>Pyrmont NSW 2009</li><li>Mon–Fri 8am–5pm &middot; Sat 10am–3pm</li></ul></div>
    </div>
    <div class="foot__base"><span>&copy; 2026 Bridgepoint Recruitment</span><span><a href="/privacy">Privacy policy</a> &nbsp;&middot;&nbsp; <a href="/terms">Terms of business</a></span></div>
  </div>
</footer>
<script>
  const bg=document.getElementById('burger'),dr=document.getElementById('drawer');
  bg.addEventListener('click',()=>{const o=dr.classList.toggle('open');bg.setAttribute('aria-expanded',o);});
</script>
"""

ICON_PIN = '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.3"><path d="M8 14s5-4.2 5-8A5 5 0 0 0 3 6c0 3.8 5 8 5 8z"/><circle cx="8" cy="6" r="1.7"/></svg>'
ICON_CLOCK = '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.3"><circle cx="8" cy="8" r="6"/><path d="M8 4.8V8l2.2 1.4"/></svg>'
ICON_LEVEL = '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.3"><path d="M2.5 13h11M4.5 13V9M8 13V5.5M11.5 13V3"/></svg>'
CHECK = '<svg viewBox="0 0 18 18" fill="none" stroke="currentColor" stroke-width="1.4"><rect x="2" y="2" width="14" height="14" rx="4"/><path d="M5.8 9.2l2.2 2.2 4.3-4.6"/></svg>'

# ---------- Listing page ----------
LIST_CSS = """
.jhead{border-bottom:1px solid var(--line)}
.jhead .in{display:grid;grid-template-columns:1.3fr 1fr;gap:40px;align-items:end;padding-top:46px;padding-bottom:34px}
.jhead h1{margin-top:12px}
.jhead .lead{margin-top:12px}
.emp{border-radius:16px;padding:22px 24px;background:var(--band);color:#fff;display:flex;justify-content:space-between;gap:20px;align-items:center}
.emp b{display:block;font-size:15px;font-weight:600}
.emp span{display:block;margin-top:2px;font-size:12.5px;color:rgba(255,255,255,.85)}
.emp a{flex:none;height:42px;padding:0 20px;border-radius:999px;background:#fff;color:var(--a);display:inline-flex;align-items:center;font-size:12px;font-weight:600;letter-spacing:.05em;text-transform:uppercase}
.filters{position:sticky;top:70px;z-index:10;background:rgba(255,255,255,.96);backdrop-filter:blur(6px);border-bottom:1px solid var(--line)}
.filters .in{display:grid;grid-template-columns:260px 1fr 180px;gap:14px;align-items:center;padding-top:14px;padding-bottom:14px}
.search{position:relative}
.search svg{position:absolute;left:12px;top:50%;transform:translateY(-50%);width:16px;height:16px;color:var(--muted)}
.search input{padding-left:36px;border-radius:999px;height:40px}
.filters select{height:40px;border-radius:999px}
.count{padding:22px 0 0;font-size:12.5px;color:var(--muted)}
.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;padding:16px 0 70px}
.card{display:flex;flex-direction:column;border:1px solid var(--line);border-radius:18px;overflow:hidden;background:#fff;transition:box-shadow .25s,transform .25s}
.card:hover{box-shadow:0 22px 50px -30px rgba(23,36,44,.45);transform:translateY(-2px)}
.card__top{padding:20px 22px 18px;background:linear-gradient(150deg,#f3f7f6,#e3ecea)}
.card__row{display:flex;justify-content:space-between;align-items:center;font-size:11px}
.pill{display:inline-flex;align-items:center;height:24px;padding:0 10px;border-radius:999px;background:#fff;border:1px solid #cfdcdb;color:var(--a);font-weight:600}
.ref{color:var(--muted);letter-spacing:.06em}
.card h3{margin-top:16px;font-size:19px;line-height:1.25;font-weight:600;letter-spacing:-.01em}
.card__salary{margin-top:6px;font-size:13px;font-weight:600;background:var(--grad);-webkit-background-clip:text;background-clip:text;color:transparent}
.card__body{padding:16px 22px 22px;display:flex;flex-direction:column;gap:14px;flex:1}
.card__body p{font-size:13px;color:var(--muted);flex:1}
.facts{display:flex;flex-wrap:wrap;gap:8px 16px;font-size:12px;color:var(--ink)}
.facts span{display:inline-flex;align-items:center;gap:6px}
.facts svg{width:14px;height:14px;color:var(--a)}
.card .cta{height:44px;font-size:12px}
.empty{display:none;padding:40px 0 80px;text-align:center;color:var(--muted)}
.typ{background:var(--soft)}
.typ .in{padding-top:70px;padding-bottom:70px;display:grid;grid-template-columns:1fr 1.05fr;gap:56px;align-items:start}
.typ ul{margin-top:26px;display:grid;grid-template-columns:1fr 1fr;gap:18px 26px}
.typ li{list-style:none}
.typ li b{display:block;font-size:13.5px;font-weight:600}
.typ li span{display:block;margin-top:3px;font-size:12.5px;color:var(--muted);line-height:1.45}
.typ .note{margin-top:24px;font-size:12px;color:var(--muted)}
@media (max-width:980px){.jhead .in,.typ .in{grid-template-columns:1fr}.grid{grid-template-columns:1fr 1fr}.filters .in{grid-template-columns:1fr 1fr}.filters .seg{grid-column:1/-1;order:3}}
@media (max-width:640px){.grid{grid-template-columns:1fr}.filters{position:static}.filters .in{grid-template-columns:1fr}.filters .seg{overflow-x:auto;flex-wrap:nowrap;padding-bottom:4px}.filters .seg button{flex:none}.emp{flex-direction:column;align-items:flex-start}.typ ul{grid-template-columns:1fr}}
"""

cats = []
for j in jobs:
    if j["category"] not in cats:
        cats.append(j["category"])
locs = sorted({j["location"] for j in jobs})

cards = []
for j in jobs:
    cards.append(f"""<a class="card" href="/jobs/{j['slug']}/" data-cat="{e(j['category'])}" data-loc="{e(j['location'])}" data-text="{e((j['title']+' '+j['summary']+' '+j['category']).lower())}">
  <div class="card__top"><div class="card__row"><span class="pill">{e(j['category'])}</span><span class="ref">{j['ref']}</span></div>
    <h3>{e(j['title'])}</h3><div class="card__salary">{e(j['salary'])}</div></div>
  <div class="card__body"><p>{e(j['summary'])}</p>
    <div class="facts"><span>{ICON_PIN}{e(j['location'])}</span><span>{ICON_CLOCK}{e(j['type'])}</span><span>{ICON_LEVEL}{e(j['level'])}</span></div>
    <span class="cta">View role</span></div>
</a>""")

listing = HEAD.format(title="Logistics &amp; Operations Jobs in Sydney | Bridgepoint Recruitment",
                      desc="Current logistics, operations, finance and office roles with Bridgepoint Recruitment.",
                      css=LIST_CSS) + f"""
<main>
<section class="jhead"><div class="in">
  <div>
    <p class="meta"><a href="/">Home</a> <i></i> Jobs</p>
    <h1>Current roles</h1>
    <p class="lead">Logistics, operations and the office teams behind them. Apply online in a few minutes; a consultant will contact you if your experience fits.</p>
  </div>
  <div class="emp"><div><b>Hiring?</b><span>No placement, no fee. 6-month replacement guarantee.</span></div><a href="/#brief">Brief us on a role</a></div>
</div></section>

<div class="filters"><div class="in">
  <label class="search" aria-label="Search roles">{'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4"><circle cx="7" cy="7" r="4.8"/><path d="M10.5 10.5L14 14"/></svg>'}<input id="q" type="search" placeholder="Search roles"></label>
  <div class="seg" id="cat"><button type="button" aria-pressed="true" data-v="">All</button>{''.join(f'<button type="button" aria-pressed="false" data-v="{e(c)}">{e(c)}</button>' for c in cats)}</div>
  <select id="loc" aria-label="Location"><option value="">All locations</option>{''.join(f'<option>{e(l)}</option>' for l in locs)}</select>
</div></div>

<div class="in">
  <p class="count" id="count">{len(jobs)} roles</p>
  <div class="grid" id="grid">
{chr(10).join(cards)}
  </div>
  <p class="empty" id="empty">No roles match your search. <a href="#register" style="border-bottom:1px solid var(--line)">Register your resume</a> and we will contact you when a suitable role comes in.</p>
</div>

<section class="typ" id="register"><div class="in">
  <div>
    <h2>Not seeing the right role?</h2>
    <p class="lead" style="margin-top:12px">Many of our roles are filled before they are advertised. Register your resume and we will contact you when a role that fits comes in. These are the roles we recruit for most often:</p>
    <ul>
      <li><b>Warehousing &amp; distribution</b><span>Storepersons, forklift operators, pick-packers, team leaders, DC managers</span></li>
      <li><b>Transport &amp; freight</b><span>Drivers, allocators, freight forwarders, import and export operators</span></li>
      <li><b>Manufacturing &amp; production</b><span>Process workers, machine operators, production supervisors</span></li>
      <li><b>Operations management</b><span>Operations, supply chain and site managers, directors</span></li>
      <li><b>Finance, HR &amp; payroll</b><span>Accounts payable, payroll officers, HR advisors, finance controllers</span></li>
      <li><b>Customer service &amp; admin</b><span>Customer service, logistics coordinators, office administration</span></li>
    </ul>
  </div>
  <form class="formcard" action="/api/register" method="post" enctype="multipart/form-data"><input type="text" name="website" tabindex="-1" autocomplete="off" aria-hidden="true" style="position:absolute;left:-9999px;height:1px;width:1px">
    <div class="fgrid">
      <div><label for="r-name">Name</label><input id="r-name" name="name" autocomplete="name" required></div>
      <div><label for="r-phone">Phone</label><input id="r-phone" name="phone" type="tel" autocomplete="tel" required></div>
      <div class="full"><label for="r-email">Email</label><input id="r-email" name="email" type="email" autocomplete="email" required></div>
      <div><label for="r-sector">Area of work</label><select id="r-sector" name="sector"><option>Warehousing &amp; distribution</option><option>Transport &amp; freight</option><option>Manufacturing &amp; production</option><option>Operations management</option><option>Finance, HR &amp; payroll</option><option>Customer service &amp; admin</option><option>Other</option></select></div>
      <div><label for="r-type">Work type</label><select id="r-type" name="work_type"><option>Permanent</option><option>Temporary</option><option>Either</option></select></div>
      <div class="full"><label for="r-cv">Resume <span>(PDF or Word, max 4 MB)</span></label><input id="r-cv" name="resume" type="file" accept=".pdf,.doc,.docx" required></div>
    </div>
    <button class="cta" type="submit">Register</button>
    <p class="fine">We use your details only to match you with suitable roles. See our <a href="/privacy">privacy policy</a>.</p>
  </form>
</div></section>
</main>
""" + FOOT + """<script>
  const q=document.getElementById('q'),loc=document.getElementById('loc'),cat=document.getElementById('cat');
  const cards=[...document.querySelectorAll('#grid .card')],count=document.getElementById('count'),empty=document.getElementById('empty');
  let c='';
  function run(){const t=q.value.trim().toLowerCase(),l=loc.value;let n=0;
    cards.forEach(k=>{const ok=(!c||k.dataset.cat===c)&&(!l||k.dataset.loc===l)&&(!t||k.dataset.text.includes(t));k.style.display=ok?'':'none';if(ok)n++;});
    count.textContent=n+(n===1?' role':' roles');empty.style.display=n?'none':'block';}
  cat.addEventListener('click',ev=>{const b=ev.target.closest('button');if(!b)return;cat.querySelectorAll('button').forEach(x=>x.setAttribute('aria-pressed',x===b));c=b.dataset.v;run();});
  q.addEventListener('input',run);loc.addEventListener('change',run);
</script>
</body>
</html>
"""

OUT = os.path.join(ROOT, "public")
os.makedirs(os.path.join(OUT, "jobs"), exist_ok=True)
open(os.path.join(OUT, "jobs", "index.html"), "w").write(listing)

# ---------- Detail pages (Healthon buy-box layout) ----------
DETAIL_CSS = """
.jd{display:grid;grid-template-columns:1.35fr 1fr;gap:0;border-bottom:1px solid var(--line)}
.jd__main{padding:40px 48px 70px 0;border-right:1px solid var(--line)}
.jd__main h1{margin-top:12px}
.jd__sum{margin-top:14px;font-size:16px;color:var(--muted);max-width:620px}
.jd__main h2{margin-top:40px;font-size:20px;font-weight:600;letter-spacing:-.01em}
.jd__main p.body{margin-top:12px;font-size:14.5px;color:#33434b;max-width:680px}
.jd__main ul{margin-top:14px;display:grid;gap:10px;max-width:680px}
.jd__main li{list-style:none;display:flex;gap:10px;font-size:14px;color:#33434b}
.jd__main li svg{width:17px;height:17px;flex:none;margin-top:2px;color:var(--a)}
.apply{margin-top:50px}
.apply h2{margin-top:0!important}
.apply .formcard{margin-top:18px}
.jd__side{padding:40px 0 40px 40px}
.box{position:sticky;top:96px;border:1px solid var(--line);border-radius:18px;overflow:hidden}
.box__top{padding:22px 24px;background:linear-gradient(150deg,#f3f7f6,#e3ecea)}
.box__top small{font-size:11px;letter-spacing:.06em;color:var(--muted)}
.box__top b{display:block;margin-top:6px;font-size:18px;font-weight:600}
.box__top span{display:block;margin-top:4px;font-size:14px;font-weight:600;background:var(--grad);-webkit-background-clip:text;background-clip:text;color:transparent}
.box dl{padding:6px 24px}
.box dl div{display:flex;justify-content:space-between;gap:16px;padding:12px 0;border-bottom:1px solid var(--line);font-size:13px}
.box dl div:last-child{border-bottom:0}
.box dt{color:var(--muted)}
.box dd{font-weight:600;text-align:right}
.box__cta{padding:6px 24px 24px;display:grid;gap:10px}
.box__cta .cta{width:100%}
.share{display:flex;justify-content:center;gap:8px;font-size:12px;color:var(--muted)}
.share button{background:none;border:0;border-bottom:1px solid var(--line);cursor:pointer;font-size:12px;color:var(--ink)}
.more{background:var(--soft)}
.more .in{padding-top:60px;padding-bottom:60px}
.more__grid{margin-top:24px;display:grid;grid-template-columns:repeat(3,1fr);gap:16px}
.more a{display:block;padding:18px 20px;border-radius:14px;background:#fff;border:1px solid var(--line)}
.more a:hover{border-color:var(--b)}
.more a b{display:block;font-size:15px;font-weight:600}
.more a span{display:block;margin-top:4px;font-size:12.5px;color:var(--muted)}
.back{display:inline-flex;margin-top:20px;font-size:12.5px;font-weight:600;color:var(--a);border-bottom:1px solid var(--line)}
@media (max-width:980px){.jd{grid-template-columns:1fr}.jd__main{padding:32px 0 50px;border-right:0}.jd__side{padding:0 0 40px;order:-1}.box{position:static;margin-top:24px}.more__grid{grid-template-columns:1fr}}
"""

for j in jobs:
    related = [r for r in jobs if r["slug"] != j["slug"] and r["category"] == j["category"]][:3]
    if len(related) < 3:
        related += [r for r in jobs if r["slug"] != j["slug"] and r not in related][: 3 - len(related)]
    page = HEAD.format(title=f"{e(j['title'])} | {e(j['location'])} | Bridgepoint Recruitment",
                       desc=e(j["summary"]), css=DETAIL_CSS) + f"""
<main class="in">
  <section class="jd">
    <article class="jd__main">
      <p class="meta"><a href="/">Home</a> <i></i> <a href="/jobs">Jobs</a> <i></i> {e(j['category'])}</p>
      <h1>{e(j['title'])}</h1>
      <p class="jd__sum">{e(j['summary'])}</p>
      <h2>About the role</h2>
      {''.join(f'<p class="body">{e(p)}</p>' for p in j['about'])}
      <h2>What you will do</h2>
      <ul>{''.join(f'<li>{CHECK}{e(d)}</li>' for d in j['duties'])}</ul>
      <h2>What you will bring</h2>
      <ul>{''.join(f'<li>{CHECK}{e(r)}</li>' for r in j['reqs'])}</ul>

      <div class="apply" id="apply">
        <h2>Apply for this role</h2>
        <form class="formcard" action="/api/apply" method="post" enctype="multipart/form-data"><input type="text" name="website" tabindex="-1" autocomplete="off" aria-hidden="true" style="position:absolute;left:-9999px;height:1px;width:1px">
          <input type="hidden" name="job_ref" value="{j['ref']}"><input type="hidden" name="job_title" value="{e(j['title'])}">
          <div class="fgrid">
            <div><label for="a-name">Name</label><input id="a-name" name="name" autocomplete="name" required></div>
            <div><label for="a-phone">Phone</label><input id="a-phone" name="phone" type="tel" autocomplete="tel" required></div>
            <div class="full"><label for="a-email">Email</label><input id="a-email" name="email" type="email" autocomplete="email" required></div>
            <div class="full"><label for="a-cv">Resume <span>(PDF or Word, max 4 MB)</span></label><input id="a-cv" name="resume" type="file" accept=".pdf,.doc,.docx" required></div>
            <div class="full"><label for="a-msg">Cover note <span>(optional)</span></label><textarea id="a-msg" name="message"></textarea></div>
          </div>
          <button class="cta" type="submit">Submit application</button>
          <p class="fine">We use your details only to assess your application. See our <a href="/privacy">privacy policy</a>.</p>
        </form>
      </div>
      <a class="back" href="/jobs">&larr; Back to all roles</a>
    </article>

    <aside class="jd__side">
      <div class="box">
        <div class="box__top"><small>REF {j['ref']}</small><b>{e(j['title'])}</b><span>{e(j['salary'])}</span></div>
        <dl>
          <div><dt>Category</dt><dd>{e(j['category'])}</dd></div>
          <div><dt>Location</dt><dd>{e(j['location'])}</dd></div>
          <div><dt>Job type</dt><dd>{e(j['type'])}</dd></div>
          <div><dt>Level</dt><dd>{e(j['level'])}</dd></div>
          <div><dt>Salary</dt><dd>{e(j['salary'])}</dd></div>
        </dl>
        <div class="box__cta"><a class="cta" href="#apply">Apply now</a>
          <div class="share">Share: <button type="button" id="copy">Copy link</button></div></div>
      </div>
    </aside>
  </section>
</main>

<section class="more"><div class="in">
  <h2 style="font-size:24px">Similar roles</h2>
  <div class="more__grid">{''.join(f'<a href="/jobs/{r["slug"]}/"><b>{e(r["title"])}</b><span>{e(r["location"])} &middot; {e(r["type"])} &middot; {e(r["level"])}</span></a>' for r in related)}</div>
</div></section>
""" + FOOT + """<script>
  document.getElementById('copy').addEventListener('click',e=>{navigator.clipboard&&navigator.clipboard.writeText(location.href);e.target.textContent='Link copied';});
</script>
</body>
</html>
"""
    d = os.path.join(OUT, "jobs", j["slug"])
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "index.html"), "w").write(page)

# Redirect old Wix job URLs to the new pages (Cloudflare Pages _redirects format)
old = {"global-operations-director": "global-operations-director-", "logistics-coordinator": "logistics-coordinator-",
       "head-of-marketing": "head-of-marketing-", "sales-director": "sales-director-", "finance-controller": "finance-controller-",
       "call-centre-customer-service": "call-centre-customer-service-",
       "customer-service-office-administrator": "customer-service%2Foffice-administration"}
redirects = {"/careers": "/jobs/", "/job-seekers": "/jobs/", "/employers": "/", "/about-us": "/", "/contact": "/#brief", "/blog": "/"}
for j in jobs:
    redirects["/jobpostings/" + old.get(j["slug"], j["slug"])] = "/jobs/" + j["slug"] + "/"
json.dump(redirects, open(os.path.join(ROOT, "src", "redirects.json"), "w"), indent=1)
print("built", len(jobs), "job pages")
