"""
Transformer: rinf_network_sections
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

def transform(config: dict[str,Any], config_dir: Path, dataset_name="rinf_network_sections")->Path:
    ds=config["datasets"][dataset_name]
    paths=config.get("paths",{})
    source=resolve_path(config_dir, ds["source_file"], paths)
    out=resolve_path(config_dir, ds["csv"], paths)
    out.parent.mkdir(parents=True, exist_ok=True)
    data=json.loads(source.read_text(encoding="utf-8"))
    fields=["network_section_id","from_operational_point_id","to_operational_point_id","length_km","track_count_code","tudu"]
    with out.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
        for r in data:
            w.writerow({
                "network_section_id":r.get("Id"),
                "from_operational_point_id":r.get("FromId"),
                "to_operational_point_id":r.get("ToId"),
                "length_km":r.get("Dlzka"),
                "track_count_code":r.get("Kolajnost"),
                "tudu":r.get("Tudu") or ""
            })
    return out
