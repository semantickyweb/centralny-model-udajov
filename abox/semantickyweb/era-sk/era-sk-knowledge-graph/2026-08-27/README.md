# Slovpedia – slovenské železničné datasety ERA

Tento adresár obsahuje publikovateľný snapshot logických datasetov odvodených
zo slovenského pomenovaného grafu ERA
`http://data.europa.eu/949/graph/0056` k dátumu 2026-08-27.

Nejde o súčasť Centrálneho modelu údajov. Slovpedia tu vystupuje ako lokálny
poskytovateľ metadát a tematických pohľadov; autorom zdrojových údajov zostáva
European Union Agency for Railways.

## Obsah

- `catalog.ttl` – DCAT katalóg 11 tematických datasetov;
- `queries/*.rq` – presný `CONSTRUCT` dotaz definujúci každý dataset;
- `queries/*.url` – celá jednoriadková URL s percent-encoded SPARQL dotazom;
- `data/*.ttl.gz` – uložený výsledok príslušného dotazu v komprimovanom
  Turtle;
- `data/manifest.json` – počty entít a statementov, veľkosti a SHA-256;
- `validation-report.ttl` – výsledok lokálnej DCAT-AP-SK SHACL validácie.

Každý dataset má tri distribúcie: uložený snapshot, živý výsledok
datasetového `CONSTRUCT` dotazu a prístup cez spoločnú ERA SPARQL službu.
Uložené súbory umožňujú dataset použiť aj bez opakovaného dotazovania ERA.

## URI politika

Lokálne URI katalógu, datasetov, distribúcií a služieb používajú doménu
`https://slovpedia.eu/`. Obsahové identifikátory entít sa neprepisujú:
v `.ttl.gz` zostávajú pôvodné URI ERA pod `http://data.europa.eu/949/`.

URI `data.gov.sk` sa používajú iba ako odkazy na externé oficiálne slovenské
slovníky DCAT-AP-SK a na registrovaný právny subjekt vydavateľa, nie ako
identifikátory katalógu alebo dátových zdrojov Slovpedie.

## Reprodukcia

Z koreňa repozitára:

```bash
scripts/era-knowledge-graph/generate-dcat.py \
  --output abox/slovpedia/era-sk/era-sk-knowledge-graph/2026-08-27

scripts/era-knowledge-graph/materialize-datasets.py \
  --source raw/era-knowledge-graph/2026-08-27/era-rinf-sk-graph-0056.nq.gz \
  --output abox/slovpedia/era-sk/era-sk-knowledge-graph/2026-08-27

# Druhé generovanie doplní do DCAT metadata veľkosti hotových súborov.
scripts/era-knowledge-graph/generate-dcat.py \
  --output abox/slovpedia/era-sk/era-sk-knowledge-graph/2026-08-27
```

Materializácia vykoná každý uložený query nad nemenným lokálnym N-Quads
snapshotom, výsledok syntakticky overí a vytvorí deterministický gzip.

## Katalogizácia do data.slovensko.sk

Slovpedia môže zverejniť `catalog.ttl` na stabilnej HTTPS adrese a registrovať
ho ako lokálny katalóg typu DCAT-AP dokument. Portál potom prevezme metadata
11 datasetov; fyzické `downloadURL` musia smerovať na verejne dostupné
`.ttl.gz` súbory pod `slovpedia.eu`.

Samotný ERA endpoint nie je lokálnym katalógom, pretože neobsahuje tento
Slovpedia `dcat:Catalog`. Je však správne ponechaný ako dátová služba a zdroj
živých distribúcií.

Lokálny shape súbor momentálne obsahuje `sh:maxCount 1` pre
`dcat:Catalog/dcat:dataset`. Preto pri katalógu s 11 datasetmi hlási jednu
známu cardinality chybu, hoci viac datasetov v katalógu je v súlade s DCAT 3.
