#!/usr/bin/env python3
"""
analyze.py: zet een crawl (crawl_site.py) om in bevindingen per categorie.

Gebruik:
  python3 analyze.py crawl.jsonl                 -> leesbaar overzicht
  python3 analyze.py crawl.jsonl --json out.json -> ook als JSON (voor rapportage)

Regels (bewust streng, afgestemd op wat Google, Ahrefs en AI-zoekmachines meten):
- status anders dan 200 in de sitemap, time-outs, trage pagina's (> 2 s)
- titel ontbreekt, < 30 of > 65 tekens, dubbel
- meta-omschrijving ontbreekt, > 160 tekens, dubbel, of sjabloontekst
- noindex in de sitemap, canonical die niet naar zichzelf wijst
- hreflang: doel niet 200, niet wederkerig, geen x-default, html lang klopt niet
- geen of meerdere H1's, dunne inhoud (< 300 woorden), geen schema, geen og:image
- afbeeldingen zonder alt-attribuut
"""
import argparse
import collections
import json
import re
import statistics

TEMPLATE_HINTS = re.compile(
    r"practical guide for|praktische gids voor|what it means, practical steps|wat het betekent, welke stappen"
    r"|overview hub for|overzichtspagina voor|lorem ipsum|\[todo",
    re.I,
)


def load(path):
    return [json.loads(line) for line in open(path) if line.strip()]


def norm(u):
    return (u or "").split("#")[0].rstrip("/")


def run(rows):
    f = collections.OrderedDict()

    def add(key, label, items, severity):
        if items:
            f[key] = {"label": label, "severity": severity, "count": len(items), "examples": items[:15]}

    ok = [r for r in rows if r.get("status") == 200]
    by_url = {norm(r["url"]): r for r in rows}

    add("non200", "URL's in sitemap zonder 200", [f'{r["status"]} {r["url"]} {r.get("location") or r.get("error") or ""}'.strip() for r in rows if r.get("status") != 200], "critical")
    secs = sorted(r["seconds"] for r in ok) or [0]
    add("slow", "Trage pagina's (> 2 s)", [f'{r["seconds"]}s {r["url"]}' for r in sorted(ok, key=lambda r: -r["seconds"]) if r["seconds"] > 2], "high")

    titles = collections.Counter(r.get("title") for r in ok)
    add("title_missing", "Titel ontbreekt", [r["url"] for r in ok if not r.get("title")], "high")
    add("title_dup", "Dubbele titels", [f'{r["title"]} | {r["url"]}' for r in ok if r.get("title") and titles[r["title"]] > 1], "high")
    add("title_short", "Titel korter dan 30 tekens", [f'{len(r["title"])} {r["title"]} | {r["url"]}' for r in ok if r.get("title") and len(r["title"]) < 30], "medium")
    add("title_long", "Titel langer dan 65 tekens", [f'{len(r["title"])} {r["url"]}' for r in ok if r.get("title") and len(r["title"]) > 65], "low")

    descs = collections.Counter(r.get("desc") for r in ok if r.get("desc"))
    add("desc_missing", "Meta-omschrijving ontbreekt", [r["url"] for r in ok if not r.get("desc")], "medium")
    add("desc_dup", "Dubbele meta-omschrijvingen", [r["url"] for r in ok if r.get("desc") and descs[r["desc"]] > 1], "medium")
    add("desc_template", "Sjabloontekst in omschrijving", [f'{r["url"]} | {r["desc"][:70]}' for r in ok if r.get("desc") and TEMPLATE_HINTS.search(r["desc"])], "high")
    add("desc_long", "Omschrijving langer dan 160 tekens", [f'{len(r["desc"])} {r["url"]}' for r in ok if r.get("desc") and len(r["desc"]) > 160], "low")

    add("noindex_in_sitemap", "noindex-pagina in sitemap", [f'{r["url"]} ({r["robots"]})' for r in ok if "noindex" in (r.get("robots") or "").lower()], "high")
    add("canonical_other", "Canonical wijst naar andere URL", [f'{r["url"]} -> {r["canonical"]}' for r in ok if r.get("canonical") and norm(r["canonical"]) != norm(r["url"])], "medium")
    add("canonical_missing", "Geen canonical", [r["url"] for r in ok if not r.get("canonical")], "low")

    hl_bad, hl_nonrecip, hl_nodefault = [], [], []
    for r in ok:
        h = r.get("hreflang") or {}
        if h and "x-default" not in h:
            hl_nodefault.append(r["url"])
        for lang, target in h.items():
            t = by_url.get(norm(target))
            if t and t.get("status") != 200:
                hl_bad.append(f'{r["url"]} -> {lang} {target} ({t.get("status")})')
            if lang != "x-default" and t and norm(target) != norm(r["url"]):
                back = [norm(x) for x in (t.get("hreflang") or {}).values()]
                if norm(r["url"]) not in back:
                    hl_nonrecip.append(f'{r["url"]} -> {lang} {target}')
    add("hreflang_broken", "hreflang naar redirect of kapotte pagina", hl_bad, "high")
    add("hreflang_nonrecip", "hreflang niet wederkerig", hl_nonrecip, "medium")
    add("hreflang_nodefault", "hreflang zonder x-default", hl_nodefault, "low")

    add("h1", "Geen of meerdere H1's", [f'{r["h1"]}x {r["url"]}' for r in ok if r.get("h1") != 1], "medium")
    add("thin", "Dunne inhoud (< 300 woorden)", [f'{r["words"]} {r["url"]}' for r in sorted(ok, key=lambda r: r.get("words", 0)) if r.get("words", 0) < 300], "medium")
    add("no_schema", "Geen structured data", [r["url"] for r in ok if not r.get("schema")], "medium")
    add("no_og_image", "Geen og:image", [r["url"] for r in ok if not r.get("og_image")], "low")
    add("img_alt", "Afbeeldingen zonder alt", [f'{r["img_no_alt"]} {r["url"]}' for r in ok if r.get("img_no_alt")], "low")

    cache = collections.Counter()
    for r in ok:
        for k, v in (r.get("cache") or {}).items():
            if k != "age":
                cache[f"{k}: {v}"] += 1

    summary = {
        "urls": len(rows),
        "status": dict(collections.Counter(r.get("status") for r in rows)),
        "seconds_median": round(statistics.median(secs), 2),
        "seconds_p90": round(secs[int(len(secs) * 0.9) - 1 if len(secs) > 1 else 0], 2),
        "schema_types": dict(collections.Counter(t for r in ok for t in r.get("schema", [])).most_common(12)),
        "cache_headers": dict(cache.most_common(8)),
    }
    return summary, f


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("crawl")
    ap.add_argument("--json")
    a = ap.parse_args()
    summary, findings = run(load(a.crawl))
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    for key, v in sorted(findings.items(), key=lambda kv: order[kv[1]["severity"]]):
        print(f'\n[{v["severity"].upper()}] {v["label"]}: {v["count"]}')
        for e in v["examples"][:8]:
            print("   ", e)
    if not findings:
        print("\nGeen bevindingen.")
    if a.json:
        json.dump({"summary": summary, "findings": findings}, open(a.json, "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
