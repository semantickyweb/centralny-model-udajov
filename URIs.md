# Politika URI Centrálneho modelu údajov

> **Dočasný stav pre ERA:** URI `slovpedia.eu` sa používajú dovtedy, kým sa
> nerozhodne a neschváli autoritatívny priestor pre slovenské železničné
> entity. Cieľovým priestorom má byť `zsr.sk` alebo `data.gov.sk`. Podrobnosti
> uvádza [register URI pre ERA](URI-ERA.md).

Tento dokument určuje spoločné pravidlá tvorby a používania URI v komunitnej
verzii Centrálneho modelu údajov. Platí pre všetky domény vrátane ERA, ELM,
ELI, ESCO a EPO.

## Základné pravidlo

Pri výbere URI sa postupuje v tomto poradí:

1. Ak už existuje autoritatívne vydané URI entity, napríklad cez METAIS,
   `data.gov.sk`, európsky register alebo pôvodného vydavateľa, použije sa
   priamo.
2. Ak autoritatívne URI neexistuje, vytvorí sa komunitné URI v priestore
   `https://slovpedia.eu/`.

Pre tú istú entitu sa nesmie vytvoriť paralelné URI na `slovpedia.eu`, ak už
má autoritatívne URI. URI pod cudzou doménou, napríklad `data.gov.sk`, sa
nesmie svojvoľne vytvárať bez pravidla alebo oprávnenia jej prevádzkovateľa.
Samotná existencia oficiálneho identifikátora neopravňuje vytvoriť nový tvar
oficiálneho URI. Návrh takéhoto URI sa musí predložiť PS1; do jeho
schválenia sa používa komunitné URI `slovpedia.eu`.

## Doménové registre URI

Každá doména CMÚ vedie na koreňovej úrovni vlastný čitateľný register URI.
Register uvádza predmetné typy entít, ich triedy, URI vzory, zdroje
identifikátorov a stav použitia.

- [ERA – železničná infraštruktúra](URI-ERA.md)

## Verejný priestor URI

Entity bez autoritatívneho URI a komunitné datasety publikuje
`slovpedia.eu`:

```text
https://slovpedia.eu/id/{class}/{identifier}
https://slovpedia.eu/def/{domain}/{term}
https://slovpedia.eu/set/{dataset-id}
https://slovpedia.eu/set/{dataset-id}/resource/{distribution-id}
```

- `/id/` identifikuje konkrétne entity a zdroje.
- `/def/` identifikuje lokálne definované ontologické termy a profily.
- `/set/` identifikuje datasety a ich distribúcie.
- URI entity nesmie závisieť od formátu distribúcie ani od konkrétneho
  vydania datasetu.
- Termy prevzatých ontológií a číselníkov používajú svoje pôvodné URI.

## Kontrola existujúcich URI a prepájanie

Pred vytvorením nového URI sa musí prehľadať:

- celý `abox/` v aktuálnej vetve;
- podľa dostupnosti aj ostatné lokálne a vzdialene sledované Git vetvy CMÚ;
- príslušné autoritatívne registre a zdrojové datasety.

Zhody sa overujú prednostne podľa autoritatívneho URI, zdrojového
identifikátora alebo identifikátora registra. Názov je iba pomôcka na
vyhľadanie kandidáta a sám osebe nedokazuje totožnosť. Ak už entita má URI v
inom datasete alebo vetve, rovnaké URI sa znovu použije. Neisté zhody sa
nezlučujú automaticky.

Ak autorita vydá oficiálne URI až neskôr, nové výstupy ho začnú používať.
Pôvodné komunitné URI sa naň prepojí iba po preukázaní totožnosti a zmena
sa uvedie v provenance.

## Konfigurácia identít

Každý dátový produkt musí v doménovej konfigurácii uviesť pre každý typ
entity aspoň:

