#!/usr/bin/env python3
"""Execute generated ERA CONSTRUCT queries and store Turtle snapshots."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def materialize(config_path: Path, source_path: Path, output_dir: Path) -> None:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    query_dir = output_dir / "queries"
    data_dir = output_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    artifacts = []
    for dataset in config["datasets"]:
        dataset_id = dataset["id"]
        query_path = query_dir / f"{dataset_id}.rq"
        if not query_path.exists():
            raise SystemExit(f"Missing generated query: {query_path}")

        with tempfile.NamedTemporaryFile(
            prefix=f"{dataset_id}-", suffix=".nt", dir=data_dir, delete=False
        ) as temporary:
            ntriples_path = Path(temporary.name)
            subprocess.run(
                [
                    "arq",
                    f"--data={source_path}",
                    f"--query={query_path}",
                    "--results=NT",
                ],
                stdout=temporary,
                check=True,
            )

        try:
            # SPARQL does not define graph serialization order. Sorting complete
            # N-Triples lines gives the Turtle formatter a stable input graph.
            statements = ntriples_path.read_bytes().splitlines(keepends=True)
            statements.sort()
            ntriples_path.write_bytes(b"".join(statements))
            subprocess.run(["riot", "--validate", str(ntriples_path)], check=True)
            statement_count = sum(1 for line in statements if line.strip())
            type_suffix = (
                " <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> "
                f'<{dataset["classIri"]}> .'
            ).encode("utf-8")
            entity_count = sum(1 for line in statements if line.rstrip().endswith(type_suffix))
            if entity_count != dataset["count"]:
                raise RuntimeError(
                    f"{dataset_id}: query returned {entity_count} entities, "
                    f'configuration expects {dataset["count"]}'
                )

            turtle_path = ntriples_path.with_suffix(".ttl")
            with turtle_path.open("wb") as turtle:
                subprocess.run(
                    ["riot", "--formatted=TURTLE", str(ntriples_path)],
                    stdout=turtle,
                    check=True,
                )
            subprocess.run(["riot", "--validate", str(turtle_path)], check=True)

            target_path = data_dir / f"{dataset_id}.ttl.gz"
            with turtle_path.open("rb") as source, target_path.open("wb") as raw_target:
                with gzip.GzipFile(fileobj=raw_target, mode="wb", filename="", mtime=0) as target:
                    shutil.copyfileobj(source, target)

            artifacts.append(
                {
                    "datasetId": dataset_id,
                    "classIri": dataset["classIri"],
                    "path": f"data/{target_path.name}",
                    "mediaType": "text/turtle",
                    "compression": "gzip",
                    "entities": entity_count,
                    "statements": statement_count,
                    "uncompressedBytes": turtle_path.stat().st_size,
                    "compressedBytes": target_path.stat().st_size,
                    "uncompressedSha256": sha256(turtle_path),
                    "sha256": sha256(target_path),
                }
            )
        finally:
            ntriples_path.unlink(missing_ok=True)
            ntriples_path.with_suffix(".ttl").unlink(missing_ok=True)

    manifest = {
        "schemaVersion": 1,
        "snapshotDate": config["snapshotDate"],
        "sourceGraph": config["sourceGraphIri"],
        "sourceArtifact": config["sourceArtifact"],
        "queryDirectory": "queries",
        "contentIrisRewritten": False,
        "artifacts": artifacts,
    }
    (data_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(__file__).with_name("dcat-datasets.json"),
    )
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    materialize(args.config.resolve(), args.source.resolve(), args.output.resolve())


if __name__ == "__main__":
    main()
