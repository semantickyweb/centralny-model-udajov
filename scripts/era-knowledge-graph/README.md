# ERA Knowledge Graph – slovenský výrez

Tento downloader preberá **celý pomenovaný graf organizácie `0056`** z
verejného ERA RINF GraphDB. Nevykonáva mapovanie, obohatenie ani zmenu URI.
Výsledok je preto verný snapshot upstream grafu, ale z pohľadu provenance je
`derived-snapshot`: ERA neposkytuje samostatný verziovaný súbor iba pre
Slovensko.

## Spustenie

Požiadavky: `bash`, `curl`, `gzip`, `jq`, Apache Jena `riot` a `sha256sum`.

```bash
scripts/era-knowledge-graph/download-sk.sh
```

Predvolený výstup je
`raw/era-knowledge-graph/<UTC-dátum>/`. Iný adresár alebo stabilný dátum sa dá
zadať takto:

```bash
ERA_SNAPSHOT_DATE=2026-08-27 \
  scripts/era-knowledge-graph/download-sk.sh /tmp/era-sk-test
```

Downloader:

1. stiahne graf `http://data.europa.eu/949/graph/0056` cez RDF4J Statements
   endpoint ako N-Quads;
2. overí RDF syntax cez `riot`;
3. overí, že všetky entity s explicitným `era:inCountry` patria do `SVK`;
4. porovná počet stiahnutých riadkov s počtom trojíc v SPARQL endpoint-e;
5. vytvorí deterministicky komprimovaný `.nq.gz` súbor;
6. uloží inventár tried, pokrytie canonical URI, DCAT inventár, externé
   závislosti, metadata najnovšieho plného Zenodo dumpu, provenance manifest
   a SHA-256 checksumy.

Graf `0056` zámerne neobsahuje kópie všetkých externých zdrojov. Odkazuje na
ERA SKOS graf a na spoločný graf hraničných bodov. Ich počty sú v
`external-dependencies.csv`; tieto URI majú pri importe zostať referenciami na
ERA zdroje.

`sk-related-graphs.csv` inventarizuje všetky triedy s explicitným
`era:inCountry` nastaveným na `SVK` naprieč celým repozitárom. Kontrola
2026-08-28 našla okrem grafu `0056` aj 24 entít
`era:ReferenceBorderPoint` v spoločnom grafe `graph/borders` a 25 slovenských
SKOS konceptov s jednou kolekciou v `graph/rinf/skos`. Hraničné body sú
kandidátom na doplnkový slovenský dataset; SKOS zdroje majú zostať
referenčnými číselníkmi.

## Generovanie Slovpedia katalógu a triedových pohľadov

Konfigurácia `dcat-datasets.json` rozdeľuje fyzický graf `0056` na logické
datasety podľa dôležitých tried ERA. Katalóg a samostatné `CONSTRUCT` dotazy sa
obnovia príkazom:

```bash
scripts/era-knowledge-graph/generate-dcat.py \
  --output abox/slovpedia/era-sk/era-sk-knowledge-graph/2026-08-27
```

Pre každý dataset generátor vytvorí čitateľný SPARQL dotaz `queries/*.rq` aj
jednoriadkovú URL-encoded podobu `queries/*.url`. Súbor `.url` obsahuje celú
spustiteľnú URL endpointu s parametrom `query`, vhodnú na vloženie do metadát
na `data.slovensko.sk`.

Výsledky dotazov sa fyzicky uložia takto:

```bash
scripts/era-knowledge-graph/materialize-datasets.py \
  --source raw/era-knowledge-graph/2026-08-27/era-rinf-sk-graph-0056.nq.gz \
  --output abox/slovpedia/era-sk/era-sk-knowledge-graph/2026-08-27
```

Potom treba generátor spustiť ešte raz, aby do DCAT doplnil veľkosti súborov.
Každý dataset dostane uloženú `.ttl.gz` distribúciu (Turtle komprimovaný
pomocou gzip), priamu živú SPARQL distribúciu aj distribúciu cez
`dcat:DataService`. Lokálne metadátové URI sú
pod `https://slovpedia.eu/`; obsahové ERA URI sa nemenia.
