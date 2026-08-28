"""
CLI for generating base RINF CSV datasets from raw source files.

Usage from scripts/zsr-opendata/2-0:
    python build_rinf_csv.py rinf_sections_of_line
"""

from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path

try:
    import yaml
except ImportError as exc:
    raise SystemExit("Missing dependency: pip install pyyaml") from exc


def load_config(config_path: Path) -> dict:
    with config_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate base RINF CSV datasets.")
    parser.add_argument("dataset", help="Dataset key from config.yml, e.g. rinf_sections_of_line")
    parser.add_argument("--config", default="config.yml", help="Path to config.yml")
    args = parser.parse_args()

    config_path = Path(args.config).resolve()
    config_dir = config_path.parent
    config = load_config(config_path)

    module_name = f"transformers.{args.dataset}"
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        raise SystemExit(f"Transformer not found: {module_name}") from exc

    output_path = module.transform(config=config, config_dir=config_dir, dataset_name=args.dataset)
    print(f"Generated: {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
