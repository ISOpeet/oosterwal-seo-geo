# oosterwal-seo-geo

SEO- en GEO-audit voor Claude, met oorzaakanalyse en veilige fixes. Gebouwd uit
echte audits: time-outs onder crawlerverkeer, revisie-explosies in WordPress,
dubbele paginaladingen door cache-plugins, noindex-pagina's in meertalige
sitemaps, kannibalisatie, en de stappen om dat aantoonbaar op te lossen.

## Wat zit erin

```
skills/seo-geo-audit/
  SKILL.md                    werkwijze: meten, verklaren, prioriteren, fixen, rapporteren
  scripts/crawl_site.py       crawlt de hele sitemap (status, tijd, cache, meta, hreflang, schema)
  scripts/analyze.py          zet de crawl om in bevindingen per ernst
  scripts/geo_check.py        AI-crawlertoegang, llms.txt, server-side rendering, headers
  references/root-causes.md   oorzakenboek: symptoom, meting, fix
  references/fix-workflow.md  veilig fixen op een live site
```

De scripts gebruiken alleen de Python-standaardbibliotheek.

## Installeren

### Claude Code (via deze marketplace)

```
/plugin marketplace add ISOpeet/oosterwal-seo-geo
/plugin install oosterwal-seo-geo@oosterwal
```

### claude.ai (ook voor een Team- of Enterprise-omgeving)

1. Download [`dist/seo-geo-audit.zip`](https://github.com/ISOpeet/oosterwal-seo-geo/raw/main/dist/seo-geo-audit.zip).
2. Ga naar Instellingen, Mogelijkheden, Skills en upload de ZIP.
3. Zet code-uitvoering aan. Heeft de omgeving geen internettoegang voor
   scripts, dan vraagt de skill om exports (sitemap, Ahrefs- of
   Search Console-CSV) of om een `crawl.jsonl` die elders is gemaakt.

### Los gebruiken

```bash
python3 skills/seo-geo-audit/scripts/geo_check.py https://example.com
python3 skills/seo-geo-audit/scripts/crawl_site.py https://example.com --out crawl.jsonl
python3 skills/seo-geo-audit/scripts/analyze.py crawl.jsonl
```

## Uitgangspunten

- Eerst meten, dan pas concluderen. Een melding uit een externe tool telt pas
  als je hem zelf reproduceert.
- Live-wijzigingen alleen met akkoord, met back-up buiten de webroot, dry run en
  hermeting met cache-buster.
- Permanente verwijderingen voert de eigenaar zelf uit.

## Licentie

MIT, Oosterwal Consultancy.
