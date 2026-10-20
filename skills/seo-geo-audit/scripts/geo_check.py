#!/usr/bin/env python3
"""
geo_check.py: snelle GEO-basiscontrole van een domein.

Gebruik:  python3 geo_check.py https://example.com [een-contentpagina-pad]

Controleert:
- robots.txt: regels voor AI-crawlers (GPTBot, ClaudeBot, PerplexityBot, Google-Extended,
  OAI-SearchBot, CCBot, Applebot-Extended, Bytespider, Amazonbot) en Content-Signal
- of die crawlers de pagina echt krijgen (statuscode met hun user-agent)
- llms.txt en llms-full.txt: aanwezig, aantal links
- server-side rendering: staat de tekst al in de ruwe HTML?
- beveiligingsheaders die vertrouwen uitstralen (HSTS, nosniff, frame-options)
"""
import re
import sys
import urllib.request

BOTS = ["GPTBot", "OAI-SearchBot", "ClaudeBot", "PerplexityBot", "Google-Extended",
        "CCBot", "Applebot-Extended", "Bytespider", "Amazonbot"]


def get(url, ua="Mozilla/5.0 (compatible; SEO-GEO-Audit/1.0)"):
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": ua}), timeout=25)
        return r.status, dict(r.headers), r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), ""
    except Exception as e:
        return 0, {}, str(e)


def robots_rules(txt, bot):
    """Grove interpretatie: geeft 'blocked' als er een Disallow: / geldt voor de bot of voor *."""
    groups, cur = [], None
    for line in txt.splitlines():
        line = line.split("#")[0].strip()
        if not line:
            continue
        k, _, v = line.partition(":")
        k, v = k.strip().lower(), v.strip()
        if k == "user-agent":
            if cur is None or cur["rules"]:
                cur = {"agents": [], "rules": []}
                groups.append(cur)
            cur["agents"].append(v.lower())
        elif k in ("allow", "disallow") and cur is not None:
            cur["rules"].append((k, v))
    specific = [g for g in groups if bot.lower() in g["agents"]]
    use = specific or [g for g in groups if "*" in g["agents"]]
    for g in use:
        if ("disallow", "/") in g["rules"]:
            return "geblokkeerd"
    return "toegestaan"


def main():
    base = sys.argv[1].rstrip("/")
    page = base + (sys.argv[2] if len(sys.argv) > 2 else "/")
    st, _, robots = get(base + "/robots.txt")
    print(f"robots.txt: {st}")
    sig = re.findall(r"(?im)^content-signal:.*$", robots)
    print("Content-Signal:", sig[0] if sig else "geen")
    print("\nAI-crawlers (robots.txt / echte respons):")
    for b in BOTS:
        s, _, _ = get(page, ua=f"Mozilla/5.0 (compatible; {b}/1.0)")
        print(f"  {b:18} {robots_rules(robots, b):12} HTTP {s}")
    for f in ("llms.txt", "llms-full.txt"):
        s, _, body = get(f"{base}/{f}")
        links = len(re.findall(r"\]\(https?://", body)) if s == 200 else 0
        print(f"\n{f}: HTTP {s}, {links} links")
    s, h, body = get(page)
    text = re.sub(r"(?s)<(script|style)[^>]*>.*?</\1>", " ", body)
    words = len(re.sub(r"<[^>]+>", " ", text).split())
    print(f"\nSSR-check {page}: {words} woorden in ruwe HTML ({'goed' if words > 150 else 'mogelijk JS-rendering'})")
    hl = {k.lower(): v for k, v in h.items()}
    for k in ("strict-transport-security", "x-content-type-options", "x-frame-options", "content-security-policy"):
        print(f"  {k}: {'ja' if k in hl else 'nee'}")


if __name__ == "__main__":
    main()
