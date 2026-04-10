# Interoperabilita a otvorené dáta železničnej infraštruktúry SR 2026 pomocou ERA (RINF)

## Prehľad
Tento dokument definuje návrh na spresnenie a doplnenie datasetov železničnej infraštruktúry SR.
Návrh sa zameriava na CSV a RDF distribúciu. 

Návrh datasetov vychádza zo sémantického modelu ERA:
- `era:SectionOfLine`
- `era:OperationalPoint`
- `era:RunningTrack`
- `era:ETCS`
- `era:PlatformEdge`
- `era:Tunnel`
- ...


---

## 1. `sections_of_line.csv`
**Popis:** Úseky trate medzi prevádzkovými bodmi.

| Stĺpec | Typ | Povinný | Popis |
|--------|-----|---------|-------|
| `section_of_line_id` | string | ÁNO | Jedinečný identifikátor úseku |
| `section_code` | string | ÁNO | Kód trate alebo úseku (napr. `101 A`) |
| `op_start_id` | string | ÁNO | FK → `operational_points.operational_point_id` |
| `op_end_id` | string | ÁNO | FK → `operational_points.operational_point_id` |
| `length_km` | decimal | ÁNO | Dĺžka úseku v km |
| `sol_nature_code` | string | ÁNO | Kód povahy úseku podľa ERA |
| `max_axle_load_t` | decimal | NIE | Maximálny nápravový tlak |
| `max_train_length_m` | decimal | NIE | Maximálna dĺžka vlaku |
| `status` | string | ÁNO | Stav úseku, napr. `operational`, `planned` |

### Mapovanie na ERA
Hlavná trieda:
- `era:SectionOfLine`

Typické mapovanie stĺpcov:
- `section_of_line_id` → URI subjektu `era:SectionOfLine`
- `op_start_id` → `era:opStart`
- `op_end_id` → `era:opEnd`
- `length_km` → `era:lengthOfSectionOfLine`
- `sol_nature_code` → `era:solNature`
- `max_axle_load_t` → vhodná technická vlastnosť ERA pre zaťaženie trate
- `max_train_length_m` → vhodná technická vlastnosť ERA pre dĺžku vlaku

### Krátky príklad
CSV riadok:
```csv
section_of_line_id,section_code,op_start_id,op_end_id,length_km,sol_nature_code,status
SOL-101A-001,101 A,OP-CIERNA,OP-KOSICE,98.730,conventional,operational
```

Príklad RDF:
```turtle
<https://data.gov.sk/id/section-of-line/SOL-101A-001> a era:SectionOfLine ;
    era:opStart <https://data.gov.sk/id/operational-point/OP-CIERNA> ;
    era:opEnd <https://data.gov.sk/id/operational-point/OP-KOSICE> ;
    era:lengthOfSectionOfLine "98.730"^^xsd:decimal .
```

---

## 2. `operational_points.csv`
**Popis:** Stanice, zastávky, výhybne a iné prevádzkové body.

| Stĺpec | Typ | Povinný | Popis |
|--------|-----|---------|-------|
| `operational_point_id` | string | ÁNO | Jedinečný interný identifikátor |
| `uopid` | string | ÁNO | Oficiálny identifikátor OP |
| `name_sk` | string | ÁNO | Názov v slovenčine |
| `op_type_code` | string | ÁNO | Typ OP podľa ERA kódovníka |
| `prm_accessibility` | boolean | NIE | Informácia o prístupnosti pre PRM |
| `status` | string | ÁNO | Stav, napr. `active`, `inactive` |

### Mapovanie na ERA
Hlavná trieda:
- `era:OperationalPoint`

Typické mapovanie stĺpcov:
- `operational_point_id` → URI subjektu `era:OperationalPoint`
- `uopid` → `era:uopid`
- `name_sk` → `era:opName`
- `op_type_code` → `era:opType`
- `prm_accessibility` → lokálna alebo odvodená vlastnosť prístupnosti
- `status` → publikačný alebo prevádzkový stav datasetu

### Krátky príklad
CSV riadok:
```csv
operational_point_id,uopid,name_sk,op_type_code,prm_accessibility,status
OP-KOSICE,SK000123,Košice,station,true,active
```

Príklad RDF:
```turtle
<https://data.gov.sk/id/operational-point/OP-KOSICE> a era:OperationalPoint ;
    era:uopid "SK000123" ;
    era:opName "Košice"@sk ;
    era:opType <http://data.europa.eu/949/concepts/op-types/10> .
```

---

## 3. `operational_point_net_references.csv`
**Popis:** Umiestnenie prevádzkového bodu v sieti.

