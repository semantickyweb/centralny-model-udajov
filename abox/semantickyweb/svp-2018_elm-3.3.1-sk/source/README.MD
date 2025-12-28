# ŠVP Matematika (2. stupeň ZŠ) – PDF → TTL transformácia

Tento repozitár/skript transformuje PDF dokument Štátneho vzdelávacieho programu (ŠVP) pre **Matematiku – 2. stupeň ZŠ (ISCED 2)** do RDF v serializácii **Turtle (TTL)**.

Výstup je navrhnutý tak, aby:

- hlavná taxonómia bola navigovateľná cez **SKOS** (ročníky → témy → výkonové štandardy),
- výkonové štandardy (VS) a obsahové štandardy (OS) boli v **samostatných ConceptScheme**,
- VS boli prepojené na OS cez `skos:relatedMatch`,
- Learning Opportunity (LO) a Learning Achievement Specification (LAS) boli modelované cez **ELM**,
- z PDF sa **ignorovali** šumy (čísla strán, hlavičky, pätičky).

---

## 1) Vstup

### PDF
Skript očakáva PDF v dvojstĺpcovom layoute:

- ľavý stĺpec: **Výkonový štandard (VS)** – často s odrážkou (v dokumente býva „“)
- pravý stĺpec: **Obsahový štandard (OS)** – zoznam pojmov/obsahu

### Identifikácia tematických celkov (témy)
Témy sú fixne definované zoznamom `THEMES` v skripte (dodaný zoznam):

- „Vytvorenie oboru prirodzených čísel do a nad milión“
- „Počtové výkony s prirodzenými číslami“
- …
- „Grafické znázorňovanie závislostí“

Tento zoznam slúži na rozpoznanie začiatku sekcií.

### Identifikácia ročníka
Ročník sa z PDF vyčíta pomocou textu typu:

> „Žiak na konci 9. ročníka …“

Skript hľadá regex: `Žiak na konci (\d+). ročníka`

---

## 2) Výstupný RDF model

Používané ontológie / slovníky:

- **SKOS**: `http://www.w3.org/2004/02/skos/core#`
- **DCTERMS**: `http://purl.org/dc/terms/`
- **ELM (European Learning Model)**: `http://data.europa.eu/snb/model/ontology/`
- **Education ontology (data.gov.sk)**: `https://data.gov.sk/def/ontology/education/`

Namespace pre doménu Minedu:

- `minedu:` = `http://minedu.sk/def/`

### 2.1 ConceptScheme – hlavná taxonómia
Hlavná schéma:

- `minedu:scheme-matematika-2-stupen-zs`

**Top koncepty** sú ročníky:

- `minedu:rocnik-5`
- `minedu:rocnik-6`
- `minedu:rocnik-7`
- `minedu:rocnik-8`
- `minedu:rocnik-9`

Každý ročník má:

- `skos:topConceptOf minedu:scheme-matematika-2-stupen-zs`
- `skos:prefLabel "5. ročník"@sk`
- `skos:exactMatch https://data.gov.sk/def/study-grade/5`

Témy sú potom vložené ako `skos:narrower` pod príslušný ročník:

- `minedu:rocnik-5 skos:narrower minedu:theme-desatinne-cisla-...`
- `minedu:theme-... skos:broader minedu:rocnik-5`

### 2.2 ConceptScheme – výkonový štandard (VS)
Schéma výkonových štandardov:

- `minedu:svp-vykonovy-standard-matematika-2-stupen-zs`

Výkonové štandardy sú `skos:Concept` a sú naviazané pod tému:

- `minedu:theme-... skos:narrower <http://minedu.sk/def/vykonovy-standard/...>`
- `<...vykonovy-standard/...> skos:broader minedu:theme-...`

### 2.3 ConceptScheme – obsahový štandard (OS)
Schéma obsahových štandardov:

- `minedu:svp-obsahovy-standard-matematika-2-stupen-zs`

Obsahové štandardy sú `skos:Concept` (pojmy/obsah) a sú len v tejto schéme.

### 2.4 VS → OS mapovanie
Každý výkonový štandard (VS) je prepojený na množinu obsahových štandardov (OS) z tej istej tematickej sekcie:

- `VS skos:relatedMatch OS`

Tým vznikne navigácia typu: „čo mám vedieť (OS) pre to, aby som vedel urobiť (VS)“.

### 2.5 ELM: Learning Opportunity (LO) a Learning Achievement Specification (LAS)
Pre každú dvojicu (ročník, téma) skript generuje:

- `elm:LearningOpportunity` (LO)
- `elm:LearningAchievementSpecification` (LAS)

Vzťah LO → LAS:

- `elm:learningActivitySpecification`

Prepojenia a metadáta:

- `LO skos:related theme`
- `LAS skos:related LO`
- `LAS skos:related theme`
- `LO elm:educationLevel <.../ISCED_2>`
- `LO dct:subject <http://data.europa.eu/snb/isced-f/054>` (matematika)
- `LAS elm:ISCEDFCode <http://data.europa.eu/snb/isced-f/054>`
- `LO edu:studyGrade https://data.gov.sk/def/study-grade/5`
- `LAS edu:studyGrade https://data.gov.sk/def/study-grade/5`

