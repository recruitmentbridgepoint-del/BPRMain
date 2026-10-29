"""Add SEO tags, structured data, sitemap.xml and robots.txt to everything in /public.
Run last:  python3 build_jobs.py && python3 build_pages.py && python3 seo.py
"""
import os, re, json, html

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "public")
SITE = "https://bridgepointrecruitment.com"   # confirm final domain (www or not) before launch
POSTED = "2026-10-12"                          # date listings are published on the new site
jobs = {j["slug"]: j for j in json.load(open(os.path.join(ROOT, "data", "jobs.json")))}

ORG = {
  "@context": "https://schema.org", "@type": "EmploymentAgency", "name": "Bridgepoint Recruitment",
  "url": SITE + "/", "logo": SITE + "/images/mark-black.png", "image": SITE + "/images/og-image.jpg",
  "telephone": "+61 2 9248 7294", "email": "info@bridgepointrecruitment.com",
  "address": {"@type": "PostalAddress", "streetAddress": "55 Pyrmont Bridge Road", "addressLocality": "Pyrmont",
              "addressRegion": "NSW", "postalCode": "2009", "addressCountry": "AU"},
  "areaServed": {"@type": "City", "name": "Sydney"},
  "openingHoursSpecification": [
    {"@type": "OpeningHoursSpecification", "dayOfWeek": ["Monday","Tuesday","Wednesday","Thursday","Friday"], "opens": "08:00", "closes": "17:00"},
    {"@type": "OpeningHoursSpecification", "dayOfWeek": "Saturday", "opens": "10:00", "closes": "15:00"}],
  "description": "Permanent, executive search and temporary recruitment for Sydney's logistics and operations businesses."
}

STATE = {"NSW": "NSW", "QLD": "QLD", "SA": "SA", "VIC": "VIC", "Western Australia": "WA"}

def job_ld(j):
    loc = j["location"].split(", ")
    locality, region = (loc[0], loc[1]) if len(loc) == 2 else ("", STATE.get(loc[0], loc[0]))
    addr = {"@type": "PostalAddress", "addressRegion": region, "addressCountry": "AU"}
    if locality: addr["addressLocality"] = locality
    ld = {"@context": "https://schema.org", "@type": "JobPosting", "title": j["title"],
          "description": "<p>" + "</p><p>".join(html.escape(p) for p in [j["summary"]] + j["about"]) + "</p><ul>" +
                         "".join(f"<li>{html.escape(d)}</li>" for d in j["duties"] + j["reqs"]) + "</ul>",
          "identifier": {"@type": "PropertyValue", "name": "Bridgepoint Recruitment", "value": j["ref"]},
          "datePosted": j.get("posted", POSTED), "employmentType": "FULL_TIME",
          "hiringOrganization": {"@type": "Organization", "name": "Bridgepoint Recruitment", "sameAs": SITE + "/", "logo": SITE + "/images/mark-black.png"},
          "jobLocation": {"@type": "Place", "address": addr}, "directApply": True}
    m = re.match(r"\$([\d,.]+)", j["salary"])
    if m:
        hourly = "/hr" in j["salary"] or "per hour" in j["salary"]
        amount = float(m.group(1).replace(",", ""))
        ld["baseSalary"] = {"@type": "MonetaryAmount", "currency": "AUD",
                            "value": {"@type": "QuantitativeValue", "value": int(amount) if amount.is_integer() else amount,
                                      "unitText": "HOUR" if hourly else "YEAR"}}
    return ld

def crumbs(items):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, "item": SITE + u} for i, (n, u) in enumerate(items)]}

urls = []
for dirpath, _, files in os.walk(OUT):
    for fn in files:
        if fn != "index.html": continue
        fp = os.path.join(dirpath, fn)
        rel = "/" + os.path.relpath(dirpath, OUT).replace("\\", "/").strip(".") .strip("/")
        path = "/" if rel in ("/", "/.") else rel.rstrip("/") + "/"
        s = open(fp).read()
        s = re.sub(r'\n?<!-- seo -->.*?<!-- /seo -->', "", s, flags=re.S)   # idempotent
        title = re.search(r"<title>(.*?)</title>", s, re.S).group(1).strip()
        desc_m = re.search(r'<meta name="description" content="(.*?)">', s, re.S)
        desc = desc_m.group(1) if desc_m else ""
        noindex = path.startswith("/thanks")
        tags = [f'<link rel="canonical" href="{SITE}{path}">',
                '<meta name="robots" content="noindex">' if noindex else '<meta name="robots" content="index, follow">',
                '<meta property="og:site_name" content="Bridgepoint Recruitment">', '<meta property="og:locale" content="en_AU">',
                f'<meta property="og:type" content="website">', f'<meta property="og:url" content="{SITE}{path}">',
                f'<meta property="og:title" content="{title}">', f'<meta property="og:description" content="{desc}">',
                f'<meta property="og:image" content="{SITE}/images/og-image.jpg">', '<meta name="twitter:card" content="summary_large_image">',
                '<meta name="theme-color" content="#23414f">',
                '<link rel="icon" type="image/png" href="/images/favicon.png">']
        lds = []
        if path == "/":
            lds.append(ORG)
        elif path == "/jobs/":
            lds.append(crumbs([("Home", "/"), ("Jobs", "/jobs/")]))
        elif path.startswith("/jobs/"):
            j = jobs.get(path.strip("/").split("/")[1])
            if j:
                lds.append(job_ld(j))
                lds.append(crumbs([("Home", "/"), ("Jobs", "/jobs/"), (j["title"], path)]))
        for ld in lds:
            tags.append('<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False).replace("</", "<\\/") + "</script>")
        s = s.replace("</title>", "</title>\n<!-- seo -->\n" + "\n".join(tags) + "\n<!-- /seo -->", 1)

        # Images: explicit lazy loading below the first screen, async decoding everywhere
        def img(m):
            t = m.group(0)
            if "decoding=" not in t: t = t.replace("<img ", '<img decoding="async" ', 1)
            return t
        s = re.sub(r"<img [^>]*>", img, s)
        first = True
        def lazy(m):
            nonlocal_first = None
            return m.group(0)
        parts = re.split(r"(<img [^>]*>)", s)
        seen = 0
        for i, p in enumerate(parts):
            if p.startswith("<img ") and "loading=" not in p:
                seen += 1
                if seen > 3:  # logo + hero images load eagerly
                    parts[i] = p.replace("<img ", '<img loading="lazy" ', 1)
        s = "".join(parts)
        open(fp, "w").write(s)
        if not noindex: urls.append(path)

urls.sort(key=lambda u: (u != "/", u))
pri = lambda u: "1.0" if u == "/" else "0.8" if u == "/jobs/" else "0.6" if u.startswith("/jobs/") else "0.3"
open(os.path.join(OUT, "sitemap.xml"), "w").write(
  '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
  "".join(f"  <url><loc>{SITE}{u}</loc><lastmod>{POSTED}</lastmod><priority>{pri(u)}</priority></url>\n" for u in urls) + "</urlset>\n")
open(os.path.join(OUT, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\nDisallow: /thanks/\nDisallow: /api/\n\nSitemap: {SITE}/sitemap.xml\n")
print(len(urls), "pages indexed in sitemap")
