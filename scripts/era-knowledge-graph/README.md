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

## Nadväzujúce spracovanie

Downloader vytvára iba overený zdrojový snapshot a inventáre. Starý generátor
Slovpedia katalógu a triedových pohľadov bol odstránený.

Nový publikačný proces ŽSR je evidovaný v `scripts/zsr-opendata/`. Bude
vychádzať z tohto snapshotu a používať URI
`https://data.gov.sk/{type}/era/{class}/{id}`. Implementuje sa po určení
stabilnej stratégie `{id}` pre každú triedu; pôvodné URI ERA zostanú
zachované ako zdroj a provenance.
