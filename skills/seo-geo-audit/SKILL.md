---
name: seo-geo-audit
description: >-
  Volledige SEO- en GEO-audit van een website, met oorzaakanalyse en veilige
  fixes. Crawlt de hele sitemap, controleert titels, omschrijvingen, canonical,
  hreflang, noindex, structured data, snelheid, AI-crawlertoegang en llms.txt,
  en vertaalt meldingen van Ahrefs, Semrush, Google Search Console, diib of
  Rank Math naar de echte oorzaak. Gebruik deze skill zodra iemand een site wil
  laten doorlichten, een audit- of Ahrefs-rapport deelt, vraagt waarom pagina's
  traag zijn, time-outs of 5xx geven, niet geïndexeerd worden, of slecht scoren
  op Core Web Vitals, of wil weten hoe vindbaar een site is in ChatGPT,
  Perplexity, Gemini en Google AI Overviews.
---

# SEO + GEO audit met oorzaakanalyse

Deze skill doet drie dingen: **meten** (de hele site, niet een steekproef),
**verklaren** (van symptoom naar echte oorzaak) en **fixen** (veilig, controleerbaar,
met voor-en-na). Een rapport met honderd meldingen helpt niemand; een lijst van
vijf oorzaken met bewezen fixes wel.

Werk altijd in deze volgorde. Sla geen meting over om sneller bij een fix te zijn:
de duurste fouten uit de praktijk kwamen van aannames die niet gemeten waren.

## 1. Nulmeting

Gebruik de scripts in `scripts/` (alleen Python-standaardbibliotheek, werken
overal waar Python en internet zijn):

```bash
python3 scripts/geo_check.py https://example.com            # AI-crawlers, llms.txt, SSR, headers
python3 scripts/crawl_site.py https://example.com --out crawl.jsonl --workers 2
python3 scripts/analyze.py crawl.jsonl --json findings.json
```

- Begin met `--workers 2`. Geeft de site al bij 2 tegelijk time-outs, dan is
  dat zelf de belangrijkste bevinding (zie het oorzakenboek).
- Meet na elke wijziging ook met `--cache-bust`, anders meet je de CDN.
- Heeft de omgeving geen internettoegang voor scripts (sommige
  chatomgevingen), vraag dan om exports: de sitemap-URL, een Ahrefs- of
  Search Console-export (CSV), of draai de scripts op een machine die wel
  internet heeft en laat de `crawl.jsonl` uploaden. Analyseer die met
  `analyze.py`.

Is er een externe audit (Ahrefs, Semrush, diib, Rank Math SEO Analyzer,
PageSpeed), zet de meldingen dan naast je eigen crawl. Neem een melding pas
over als je hem zelf kunt reproduceren; tools tellen soms tijdelijke fouten mee.

## 2. Van symptoom naar oorzaak

Lees `references/root-causes.md`. Daar staan de symptomen die het vaakst
voorkomen, de meting die de oorzaak bevestigt en de fix. Kern:

- **Groepeer.** 285 time-outs zijn meestal één oorzaak. Zoek het patroon:
  welke paginatypes, welk tijdstip, welke serverlog-regel?
- **Meet de server, niet de cache.** Vergelijk met en zonder `?nc=`, lees
  `cache-control`, `age` en de cachestatusheaders.
- **Zoek in logs en code**, niet alleen in de HTML. Een 500 zonder logregel
  vraagt om een tijdelijke logger; een trage pagina vraagt om de datafetch erachter.
- **Bewijs voor je fixt.** Een oorzaak is pas bevestigd als een meting hem
  laat zien (een getal, een logregel, een netwerkverzoek).

## 3. Prioriteren

Orden fixes op impact per uur werk:

1. **Kapot:** 5xx, time-outs, 404's in de sitemap, noindex op pagina's die
   moeten ranken, robots.txt die crawlers blokkeert.
2. **Indexatie en signalen:** canonical, hreflang (wederkerig, juiste taal),
   noindex-pagina's uit de sitemap, dubbele titels en omschrijvingen, og:locale.
3. **Snelheid:** LCP en TTFB. Kijk eerst naar dubbele paginaladingen, onnodige
   scripts en ongecachte datafetches; pas daarna naar CSS en afbeeldingen.
4. **Inhoud en GEO:** dunne pagina's verdiepen (circa 1.000 woorden echte
   inhoud), kannibalisatie samenvoegen, direct-antwoordblokken, FAQ-schema,
   llms.txt, auteur- en bronvermelding (E-E-A-T).

## 4. Fixen

Volg `references/fix-workflow.md`. Kort: akkoord vragen voor live-wijzigingen,
back-up buiten de webroot, dry run vóór apply, bron in versiebeheer, valideren,
cache legen, hermeten met cache-buster, committen.

Bij teksten (titels, omschrijvingen, artikelen):

- **Titels:** zoekwoord eerst, 45 tot 62 tekens, uniek over de hele site,
  geen merknaam nodig als het vangnet die toevoegt.
- **Omschrijvingen:** 110 tot 158 tekens, concreet (wat leest de bezoeker,
  wat levert het op), geen sjabloonzinnen.
- **Artikelen:** feitelijk, met bron of voorbehoud bij wetgeving en data die
  kunnen schuiven; geen verzonnen claims ("we zien dat directeuren..."). Interne
  links alleen naar URL's die 200 geven.
- Schrijf in de taal van de pagina; houd aanspreekvorm (je/u) consistent.

## 5. Rapporteren

Rapporteer in de taal van de gebruiker, kort en eerlijk:

- **Eerst het antwoord:** wat er mis was en of het nu opgelost is.
- **Voor en na in getallen** (statuscodes, seconden, aantallen).
- **Wat de eigenaar zelf moet doen** (CDN legen, deployen, opschoonscript
  draaien, een nieuwe crawl in de externe tool starten).
- **Wat bewust niet is gedaan en waarom.**

Een PDF in huisstijl nodig? Gebruik dan de skill `seo-geo-report` als die
beschikbaar is en voed die met `findings.json`.

## Grenzen

- Respecteer robots.txt en de server: maximaal 5 verzoeken tegelijk, liever 2.
- Geen wachtwoorden, API-sleutels of betaalgegevens invoeren of opslaan.
- Permanente verwijderingen voert de eigenaar zelf uit.
- Klantdata (exports, logs met persoonsgegevens) niet in git of in publieke
  plekken; ruim tijdelijke bestanden op.
