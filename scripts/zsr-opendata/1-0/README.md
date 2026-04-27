# Generovanie RDF distribúcií (ERA) pre údaje železničnej infraštruktúry SR

Tento projekt obsahuje Python skripty na transformáciu otvorených dát publikovaných Ministerstvom dopravy Slovenskej republiky do RDF formátu.

Skripty spracúvajú CSV datasety týkajúce sa železničnej infraštruktúry a konvertujú ich do RDF distribúcií (napr. Turtle), ktoré sú vhodné na ďalšie sémantické spracovanie (napr. podľa modelov ERA).

---

## Zdroj dát

Skripty pracujú s otvorenými datasetmi publikovanými Ministerstvom dopravy SR:

- železničné trate
- zoznam staníc a zastávok

Dáta sú očakávané vo formáte **CSV**.

---

## Požiadavky

- Python 3.x

Voliteľné knižnice (podľa implementácie):

```bash
pip install pandas rdflib
```

---

## Použitie

Skripty spusti z **root adresára projektu**.

---

### 1. Železničné trate → RDF

```bash
python3 scripts/zsr-opendata/1-0/rdfize-zeleznicne-trate-SR-2025.py
```

**Popis:**
- načíta CSV s údajmi o železničných tratiach
- transformuje záznamy do RDF

---

### 2. Stanice a zastávky → RDF

```bash
python3 scripts/zsr-opendata/1-0/rdfize-zoznam-stanic-a-zastavok.py
```

**Popis:**
- načíta CSV so stanicami a zastávkami
- konvertuje údaje do RDF