| Stĺpec | Typ | Povinný | Popis |
|--------|-----|---------|-------|
| `op_net_reference_id` | string | ÁNO | ID sieťovej referencie |
| `operational_point_id` | string | ÁNO | FK → `operational_points.operational_point_id` |
| `kilometer` | decimal | ÁNO | Poloha v km |
| `latitude` | decimal | NIE | Zemepisná šírka |
| `longitude` | decimal | NIE | Zemepisná dĺžka |

### Mapovanie na ERA
Hlavné triedy:
- `era:NetPointReference` alebo iný relevantný typ sieťovej referencie
- väzba z `era:OperationalPoint`

Typické mapovanie:
- `op_net_reference_id` → URI objektu referencie
- `operational_point_id` → subjekt, ktorý dostane `era:netReference`
- `kilometer` → lineárna poloha v rámci siete
- `latitude`, `longitude` → geografická reprezentácia polohy

### Krátky príklad
CSV riadok:
```csv
op_net_reference_id,operational_point_id,kilometer,latitude,longitude
OPNR-KOSICE-1,OP-KOSICE,97.450,48.7164,21.2611
```

Príklad RDF:
```turtle
<https://data.gov.sk/id/operational-point/OP-KOSICE> era:netReference
    <https://data.gov.sk/id/net-point-reference/OPNR-KOSICE-1> .

<https://data.gov.sk/id/net-point-reference/OPNR-KOSICE-1> a era:NetPointReference .
```

---

## 4. `running_tracks.csv`
**Popis:** Jednotlivé bežné koľaje.

| Stĺpec | Typ | Povinný | Popis |
|--------|-----|---------|-------|
| `running_track_id` | string | ÁNO | ID koľaje |
| `section_of_line_id` | string | ÁNO | FK → `sections_of_line.section_of_line_id` |
| `track_id` | string | ÁNO | Identifikátor koľaje podľa ERA/RINF |
| `max_speed_kmh` | decimal | NIE | Maximálna rýchlosť |
| `etcs_id` | string | NIE | FK → ETCS záznam alebo profil ETCS |

### Mapovanie na ERA
Hlavná trieda:
- `era:RunningTrack`

Typické mapovanie:
- `running_track_id` → URI subjektu `era:RunningTrack`
- `track_id` → `era:trackId`
- `section_of_line_id` → väzba na príslušný `era:SectionOfLine`
- `max_speed_kmh` → príslušná technická vlastnosť ERA pre rýchlosť
- `etcs_id` → väzba na ETCS vlastnosti alebo samostatný ETCS objekt

### Krátky príklad
CSV riadok:
```csv
running_track_id,section_of_line_id,track_id,max_speed_kmh,etcs_id
RT-101A-001-1,SOL-101A-001,1,120,ETCS-001
```

Príklad RDF:
```turtle
<https://data.gov.sk/id/running-track/RT-101A-001-1> a era:RunningTrack ;
    era:trackId "1" .

<https://data.gov.sk/id/running-track/RT-101A-001-1>
    <https://data.gov.sk/def/railways/inSectionOfLine>
    <https://data.gov.sk/id/section-of-line/SOL-101A-001> .
```

---

## 5. `platform_edges.csv`
**Popis:** Nástupištné hrany v prevádzkových bodoch.

| Stĺpec | Typ | Povinný | Popis |
|--------|-----|---------|-------|
| `platform_edge_id` | string | ÁNO | ID nástupištnej hrany |
| `operational_point_id` | string | ÁNO | FK → `operational_points.operational_point_id` |
| `length_m` | decimal | NIE | Dĺžka hrany |
| `height_code` | string | NIE | Kód výšky nástupišťa |

### Mapovanie na ERA
Hlavná trieda:
- `era:PlatformEdge`

Typické mapovanie:
- `platform_edge_id` → URI subjektu `era:PlatformEdge`
- `operational_point_id` → väzba na `era:OperationalPoint`
- `length_m` → vlastnosť dĺžky nástupištnej hrany
- `height_code` → vlastnosť výšky podľa ERA kódovníka

### Krátky príklad
CSV riadok:
```csv
platform_edge_id,operational_point_id,length_m,height_code
PE-KOSICE-1,OP-KOSICE,250,550
```

Príklad RDF:
```turtle
<https://data.gov.sk/id/platform-edge/PE-KOSICE-1> a era:PlatformEdge .

<https://data.gov.sk/id/platform-edge/PE-KOSICE-1>
    <https://data.gov.sk/def/railways/inOperationalPoint>
    <https://data.gov.sk/id/operational-point/OP-KOSICE> .
```

---

## 6. `tunnels.csv`
**Popis:** Tunely ako samostatné železničné infraštruktúrne objekty.