### URI stratégie
- Témy: `minedu:theme-{slug}`
- Ročníky: `minedu:rocnik-{grade}`
- VS: `http://minedu.sk/def/vykonovy-standard/{slug}`
- OS: `http://minedu.sk/def/obsahovy-standard/{slug}`
- LO: `http://minedu.sk/id/learning-opportunity/matematika-{grade}-rocnik-{slug(theme)}`
- LAS: `http://minedu.sk/id/learning-achievement-specification/{slug(theme)}-las-{grade}`

`slug()` je ASCII-normalizácia (diakritika preč), malé písmená, pomlčky.

---

## 3) Filtrovanie šumu z PDF (hlavička/pätička/čísla strán)

PDF obsahuje opakujúce sa prvky, ktoré sa **nemajú** stať konceptmi:

- čísla strán: `1`, `2`, `3`, …
- hlavička: „Matematika – nižšie stredné vzdelanie“
- pätička: „© Štátny pedagogický ústav“
- fragmenty ako „nižšie stredné vzdelanie“, „pedagogický ústav“

Skript používa agresívny substring filter (`NOISE_PATTERNS`), ktorý odfiltruje tieto texty ešte pred vytvorením VS/OS konceptov.

---

## 4) Inštalácia

### Požiadavky
- Python 3.10+
- balíky:
  - `pdfplumber`
  - `rdflib`

Inštalácia:

```bash
pip install pdfplumber rdflib
```

---

## 5) Spustenie

```bash
python svp_pdf_to_ttl.py /cesta/k/svp_matematika.pdf -o minedu_matematika_2stupen.ttl
```

Voliteľne môžeš doladiť hranicu stĺpcov (ak PDF nemá presne rovnaký layout):

```bash
python svp_pdf_to_ttl.py svp.pdf -o out.ttl --xsplit 380
```

---

## 6) Ako skript funguje (pipeline)

1. **Extract words** z PDF pomocou `pdfplumber`.
2. **Zoskupovanie slov do riadkov** podľa `y` pozície (tolerancia `ytol`).
3. **Rozdelenie riadka na ľavý/pravý stĺpec** podľa `xsplit`.
4. Detekcia:
   - začiatok **témy** (`THEMES`)
   - **ročník** (regex „Žiak na konci X. ročníka“)
   - VS položky (indikované „“ alebo následný riadok)
   - OS položky (pravý stĺpec)
5. Záznamy sa ukladajú ako:
   - `{theme, grade, vs[], os[]}`
6. Záznamy sa prevedú na RDF graf:
   - ročníky (topConcept)
   - témy pod ročníkom
   - VS pod témou
   - OS v OS scheme
   - VS `skos:relatedMatch` OS
   - LO/LAS pre (grade, theme)
7. Druhá „safety“ čistka odstráni VS/OS koncepty, ktoré by náhodou obsahovali šum.

---

## 7) Známé limity a odporúčania

- PDF extrakcia je heuristická: pri odlišnom layoute môže byť potrebné upraviť `--xsplit` alebo toleranciu `ytol` vo funkcii `split_lines`.
- Rozdelenie VS/OS je založené na predpoklade, že VS je vľavo a OS vpravo.
- Ak PDF používa iné symboly ako „“ pre VS, uprav detekciu v `parse_pdf()`.

---

## 8) Licencia / zdroj

Výstupné RDF používa `dct:source` pre uvedenie pôvodu:

- „Štátny vzdelávací program pre 2. stupeň ZŠ“@sk

PDF dokument môže mať vlastnú licenciu/podmienky použitia (nie je súčasťou tejto transformácie).

---

## 9) Rýchla kontrola výsledku (SPARQL tipy)

### Top koncepty (ročníky)
```sparql
SELECT ?c ?label WHERE {
  <http://minedu.sk/def/scheme-matematika-2-stupen-zs> <http://www.w3.org/2004/02/skos/core#hasTopConcept> ?c .
  OPTIONAL { ?c <http://www.w3.org/2004/02/skos/core#prefLabel> ?label }
}
```

### Témy pod 9. ročníkom
```sparql
SELECT ?t ?label WHERE {
  <http://minedu.sk/def/rocnik-9> <http://www.w3.org/2004/02/skos/core#narrower> ?t .
  OPTIONAL { ?t <http://www.w3.org/2004/02/skos/core#prefLabel> ?label }
}
```

### VS → OS mapovanie
```sparql
SELECT ?vsLabel ?osLabel WHERE {
  ?vs <http://www.w3.org/2004/02/skos/core#relatedMatch> ?os .
  ?vs <http://www.w3.org/2004/02/skos/core#prefLabel> ?vsLabel .
  ?os <http://www.w3.org/2004/02/skos/core#prefLabel> ?osLabel .
}
LIMIT 50
```

---