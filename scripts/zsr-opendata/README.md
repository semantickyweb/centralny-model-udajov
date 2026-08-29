# Generovanie otvorených dát ŽSR

Tento adresár obsahuje publikačný proces. Konfigurácia `datasets.json`
eviduje zdroje, datasety a spoločnú URI politiku. Skript
`build_zsr_opendata.py` načíta slovenský ERA/RINF snapshot a vytvorí pre
každú nakonfigurovanú triedu samostatný Turtle dataset komprimovaný pomocou
gzip.

Požiadavky: Python 3 s balíkom `rdflib` a Apache Jena `riot` dostupný v
`PATH`.

Spustenie z koreňa repozitára:

```bash
scripts/zsr-opendata/build_zsr_opendata.py
```

Predvolené vstupné a výstupné cesty sú v `datasets.json`. Dajú sa prepísať:

```bash
scripts/zsr-opendata/build_zsr_opendata.py \
  --source raw/era-knowledge-graph/2026-08-27/era-rinf-sk-graph-0056.nq.gz \
  --output abox/semantickyweb/era-sk/zsr-opendata/2026-08-27
```

Výstup obsahuje `catalog.ttl`, `data/*.ttl.gz` a `manifest.json`. Každý
`dcat:Dataset` v katalógu má `prov:wasDerivedFrom` na zdrojový ERA graf.
Každá lokálna entita má URI `https://data.gov.sk/id/era/{class}/{id}` a dve väzby
`prov:wasDerivedFrom`: na pôvodnú ERA entitu a na zdrojový graf ERA.
Prepojenia na iné nakonfigurované entity sa prepíšu na ich lokálne URI.
Referencie na ERA ontológiu, číselníky a entity mimo registra zostávajú
nezmenené.

Stratégia `source-uri-last-segment` dočasne preberá posledný segment pôvodnej
URI entity ERA. Napríklad traťová koľaj dostane krátke ERA ID `d5cb573041`
namiesto zloženého identifikátora z `era:canonicalURI`. Generátor kontroluje,
že v rámci triedy nevzniknú dve rovnaké lokálne URI; pri kolízii skončí chybou.
Po nájdení oficiálneho národného číselníka sa stratégia identít znovu
vyhodnotí pred stabilnou publikáciou.

## Pomocný vstup: ŽSR InfoMapa

Register obsahuje aj InfoMapu ako pomocný národný vstup a kandidáta na autoritu
slovenských identít pre entity, ktoré pokrýva. Nie je datasetom publikovaným
z CMÚ a generátor z nej nevytvára distribúcie v `abox`. Lokálne sú dostupné dva
zdrojové súbory vrstvy 3:

- 1 154 dopravných bodov s jedinečným `Id`, názvom, súradnicami a platnosťou;
- 1 277 sieťových úsekov s jedinečným `Id`, koncovými bodmi, dĺžkou a
  geometriou.

Všetky odkazy úsekov na počiatočný a koncový bod sú platné. Vydavateľom sú
Železnice Slovenskej republiky
(`<https://data.gov.sk/id/legal-subject/31364501>`). Identita bude používať
priamo pole `Id`:

```text
https://data.gov.sk/id/era/operational-point/13016100
https://data.gov.sk/id/era/network-section/10931
```

InfoMapa entity sa nemajú automaticky stotožniť s ERA entitami; prípadné
párovanie bude samostatný, kontrolovateľný medzikrok publikačného procesu.
Endpoint na dereferencovanie zatiaľ neexistuje. Navrhované URI začnú verejne
vracať HTML, Turtle alebo JSON-LD až po nasadení resolvera na `data.gov.sk`.
Pre pomocný vstup InfoMapa je z medzinárodného licenčného číselníka zvolená
`http://publications.europa.eu/resource/authority/licence/CC0` (Creative
Commons CC0 1.0 Universal).

Nový dataset sa pridáva takto:

1. zdroj sa zaeviduje v `sources` vrátane pôvodu a licencie;
2. dataset sa pridá do `datasets` so stavom `planned`;
3. určí sa podporovaná `idStrategy` a overí sa jej stabilita a jednoznačnosť;
4. dataset sa prepne do stavu `ready` a spustí sa generátor.
