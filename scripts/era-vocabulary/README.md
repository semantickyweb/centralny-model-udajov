# ERA Ontology a SHACL

Skript `download.sh` vytvorí lokálny snapshot poslednej podporovanej vydanej
verzie ERA Ontology. Verzia je zámerne pripnutá na `v3.3.4`.

```bash
scripts/era-vocabulary/download.sh
```

Spoločná ontológia a produkčný RINF SHACL profil sa exportujú priamo
z pomenovaných grafov verejného repozitára `ERA-Onto`. Doménové profily
ERATV, EVR a ERADIS sa sťahujú z rovnakého vydaného tagu v oficiálnom GitLab
repozitári, pretože živý `graph/shacl` obsahuje iba profil RINF.

Výstup je v `tbox/international/era/`. `manifest.json` pri každom artefakte
uvádza doménu, zdroj, počet trojíc a SHA-256.
