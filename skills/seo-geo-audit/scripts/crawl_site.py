#!/usr/bin/env python3
"""
crawl_site.py: crawl alle URL's uit de sitemap van een site en leg per pagina de
signalen vast die voor SEO en GEO tellen. Alleen standaardbibliotheek.

Gebruik:
  python3 crawl_site.py https://example.com --out crawl.jsonl
  python3 crawl_site.py https://example.com --out crawl.jsonl --workers 3 --limit 200
  python3 crawl_site.py https://example.com --out crawl.jsonl --cache-bust
  python3 crawl_site.py --urls urls.txt --out crawl.jsonl

Opties:
  --workers N    gelijktijdige verzoeken (standaard 2; ga niet boven 5)
  --delay S      pauze per verzoek per worker in seconden (standaard 0.3)
  --limit N      maximaal N URL's (standaard alles)
  --cache-bust   voeg ?nc=<random> toe: meet de server in plaats van de CDN
  --urls FILE    gebruik een eigen URL-lijst in plaats van de sitemap

Uitvoer: één JSON-regel per URL met status, tijd, cacheheaders, titel,
omschrijving, robots, canonical, hreflang, html lang, H1-aantal, woorden in de
hoofdtekst, schema-types, og:image/og:locale en afbeeldingen zonder alt.

Belangrijk: robots- en andere meta-tags worden in de HELE pagina gezocht, niet
alleen in <head>. React 19 / Next.js zet metadata soms in de body; een parser
die bij </head> stopt, mist dan noindex.
"""
import argparse
import html
import json
import random
import re
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

UA = "Mozilla/5.0 (compatible; SEO-GEO-Audit/1.0; +https://oosterwal.com)"


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


OPENER = urllib.request.build_opener(NoRedirect)


def get(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Encoding": "identity"})
    t0 = time.time()
    try:
        r = OPENER.open(req, timeout=timeout)
        body = r.read().decode("utf-8", "replace")
        return r.status, dict(r.headers), body, time.time() - t0
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), "", time.time() - t0
    except Exception as e:  # time-out, DNS, TLS
        return 0, {}, f"{type(e).__name__}: {e}", time.time() - t0


def sitemap_urls(base):
    """Volgt sitemap-indexen (WordPress, Rank Math, Yoast, Next.js)."""
    candidates = [base + "/sitemap_index.xml", base + "/sitemap.xml", base + "/wp-sitemap.xml"]
    # robots.txt kan de sitemap noemen
    st, _, robots, _ = get(base + "/robots.txt")
    if st == 200:
        candidates = re.findall(r"(?im)^sitemap:\s*(\S+)", robots) + candidates
    seen, urls = set(), []
    queue = []
    for c in candidates:
        st, _, body, _ = get(c)
        if st == 200 and "<loc>" in body:
            queue.append((c, body))
            break
    while queue:
        loc, body = queue.pop()
        if loc in seen:
            continue
        seen.add(loc)
        for u in re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", body):
            u = html.unescape(u)
            if "<sitemapindex" in body:
                st, _, sub, _ = get(u)
                if st == 200:
                    queue.append((u, sub))
            elif "/wp-content/uploads/" not in u:
                urls.append(u)
    return list(dict.fromkeys(urls))


def attr(tag, name):
    m = re.search(r"\b" + name + r'\s*=\s*"([^"]*)"', tag, re.I) or re.search(
        r"\b" + name + r"\s*=\s*'([^']*)'", tag, re.I
    )
    return html.unescape(m.group(1)) if m else None


def analyse(url, status, headers, body, seconds):
    rec = {"url": url, "status": status, "seconds": round(seconds, 2)}
    hl = {k.lower(): v for k, v in headers.items()}
    for h in ("x-hcdn-cache-status", "x-litespeed-cache", "x-nextjs-cache", "cf-cache-status", "x-cache", "age", "cache-control"):
        if h in hl:
            rec.setdefault("cache", {})[h] = hl[h]
    if status in (301, 302, 307, 308):
        rec["location"] = hl.get("location")
        return rec
    if status != 200:
        if status == 0:
            rec["error"] = body[:120]
        return rec

    tags = re.findall(r"<(?:meta|link)\b[^>]*>", body, re.I)
    for t in tags:
        name = (attr(t, "name") or attr(t, "property") or "").lower()
        rel = (attr(t, "rel") or "").lower()
        if name == "robots":
            rec["robots"] = attr(t, "content")
        elif name == "description" and "desc" not in rec:
            rec["desc"] = attr(t, "content")
        elif name == "og:image":
            rec["og_image"] = attr(t, "content")
        elif name == "og:locale":
            rec["og_locale"] = attr(t, "content")
        if rel == "canonical":
            rec["canonical"] = attr(t, "href")
        lang = attr(t, "hreflang")
        if lang and rel == "alternate":
            rec.setdefault("hreflang", {})[lang] = attr(t, "href")

    m = re.search(r"<title[^>]*>(.*?)</title>", body, re.S | re.I)
    rec["title"] = html.unescape(re.sub(r"\s+", " ", m.group(1))).strip() if m else None
    m = re.search(r"<html[^>]*\blang=\"([^\"]+)\"", body, re.I)
    rec["lang"] = m.group(1) if m else None
    rec["h1"] = len(re.findall(r"<h1\b", body, re.I))
    types = []
    for js in re.findall(r"<script[^>]*application/ld\+json[^>]*>(.*?)</script>", body, re.S | re.I):
        types += re.findall(r'"@type"\s*:\s*"([^"]+)"', js)
    rec["schema"] = sorted(set(types))
    main = re.sub(r"(?s)<(script|style|nav|header|footer|noscript)[^>]*>.*?</\1>", " ", body)
    rec["words"] = len(re.sub(r"<[^>]+>", " ", main).split())
    rec["img_no_alt"] = sum(1 for i in re.findall(r"<img\b[^>]*>", body, re.I) if attr(i, "alt") is None)
    rec["bytes"] = len(body.encode("utf-8"))
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("base", nargs="?")
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--delay", type=float, default=0.3)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--cache-bust", action="store_true")
    ap.add_argument("--urls")
    a = ap.parse_args()

    if a.urls:
        urls = [u.strip() for u in open(a.urls) if u.strip()]
    elif a.base:
        urls = sitemap_urls(a.base.rstrip("/"))
    else:
        sys.exit("Geef een basis-URL of --urls op.")
    if a.limit:
        urls = urls[: a.limit]
    if not urls:
        sys.exit("Geen URL's gevonden (sitemap ontbreekt of is leeg).")
    print(f"{len(urls)} URL's, {a.workers} tegelijk", file=sys.stderr)

    def job(u):
        target = u + (("&" if "?" in u else "?") + f"nc={random.randint(10**6, 10**7)}" if a.cache_bust else "")
        st, hd, body, sec = get(target)
        time.sleep(a.delay)
        return analyse(u, st, hd, body, sec)

    with open(a.out, "w") as f, ThreadPoolExecutor(max(1, min(a.workers, 5))) as ex:
        for i, rec in enumerate(ex.map(job, urls), 1):
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            if i % 50 == 0:
                print(f"  {i}/{len(urls)}", file=sys.stderr)
    print(f"klaar: {a.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