| Stĺpec | Typ | Povinný | Popis |
|--------|-----|---------|-------|
| `tunnel_id` | string | ÁNO | ID tunela |
| `section_of_line_id` | string | ÁNO | FK → `sections_of_line.section_of_line_id` |
| `length_m` | decimal | ÁNO | Dĺžka tunela |

### Mapovanie na ERA
Hlavná trieda:
- `era:Tunnel`

Typické mapovanie:
- `tunnel_id` → URI subjektu `era:Tunnel`
- `section_of_line_id` → väzba na príslušný `era:SectionOfLine`
- `length_m` → vlastnosť dĺžky tunela

### Krátky príklad
CSV riadok:
```csv
tunnel_id,section_of_line_id,length_m
TUN-001,SOL-173-004,1180
```

Príklad RDF:
```turtle
<https://data.gov.sk/id/tunnel/TUN-001> a era:Tunnel .
```

---

## 7. `etcs_track_deployments_operational.csv`
**Popis:** ETCS zariadenia v prevádzke na tratiach alebo koľajach.

| Stĺpec | Typ | Povinný | Popis |
|--------|-----|---------|-------|
| `etcs_deployment_id` | string | ÁNO | ID ETCS záznamu |
| `running_track_id` | string | ÁNO | FK → `running_tracks.running_track_id` |
| `level` | string | ÁNO | ETCS level |
| `baseline` | string | ÁNO | ETCS baseline |
| `srs` | string | ÁNO | Verzia SRS |
| `operational_since` | date | NIE | Dátum uvedenia do prevádzky |

### Mapovanie na ERA
Typické mapovanie:
- `running_track_id` → track, na ktorý sa ETCS parametre vzťahujú
- `level` → vlastnosť ETCS level
- `baseline` → vlastnosť ETCS baseline
- `srs` → vlastnosť SRS verzie
- `operational_since` → dátum začiatku platnosti alebo dátum uvedenia do prevádzky

### Krátky príklad
CSV riadok:
```csv
etcs_deployment_id,running_track_id,level,baseline,srs,operational_since
ETCS-001,RT-125A-001-1,L1,Baseline 2,SRS 2.2.2,2006-07-01
```

Príklad RDF:
```turtle
<https://data.gov.sk/id/running-track/RT-125A-001-1>
    <https://data.gov.sk/def/railways/etcsLevel> "L1" ;
    <https://data.gov.sk/def/railways/etcsBaseline> "Baseline 2" ;
    <https://data.gov.sk/def/railways/etcsSrs> "SRS 2.2.2" .
```

---

## 8. `etcs_track_deployments_under_construction.csv`
**Popis:** ETCS vo výstavbe.

| Stĺpec | Typ | Povinný | Popis |
|--------|-----|---------|-------|
| `etcs_deployment_id` | string | ÁNO | ID ETCS záznamu |
| `running_track_id` | string | ÁNO | FK → `running_tracks.running_track_id` |
| `level` | string | ÁNO | ETCS level |
| `baseline` | string | ÁNO | ETCS baseline |
| `planned_start` | date | NIE | Plánovaný alebo reálny začiatok výstavby |

### Mapovanie na ERA
Mapovanie je podobné ako pri ETCS v prevádzke, ale dataset vyjadruje inú životnú fázu:
- existujúci projekt vo výstavbe,
- budúce uvedenie do prevádzky,
- možnosť samostatnej evidencie harmonogramu.

### Krátky príklad
CSV riadok:
```csv
etcs_deployment_id,running_track_id,level,baseline,planned_start
ETCS-CONSTR-001,RT-120-001-1,L2,Baseline 3,2027-03-01
```

---

## 9. `etcs_track_deployments_planned.csv`
**Popis:** ETCS plánované.

| Stĺpec | Typ | Povinný | Popis |
|--------|-----|---------|-------|
| `etcs_deployment_id` | string | ÁNO | ID ETCS záznamu |
| `running_track_id` | string | ÁNO | FK → `running_tracks.running_track_id` |
| `level` | string | ÁNO | ETCS level |
| `baseline` | string | ÁNO | ETCS baseline |
| `planned_date` | date | NIE | Plánovaný dátum realizácie |

### Mapovanie na ERA
Mapovanie je podobné ako pri ostatných ETCS datasetoch, ale ide o plánované nasadenie:
- vhodné pre investičné plány,
- roadmapy modernizácie,
- prehľad budúceho pokrytia ETCS.

### Krátky príklad
CSV riadok:
```csv
etcs_deployment_id,running_track_id,level,baseline,planned_date
ETCS-PLAN-001,RT-110-001-1,L2,Baseline 3,2030-12-31
```