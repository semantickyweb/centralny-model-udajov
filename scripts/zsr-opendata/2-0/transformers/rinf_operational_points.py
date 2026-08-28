"""
Transformer: rinf_operational_points
Reads dataset["source_file"] from config.yml and produces CSV.
"""
from pathlib import Path
import json,csv
from typing import Any

def resolve_path(config_dir: Path, path_value: str, paths: dict[str,str]) -> Path:
    resolved = path_value.format(**paths)
    p = Path(resolved)
    if not p.is_absolute():
        p = config_dir / p
    return p.resolve()

def transform(config: dict[str,Any], config_dir: Path, dataset_name="rinf_operational_points")->Path:
    ds=config["datasets"][dataset_name]
    paths=config.get("paths",{})
    source=resolve_path(config_dir, ds["source_file"], paths)
    out=resolve_path(config_dir, ds["csv"], paths)
    out.parent.mkdir(parents=True, exist_ok=True)
    data=json.loads(source.read_text(encoding="utf-8"))
    fields=["operational_point_id","name","latitude","longitude","valid_from","valid_to"]
    with out.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
        for r in data:
            lat,lon=("","")
            if isinstance(r.get("Suradnice"),list) and len(r["Suradnice"])>=2:
                lat,lon=r["Suradnice"][0],r["Suradnice"][1]
            w.writerow({
                "operational_point_id":r.get("Id"),
                "name":r.get("Nazov",""),
                "latitude":lat,
                "longitude":lon,
                "valid_from":r.get("PlatnostOd",""),
                "valid_to":r.get("PlatnostDo","")
            })
    return out
