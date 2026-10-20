# Oorzakenboek: symptoom, echte oorzaak, fix

Lessen uit echte audits (okt 2026). Begin bij het symptoom, controleer de oorzaak
met de genoemde meting, en fix pas als de meting het bevestigt. Een symptoom kan
meerdere oorzaken hebben; meet altijd voor je concludeert.

## Time-outs en 5xx onder crawlerverkeer

| Symptoom | Meting | Mogelijke oorzaak |
|---|---|---|
| 500 na 6 tot 15 s, steeds andere URL's, ongeveer één per minuut | Tijdelijke fatal-logger (zie hieronder) | Een periodieke taak (WP-cron, plugin) loopt vast op geheugen |
| Fatal "Allowed memory size exhausted" in `class-wpdb.php` tijdens `wp_after_insert_post` | Revisies tellen per post: `SELECT post_parent, COUNT(*) FROM wp_posts WHERE post_type='revision' GROUP BY post_parent ORDER BY 2 DESC` | Een script werkt posts elke run bij zonder dat er iets verandert; elke update maakt een revisie, en WordPress laadt bij elke save alle revisies |
| Pagina's 1 tot 2,5 s, alle `cache-control: no-store` | `curl -I` op een pagina; zoek naar `headers()`/`cookies()` in de root-layout (Next.js) | De hele app rendert dynamisch; elke request haalt data opnieuw op |
| "items over 2MB can not be cached" in de serverlog | Grootte van de API-respons meten | Next.js data cache weigert grote responses; cache in geheugen of de respons verkleinen |

**Fatal-logger zonder WP_DEBUG** (mu-plugin, tijdelijk, achteraf verwijderen):
haak in op de filter `wp_php_error_message` (WordPress' eigen fatal handler stopt
met `wp_die`, dus een gewone shutdown-functie draait niet), log `$error` plus de
laatste query (via de `query`-filter) en `$GLOBALS['wp_current_filter']` naar een
bestand **buiten de webroot**.

**Fix revisie-explosie:** werk alleen bij als de waarde echt verandert, en zonder
revisie (`remove_action('wp_after_insert_post', 'wp_save_post_revision_on_insert')`
rond de update). Zet `WP_POST_REVISIONS` op 10. Ruim op met een SQL-batch die per
post de nieuwste 10 houdt; maak eerst een volledige `mysqldump`. Let op: `wp db
query` geeft bij een DELETE geen bruikbaar rijenaantal terug; tel vóór en na.

## Dubbele paginalading en opgeblazen analytics

| Symptoom | Meting | Oorzaak |
|---|---|---|
| Lighthouse toont twee Document-requests voor één pagina | Netwerklijst in de Lighthouse-JSON; zoek `guest.vary.php` | LiteSpeed Guest Mode: nieuwe bezoekers krijgen eerst een gastpagina en daarna een reload. GA4 telt dan twee page_views |

Fix: `wp litespeed-option set guest false`, tenzij `guest_optm` bewust aan staat.

## LCP-element is de cookiebanner

Als Lighthouse het tekstblok van de consentbanner (Complianz, Cookiebot) als LCP
aanwijst, is de banner groter dan de hero-kop en verschijnt hij laat. Meet in de
browser de oppervlakte (`getBoundingClientRect`) van de H1 en van de bannertekst.
Fix: bannertekst inkorten (beter leesbaar) tot hij kleiner is dan de H1; dan is de
H1 het LCP-element en die staat er bij de eerste paint.

## Onnodige scripts op elke pagina

Google Site Kit "Sign in with Google" laadt `accounts.google.com/gsi/client`
(100 KB) op elke pagina, ook als One Tap uit staat. Alleen nodig waar een
inlogformulier staat. Fix: footer-output bufferen en het blok weghalen op pagina's
zonder inlogformulier (mu-plugin).

## Cache- en CDN-valkuilen

- **Hostinger hCDN** (`x-hcdn-cache-status`) cachet HTML uren en heeft meerdere
  edges. `litespeed-purge` raakt die cache niet; legen kan alleen via hPanel, en
  dat komt niet altijd op alle edges aan. Verifieer met en zonder `?nc=` en kijk
  naar `age` en de edge-naam in `x-hcdn-request-id`.
- **Altijd meten met cache-buster** na een wijziging (`crawl_site.py --cache-bust`),
  anders meet je de oude kopie.
- **Rank Math**: de optie `open_graph_image` (standaardafbeelding) zetten via
  `update_option` kan og:image sitebreed laten verdwijnen. Gebruik in plaats daarvan
  de action `rank_math/opengraph/facebook/add_additional_images` met
  `$image->add_image_by_url()`. Afbeeldingen lager dan 200 px worden geweigerd; maak
  een deelafbeelding van 1200x630.

## Sitemap en hreflang

- **noindex in sitemap bij meertalige catalogi:** de sitemap rolt elk product uit
  over alle talen, maar onvertaalde pagina's tonen een fallback met noindex. Neem
  alleen talen op waarin het item echt bestaat (vergelijk de slug-sets per taal uit
  de API), en laat hreflang alleen naar die talen wijzen.
- **hreflang niet wederkerig:** controleer of het doel terugverwijst. Taaldetectie
  die op één meta-veld leunt (bijvoorbeeld alleen `_isoc_page_lang`) mist posts die
  een ander veld gebruiken; laat de detectie op beide terugvallen.
- **og:locale en schema inLanguage** moeten de paginataal volgen, niet de sitetaal.

## Content en meta

- **Sjabloontekst** in omschrijvingen ("practical guide for executives...",
  "Overzichtspagina voor...") telt als dubbele content; herschrijf per pagina.
- **Korte titels** (< 30 tekens) zonder merknaam: herschrijf naar zoekwoord eerst,
  45 tot 62 tekens, en voeg een vangnet toe dat de merknaam achter titels < 40 zet.
- **Kannibalisatie:** meerdere pagina's met dezelfde intentie (bijv. "management
  review" en "directiebeoordeling"). Kies de beste URL, voeg de beste inhoud samen,
  301 de rest, werk interne links en "gerelateerd"-lijsten bij, zet de oude pagina's
  op concept.
- **Weescategorieën** ontstaan als `wp post term set <id> category 6` zonder
  `--by=id` wordt uitgevoerd: WordPress maakt dan een categorie met de naam "6".

## Supply-chain-incidenten

Bij een melding over een besmette pluginversie (zoals Rank Math SEO PRO 3.0.123,
okt 2026): inventariseer alle WordPress-installaties per account, zoek de versie,
de bestandsdatums in het besmettingsvenster en de IOC's uit het advies (opties in
`wp_options`, nep-beheerders, nepbestanden in `wp-includes`, `.cache`-bestanden met
PHP, cron-markers, strings in code). Alleen lezen; rapporteer en laat de eigenaar
beslissen.
