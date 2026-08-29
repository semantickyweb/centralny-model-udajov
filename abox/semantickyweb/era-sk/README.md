# Otvorené dáta ŽSR podľa modelu ERA

Cieľom je vytvoriť nové datasety ŽSR odvodené prednostne z európskych
zdrojov. Prvým zdrojom je slovenský výrez ERA/RINF; ďalšie európske a
slovenské zdroje sa budú pridávať do registra až po overení pôvodu, licencie
a spôsobu identifikácie záznamov.

Starý ručný návrh `zsr-opendata/2-0` sa nepoužíva. Jeho CSV, transformery a
návrhový dokument boli odstránené, aby sa nemiešali s novým dátovým modelom.

## URI politika

Všetky nové lokálne URI používajú záväzný vzor:

```text
https://data.gov.sk/{type}/era/{class}/{id}
```

- `{type}` je druh zdroja, najmä `id` pre entity a `set` pre datasety,
  katalógy a distribúcie;
- `{class}` je stabilný názov triedy v angličtine, zapísaný ako lowercase
  kebab-case;
- `{id}` je stabilný identifikátor nezávislý od názvu a ostatných meniteľných
  vlastností entity.

Príklady:

```text
https://data.gov.sk/id/era/operational-point/SK000123
https://data.gov.sk/id/era/section-of-line/12345
https://data.gov.sk/set/era/dataset/operational-points
https://data.gov.sk/set/era/catalog/zsr-open-data
```

Zdrojová URI ERA pod `http://data.europa.eu/949/` sa v novom datasete
zachovajú ako provenance alebo mapovanie na zdroj. Nenahrádzajú publikačné
URI ŽSR. `owl:sameAs` sa použije iba vtedy, keď je potvrdená totožnosť oboch
entít; samotné odvodenie sa vyjadrí cez `prov:wasDerivedFrom` alebo
`dct:source`.

## Počiatočné datasety

Počiatočný zoznam vychádza z tried dostupných v grafe ERA/RINF organizácie
`0056`: operačné body, úseky tratí, traťové koľaje, vlečkové a odstavné
koľaje, nástupištné hrany, tunely, trakčné systémy, systémy detekcie vlakov,
ETCS, kilometrické body a primárne lokality.

Strojovo čitateľný zoznam a stav prípravy je v
`scripts/zsr-opendata/datasets.json`. Nový dataset sa najprv pridá do tohto
registra spolu so zdrojom, ERA triedou a pravidlom tvorby identifikátora.

## Spracovanie zdrojov

Pre každý zdroj sa uchová:

- pôvodná URI alebo identifikátor záznamu;
- dátum a verzia zdrojového snapshotu;
- licencia a pôvodca;
- pravidlo mapovania na lokálne URI;
- provenance jednotlivých odvodených tvrdení.

Referenčný snapshot európskych dát je uložený v
`raw/era-knowledge-graph/<dátum>/`. Je to vstup do nového procesu, nie hotový
publikačný balík ŽSR. Existujúce historické výstupy so Slovpedia URI sa nesmú
zamieňať za nové dáta; nové výstupy generuje `scripts/zsr-opendata/` podľa
tejto URI politiky.

Súbory ŽSR InfoMapa v `raw/zsr-infomapa/` sú iba pomocné vstupy na budúce
overenie národných identít a párovanie s ERA. Nie sú výstupom CMÚ a v `abox`
sa z nich nepublikuje samostatný dataset.

Publikované RDF distribúcie budú Turtle (`.ttl.gz`). Gzip je iba kompresia;
RDF formát zostáva `text/turtle`.
