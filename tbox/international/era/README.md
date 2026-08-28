# ERA Ontology 3.3.4

Tento adresár je generovaný pomocou
`scripts/era-vocabulary/download.sh`. Súbory neupravujte ručne.

- `ontology.ttl` – spoločná ontológia exportovaná zo živého ERA grafu;
- `shacl/ERA-RINF-shapes.ttl` – produkčný RINF profil zo živého ERA grafu;
- `shacl/ERA-ERATV-shapes.ttl` – profil typov vozidiel z tagu `v3.3.4`;
- `shacl/ERA-EVR-shapes.ttl` – profil registra vozidiel z tagu `v3.3.4`;
- `shacl/ERA-ERADIS-shapes.ttl` – profil oprávnení a certifikácií z tagu
  `v3.3.4`;
- `manifest.json` a `checksums.sha256` – provenance a kontrolné súčty.

Rozdelenie profilov zodpovedá upstream projektu `era-vocabulary`. Verejný
GraphDB publikuje ontológiu `v3.3.4`, ale v spoločnom SHACL pomenovanom grafe
sprístupňuje iba produkčný RINF profil.
