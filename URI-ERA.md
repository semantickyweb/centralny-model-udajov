# Register URI pre ERA

> **Dočasný stav:** URI pod `https://slovpedia.eu/` sú komunitné pracovné
> URI. Cieľom je používať autoritatívny priestor pod `zsr.sk` alebo
> `data.gov.sk`. Výber priestoru, presný tvar URI a spôsob migrácie treba
> rozhodnúť a schváliť. Dovtedy sa používajú URI `slovpedia.eu`.

Tento dokument je konkrétny register URI pre železničnú doménu ERA v
Centrálnom modeli údajov. Všeobecné pravidlá určuje [Politika URI Centrálneho
modelu údajov](URIs.md).

Pre každú entitu sa najprv hľadá autoritatívne URI. Uvedený vzor
`slovpedia.eu` sa použije iba vtedy, keď autoritatívne URI neexistuje.

## Použité ERA priestory

```text
era:          http://data.europa.eu/949/
era-op-types: http://data.europa.eu/949/concepts/op-types/
```

## Operačné body, stanice a zastávky

Stanica ani zastávka nedostáva iný URI priestor. Identita fyzického
operačného bodu zostáva rovnaká a jeho funkčný typ sa vyjadrí vlastnosťou
`era:opType` s hodnotou z ERA schémy `OperationalPointTypes`.

| Entita | URI pattern | ERA trieda a presné rozlíšenie | Zdroj identifikátora | Stav mapovania |
| --- | --- | --- | --- | --- |
| Železničná stanica – veľký alebo hlavný uzol | `https://slovpedia.eu/id/operational-point/{infomapa_id}` | `a era:OperationalPoint`; `era:opType era-op-types:10` (`station`) | InfoMapa ŽSR, pole `Id` | Slovenská hodnota `železničná stanica` sama nestačí na priradenie konceptu `10` |
| Malá železničná stanica | `https://slovpedia.eu/id/operational-point/{infomapa_id}` | `a era:OperationalPoint`; `era:opType era-op-types:20` (`small station`) | InfoMapa ŽSR, pole `Id` | Slovenská hodnota `železničná stanica` sama nestačí na priradenie konceptu `20` |
| Železničná zastávka | `https://slovpedia.eu/id/operational-point/{infomapa_id}` | `a era:OperationalPoint`; `era:opType era-op-types:70` (`passenger stop`) | InfoMapa ŽSR, pole `Id` | Používa sa pre zdrojovú hodnotu `zastávka` |

Koncepty v plnom tvare:

```text
http://data.europa.eu/949/concepts/op-types/10  station
http://data.europa.eu/949/concepts/op-types/20  small station
http://data.europa.eu/949/concepts/op-types/70  passenger stop
```

ERA pravidlo vyžaduje pre operačný bod jeden konkrétny funkčný typ.
Všeobecný koncept pre operačný bod neexistuje, preto register neuvádza
generický riadok bez konkrétnej hodnoty `era:opType`.
Preto sa 380 slovenským záznamom označeným iba ako `železničná stanica`
zatiaľ nepriraďuje koncept `10` ani `20`; treba doplniť zdroj, ktorý ich
spoľahlivo rozlíši. Ich URI operačného bodu je napriek tomu stabilné.

## Ostatné infraštruktúrne entity