- zdroj autoritatívneho URI alebo, ak neexistuje, vzor komunitného URI;
- zdroj identifikátora a názov zdrojového poľa;
- prípadnú transformáciu identifikátora;
- spôsob zosúladenia, ak identifikátor pochádza z iného zdroja;
- pravidlá riešenia chýbajúcich, duplicitných a nejednoznačných zhôd.

Konkrétne URI vzory a pravidlá identít nesmú byť ukryté iba v zdrojovom
kóde transformátora.

Príklad konfigurácie operačných bodov ERA:

```yaml
identities:
  operational_point:
    uri_pattern: "https://slovpedia.eu/id/operational-point/{id}"
    identifier:
      source: zsr_infomapa_operational_points
      field: Id
    reconciliation:
      source: railway_stations_and_stops
      source_field: Názov
      reference_field: Nazov
      method: normalized_exact_name
```

V tomto príklade zdrojový zoznam staníc a zastávok neposkytuje identifikátor
operačného bodu. Stĺpec `Cestovné poriadky` označuje trať alebo cestovný
poriadok a nesmie sa použiť ako identifikátor zastávky. Identifikátor sa
preberá z poľa `Id` zodpovedajúceho dopravného bodu InfoMapy po jednoznačnej
normalizovanej presnej zhode názvu.

## Stabilita identít

- Autoritatívne URI má prednosť pred komunitným URI `slovpedia.eu`.
- Prednostne sa používa stabilný identifikátor poskytnutý zdrojom.
- URI sa nesmie vytvárať iba z názvu, ak existuje vhodný zdrojový
  identifikátor.
- Zmena názvu, jazyka alebo pravopisu entity nesmie zmeniť jej URI.
- Rovnaká entita musí mať rovnaké URI vo všetkých datasetoch a vydaniach.
- Zdrojový identifikátor sa eviduje aj samostatne od verejného URI.
- Identifikátor jednej autority sa nesmie vydávať za identifikátor inej
  autority. InfoMapa `Id` napríklad nie je ERA `uopid`.
- Ak zdroj neposkytuje vhodný identifikátor, náhradný identifikátor musí mať
  zdokumentovaný a deterministický spôsob tvorby.

## Zosúladenie viacerých zdrojov

Ak sa identita alebo vlastnosti entity skladajú z viacerých zdrojov,
konfigurácia a provenance musia uvádzať:

- použité zdroje a polia;
- metódu zosúladenia;
- pravidlá normalizácie;
- spôsob riešenia konfliktov;
- výsledok nejednoznačných a nenájdených zhôd.

Nejednoznačná zhoda sa nesmie automaticky vybrať. Nenájdená zhoda musí byť
uvedená v quality reporte. `owl:sameAs` sa používa iba pri preukázanej
totožnosti; neisté zosúladenie sa vyjadrí slabším vzťahom a doloží sa jeho
metóda.

## Reálne a syntetické datasety

Syntetickosť sa nezapisuje do názvu ani do URI datasetu alebo jeho entít.
Uvádza sa v katalógových metadátach datasetu pomocou typu z európskeho
číselníka:

```turtle
<https://slovpedia.eu/set/era-sk-etcs>
    a dcat:Dataset ;
    dct:type
        <http://publications.europa.eu/resource/authority/dataset-type/SYNTHETIC_DATA> .
```

RDF Galaxy môže podľa tohto tvrdenia syntetický dataset označiť, filtrovať
a primerane prezentovať v používateľskom rozhraní. Reálne odvodené a
syntetické tvrdenia musia zostať v samostatných datasetoch a pomenovaných
grafoch.

## Kontrola

Každá doménová transformácia musí mať kontraktové testy, ktoré overia:

- použitie URI vzoru z konfigurácie;
- deterministickú tvorbu URI;
- jedinečnosť URI v rámci typu entity;
- stabilitu URI pri opakovanom zostavení;
- odmietnutie duplicitných alebo nejednoznačných identít;
- evidovanie neúspešných zosúladení v quality reporte.
