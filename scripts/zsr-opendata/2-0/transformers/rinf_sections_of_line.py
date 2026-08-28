"""
Transformer for the raw Slovak railway-lines CSV into the project base dataset:

    data/rinf/rinf_sections_of_line.csv

Expected source file example:
    Zoznam železničných tratí v SR za rok 2021

The transformer is intentionally conservative: it does not invent official RINF
identifiers. It creates deterministic local IDs from the line/section code and
keeps original OP names so that they can later be reconciled to real UOPIDs.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any

# The source CSV is mostly UTF-8, but some Slovak letters appear as Windows-1250
# C1 control bytes. These replacements repair the known cases in the provided file.
BROKEN_CP1250_CHARS = {
    "\x8a": "Š",
    "\x9a": "š",
    "\x8e": "Ž",
    "\x9e": "ž",
    "\x9d": "ť",
}


def normalize_text(value: str | None) -> str:
    if value is None:
        return ""
    value = value.strip().replace("\ufeff", "")
    for bad, good in BROKEN_CP1250_CHARS.items():
        value = value.replace(bad, good)
    return " ".join(value.split())


def slug_code(value: str) -> str:
    """Convert railway line code such as '101 A' to a stable ID part '101-A'."""
    value = normalize_text(value).upper()
    value = value.replace("/", "-")
    value = re.sub(r"\s+", "-", value)
    value = re.sub(r"[^A-Z0-9.-]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value


def parse_decimal(value: str | None) -> str:
    value = normalize_text(value).replace(",", ".")
    if not value:
        return ""
    # Validation only. Keep normalized string to avoid formatting surprises.
    float(value)
    return value


def get_column(row: dict[str, str], expected: str) -> str:
    """Find a column even if its header contains newlines or extra spaces."""
    expected_norm = normalize_text(expected).lower()
    for key, value in row.items():
        key_norm = normalize_text(key).lower()
        if key_norm == expected_norm or expected_norm in key_norm:
            return value
    raise KeyError(f"Column not found: {expected}. Available columns: {list(row.keys())}")


def resolve_path(config_dir: Path, path_value: str, paths: dict[str, str]) -> Path:
    resolved = path_value.format(**paths)
    path = Path(resolved)
    if not path.is_absolute():
        path = config_dir / path
    return path.resolve()


def transform(config: dict[str, Any], config_dir: Path, dataset_name: str = "rinf_sections_of_line") -> Path:
    datasets = config["datasets"]
    dataset = datasets[dataset_name]
    paths = config.get("paths", {})

    source_value = dataset.get("source_csv") or dataset.get("raw_csv")
    if not source_value:
        raise ValueError(
            f"Dataset '{dataset_name}' needs 'source_csv' or 'raw_csv' in config.yml."
        )

    source_csv = resolve_path(config_dir, source_value, paths)
    output_csv = resolve_path(config_dir, dataset["csv"], paths)
    output_csv.parent.mkdir(parents=True, exist_ok=True)

    rows_out: list[dict[str, str]] = []

    with source_csv.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            source_row_id = normalize_text(get_column(row, "_id"))
            section_code = normalize_text(get_column(row, "Číslo trate"))
            line_category_code = normalize_text(get_column(row, "Kategória trate"))
            op_start_name = normalize_text(get_column(row, "Začiatok trate"))
            op_end_name = normalize_text(get_column(row, "Koniec trate"))
            length_km = parse_decimal(get_column(row, "Trate v km"))

            if not section_code:
                continue

            section_id = f"SOL-{slug_code(section_code)}"

            rows_out.append(
                {
                    "section_of_line_id": section_id,
                    "section_code": section_code,
                    "op_start_name": op_start_name,
                    "op_end_name": op_end_name,
                    "length_km": length_km,
                    "line_category_code": line_category_code,
                    "status": "operational",
                    "source_dataset": source_csv.name,
                    "source_row_id": source_row_id,
                }
            )

    fieldnames = [
        "section_of_line_id",
        "section_code",
        "op_start_name",
        "op_end_name",
        "length_km",
        "line_category_code",
        "status",
        "source_dataset",
        "source_row_id",
    ]

    with output_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows_out)

    return output_csv