| Entita | URI pattern | ERA trieda alebo vzťah | Zdroj identifikátora | Stav mapovania |
| --- | --- | --- | --- | --- |
| Grafický úsek siete | `https://slovpedia.eu/id/network-section/{infomapa_id}` | odvodená entita InfoMapy; zatiaľ bez tvrdenia `a era:SectionOfLine` | InfoMapa ŽSR, stabilné ID grafického úseku | Treba overiť zdrojové ID a sémantiku |
| Úsek trate | `https://slovpedia.eu/id/section-of-line/{id}` | `a era:SectionOfLine` | overený identifikátor úseku medzi dvoma operačnými bodmi | Identita sa nesmie odvodiť iba z názvov koncov |
| Jazdná koľaj | `https://slovpedia.eu/id/running-track/{section_of_line_id}/{track_id}` | `a era:RunningTrack`; súčasť úseku cez `era:isPartOf` | ID úseku trate a stabilné ID koľaje | Zdroj identifikátorov treba overiť |
| Vlečková alebo odstavná koľaj | `https://slovpedia.eu/id/siding/{operational_point_id}/{siding_id}` | `a era:Siding`; súčasť operačného bodu cez `era:isPartOf` | ID operačného bodu a lokálne stabilné ID koľaje | Zdroj zatiaľ chýba |
| Nástupištná hrana | `https://slovpedia.eu/id/platform-edge/{operational_point_id}/{platform_edge_id}` | `a era:PlatformEdge`; súčasť infraštruktúry cez `era:isPartOf` | ID operačného bodu a lokálne stabilné ID hrany | Zdroj zatiaľ chýba |
| Tunel | `https://slovpedia.eu/id/tunnel/{id}` | `a era:Tunnel` | stabilný identifikátor tunela zo zdroja | Zdrojové ID treba overiť |
| Most | `https://slovpedia.eu/id/bridge/{id}` | `a era:Bridge` | stabilný identifikátor mosta zo zdroja | Zdroj zatiaľ chýba |
| Traťové ETCS | `https://slovpedia.eu/id/etcs-track-deployment/{id}` | `a era:ETCS`; jazdná koľaj odkazuje cez `era:etcs` | stabilné ID nasadenia alebo deterministická kombinácia ID koľaje a verzie nasadenia | Presný identifikátor treba overiť |
| Sieťová referencia operačného bodu | `https://slovpedia.eu/id/net-point-reference/{operational_point_id}/{reference_id}` | `a era:NetPointReference`; operačný bod odkazuje cez `era:netReference` | ID operačného bodu a stabilné ID referencie | Zdroj identifikátora treba overiť |

Každá premenná v URI patterne znamená stabilný identifikátor doložený
konkrétnym zdrojom. Nesmie sa nahradiť názvom, poradovým číslom
transformačného behu ani vymysleným ERA identifikátorom.

## Zdroje ERA modelu

Rozlíšenie operačných bodov je overené proti týmto upstream artefaktom:

- `ontology.ttl` – trieda `era:OperationalPoint` a vlastnosť `era:opType`;
- `era-skos/era-skos-OperationalPointTypes.ttl` – koncepty `10`, `20` a `70`;
- `era-shacl/rinf/_core.ttl` – tvar `OperationalPointShape` a kontrola
  vlastnosti `era:opType`.

Pracovný susedný repozitár ERA sa používa na analýzu aktuálneho vývoja.
Publikovaný CMÚ dataset sa však musí validovať proti presnej pripnutej a
overenej verzii ERA artefaktov v tomto repozitári.

## Aktuálne použitá identita

Dataset staníc a zastávok používa:

```text
https://slovpedia.eu/id/operational-point/{infomapa_id}
```

Napríklad operačný bod s InfoMapa ID `13016100` má URI:

```text
https://slovpedia.eu/id/operational-point/13016100
```

InfoMapa `Id` je zdrojový identifikátor. Nie je to `era:uopid` a nesmie sa zaň
vydávať.

## Staré ukážkové URI

Existujúce ilustračné súbory v `abox/semantickyweb/era/examples/` používajú
URI pod `https://data.gov.sk/id/railway/`. Tieto URI nie sú doložené ako
autoritatívne a nesmú sa preberať do odvodených alebo publikovaných
datasetov. Pri oprave príkladov sa nahradia URI podľa tohto registra alebo
skutočnými autoritatívnymi URI.

Kontrola `abox/` vo všetkých aktuálne dostupných lokálnych a vzdialene
sledovaných vetvách našla rovnaké ukážkové a konfiguračné URI
`data.gov.sk`, ale nenašla pre tieto železničné entity iné doložené
autoritatívne URI. Pred použitím každého komunitného vzoru sa napriek tomu
musí overiť príslušný externý autoritatívny register.

## Pravidlo aktualizácie

Pri pridaní nového typu ERA entity sa najprv aktualizuje tento register a až
potom konfigurácia, transformácia a testy. Zmena URI vzoru musí obsahovať
pravidlo migrácie existujúcich URI a kontrolu odkazov v celom `abox/` aj v
dostupných vetvách CMÚ.
