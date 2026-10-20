# Veilig fixen op een live site

Deze regels voorkomen dat een SEO-fix de site breekt. Ze komen uit echte
incidenten; sla er geen over.

## Voor elke wijziging

1. **Vraag akkoord** voor alles wat de live site raakt, tenzij de eigenaar dat al
   expliciet heeft gegeven voor deze specifieke stap. Lezen mag altijd.
2. **Back-up buiten de webroot.** Nooit `.bak`-bestanden naast PHP in de webroot:
   die zijn via het web te downloaden (broncodelek). Gebruik `~/backups/<site>-<datum>/`.
3. **Vergelijk lokaal met live** voordat je een bestand uploadt. Is live nieuwer,
   neem eerst de live-versie over.
4. **Database: eerst een volledige dump** (`mysqldump --single-transaction`, met
   een tijdelijk optiebestand met mode 600, daarna wissen). `wp db export` kan stil
   falen; controleer op "Dump completed" in de staart van het bestand.

## Tijdens het wijzigen

- **Scripts met dry run en apply.** Eerst tellen en tonen, dan pas uitvoeren.
  Leg oude waarden vast in een back-up-JSON.
- **Bron in versiebeheer.** Teksten (titels, omschrijvingen, artikelen) als
  bestanden in de repo (bijvoorbeeld TSV per taal) plus een idempotent
  toepassingsscript; de database volgt de repo, niet andersom.
- **Uploaden:** naar een tijdelijke map, `php -l`, dan `mv` naar de juiste plek.
  Nooit regex-edits direct op live PHP- of TypeScript-bestanden.
- **Permanente verwijdering** (revisies, posts, bestanden) voert de eigenaar zelf
  uit; jij bereidt het commando en de back-up voor.
- **Valideer teksten automatisch:** lengte (titel 40 tot 62, omschrijving 110 tot
  158), geen dubbelen over de hele site, geen sjabloonresten, geen em-streepjes,
  alle interne links geven 200.

## Na het wijzigen

1. **Cache legen:** plugin-cache (`wp litespeed-purge all`), en weet dat een
   externe CDN (Hostinger hCDN, Cloudflare) apart geleegd moet worden.
2. **Meet met cache-buster** (`?nc=`) en daarna zonder, om te zien wat bezoekers
   en crawlers echt krijgen.
3. **Volledige hercrawl** van de sitemap met `crawl_site.py` en `analyze.py`.
   Vergelijk met de nulmeting: elke fix moet een getal laten zakken.
4. **Commit** de bron met een bericht dat de oorzaak, de fix en de meting noemt.
5. **Rapporteer eerlijk:** wat is verbeterd (voor/na), wat nog openstaat en wat de
   eigenaar zelf moet doen (CDN legen, deployen, opschoonscript draaien).

## Snelheid meten

- PageSpeed Insights-API heeft een dagquotum. Draai Lighthouse lokaal:
  `npx -y lighthouse@12.6.1 <url> --only-categories=performance --form-factor=mobile --output=json --output-path=lh.json --chrome-flags="--headless=new"`
- Lees uit de JSON: `largest-contentful-paint-element` (welk element is LCP en
  welke fase kost de tijd), `network-requests` (dubbele documenten, onnodige
  scripts), `render-blocking-resources`.
- Labmetingen schommelen; draai minstens twee keer.
