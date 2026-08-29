#!/usr/bin/env python3
"""Build ŽSR open-data class datasets from an ERA/RINF N-Quads snapshot."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit

from rdflib import Dataset, Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, RDF, XSD


PROV = "http://www.w3.org/ns/prov#"
PROV_WAS_DERIVED_FROM = URIRef(f"{PROV}wasDerivedFrom")
SUPPORTED_ID_STRATEGY = "source-uri-last-segment"
DCAT = Namespace("http://www.w3.org/ns/dcat#")
FILE_TYPE = Namespace("http://publications.europa.eu/resource/authority/file-type/")
IANA_MEDIA_TYPE = Namespace("http://www.iana.org/assignments/media-types/")


@dataclass(frozen=True)
class DatasetDefinition:
    dataset_id: str
    class_slug: str
    class_iri: URIRef
    source_id: str
    id_strategy: str
    incoming_property_iri: URIRef | None


def repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_config(path: Path) -> dict:
    config = json.loads(path.read_text(encoding="utf-8"))
    if config.get("schemaVersion") != 1:
        raise ValueError("Only schemaVersion 1 is supported")
    expected_template = "https://data.gov.sk/{type}/era/{class}/{id}"
    if config.get("uriTemplate") != expected_template:
        raise ValueError(f"uriTemplate must be {expected_template!r}")
    return config


def definitions(config: dict) -> list[DatasetDefinition]:
    result = []
    for item in config["datasets"]:
        if item.get("status") != "ready":
            continue
        strategy = item.get("idStrategy")
        if strategy != SUPPORTED_ID_STRATEGY:
            raise ValueError(
                f'{item["id"]}: unsupported idStrategy {strategy!r}; '
                f"expected {SUPPORTED_ID_STRATEGY!r}"
            )
        incoming = item.get("incomingPropertyIri")
        result.append(
            DatasetDefinition(
                dataset_id=item["id"],
                class_slug=item["class"],
                class_iri=URIRef(item["classIri"]),
                source_id=item["source"],
                id_strategy=strategy,
                incoming_property_iri=URIRef(incoming) if incoming else None,
            )
        )
    if not result:
        raise ValueError("No datasets have status 'ready'")
    return result


def iri_last_segment(iri: URIRef) -> str:
    parsed = urlsplit(str(iri))
    segment = parsed.path.rstrip("/").rsplit("/", 1)[-1]
    if not segment:
        raise ValueError(f"ERA URI has no final path segment: {iri}")
    decoded = segment
    while True:
        next_value = unquote(decoded)
        if next_value == decoded:
            break
        decoded = next_value
    return quote(decoded, safe="-._~")


def local_entity_iri(class_slug: str, source_iri: URIRef) -> URIRef:
    return URIRef(
        f"https://data.gov.sk/id/era/{class_slug}/{iri_last_segment(source_iri)}"
    )


def read_source(path: Path) -> Dataset:
    dataset = Dataset()
    with gzip.open(path, "rb") if path.suffix == ".gz" else path.open("rb") as source:
        dataset.parse(source=source, format="nquads")
    return dataset


def build_iri_map(
    source_graph: Graph, dataset_definitions: list[DatasetDefinition]
) -> tuple[dict[URIRef, URIRef], dict[str, list[URIRef]]]:
    iri_map: dict[URIRef, URIRef] = {}
    entities_by_dataset: dict[str, list[URIRef]] = {}
    local_owners: dict[URIRef, URIRef] = {}

    for definition in dataset_definitions:
        entities = sorted(
            {
                subject
                for subject in source_graph.subjects(RDF.type, definition.class_iri)
                if isinstance(subject, URIRef)
            },
            key=str,
        )
        entities_by_dataset[definition.dataset_id] = entities
        for source_iri in entities:
            local_iri = local_entity_iri(definition.class_slug, source_iri)
            previous_source = local_owners.get(local_iri)
            if previous_source is not None and previous_source != source_iri:
                raise ValueError(
                    f"URI collision: {previous_source} and {source_iri} map to {local_iri}"
                )
            previous_local = iri_map.get(source_iri)
            if previous_local is not None and previous_local != local_iri:
                raise ValueError(
                    f"ERA entity {source_iri} belongs to multiple configured classes: "
                    f"{previous_local} and {local_iri}"
                )
            local_owners[local_iri] = source_iri
            iri_map[source_iri] = local_iri

    return iri_map, entities_by_dataset


def rewrite_object(value, iri_map: dict[URIRef, URIRef]):
    if isinstance(value, URIRef):
        return iri_map.get(value, value)
    return value


def build_dataset_graph(
    source_graph: Graph,
    definition: DatasetDefinition,
    entities: list[URIRef],
    iri_map: dict[URIRef, URIRef],
    source_graph_iri: URIRef,
) -> Graph:
    output = Graph()
    output.bind("dct", DCTERMS)
    output.bind("era", URIRef("http://data.europa.eu/949/"))
    output.bind("prov", URIRef(PROV))

    for source_iri in entities:
        local_iri = iri_map[source_iri]
        for _, predicate, value in source_graph.triples((source_iri, None, None)):
            output.add((local_iri, predicate, rewrite_object(value, iri_map)))
        output.add((local_iri, PROV_WAS_DERIVED_FROM, source_iri))
        output.add((local_iri, PROV_WAS_DERIVED_FROM, source_graph_iri))

        if definition.incoming_property_iri is not None:
            for referring_iri in source_graph.subjects(
                definition.incoming_property_iri, source_iri
            ):
                if not isinstance(referring_iri, URIRef) or referring_iri not in iri_map:
                    continue
                local_referrer = iri_map[referring_iri]
                output.add(
                    (local_referrer, definition.incoming_property_iri, local_iri)
                )
                output.add(
                    (local_referrer, PROV_WAS_DERIVED_FROM, referring_iri)
                )
                output.add(
                    (local_referrer, PROV_WAS_DERIVED_FROM, source_graph_iri)
                )

    return output


def build_catalog_graph(
    config: dict,
    source_config: dict,
    dataset_definitions: list[DatasetDefinition],
) -> Graph:
    catalog = Graph()
    catalog.bind("dcat", DCAT)
    catalog.bind("dct", DCTERMS)
    catalog.bind("prov", URIRef(PROV))
    catalog.bind("xsd", XSD)

    catalog_iri = URIRef(config["catalogIri"])
    source_graph_iri = URIRef(source_config["graphIri"])
    snapshot_date = Literal(source_config["snapshotDate"], datatype=XSD.date)
    catalog.add((catalog_iri, RDF.type, DCAT.Catalog))
    catalog.add((catalog_iri, PROV_WAS_DERIVED_FROM, source_graph_iri))

    for definition in dataset_definitions:
        dataset_iri = URIRef(
            f"https://data.gov.sk/set/era/dataset/{definition.dataset_id}"
        )
        distribution_iri = URIRef(
            "https://data.gov.sk/set/era/distribution/"
            f"{definition.dataset_id}-{source_config['snapshotDate']}-turtle-gzip"
        )
        catalog.add((catalog_iri, DCAT.dataset, dataset_iri))
        catalog.add((dataset_iri, RDF.type, DCAT.Dataset))
        catalog.add((dataset_iri, DCTERMS.identifier, Literal(definition.dataset_id)))
        catalog.add((dataset_iri, DCTERMS.modified, snapshot_date))
        catalog.add((dataset_iri, DCTERMS.conformsTo, definition.class_iri))
        catalog.add((dataset_iri, DCTERMS.source, source_graph_iri))
        catalog.add((dataset_iri, PROV_WAS_DERIVED_FROM, source_graph_iri))
        catalog.add((dataset_iri, DCAT.distribution, distribution_iri))
        catalog.add((distribution_iri, RDF.type, DCAT.Distribution))
        catalog.add((distribution_iri, DCTERMS.format, FILE_TYPE.RDF_TURTLE))
        catalog.add((distribution_iri, DCAT.mediaType, IANA_MEDIA_TYPE["text/turtle"]))
        catalog.add(
            (distribution_iri, DCAT.compressFormat, IANA_MEDIA_TYPE["application/gzip"])
        )

    return catalog


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(repository_root()))
    except ValueError:
        return str(path)


def serialize_turtle_gzip(graph: Graph, target: Path) -> dict:
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="zsr-opendata-") as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        ntriples_path = temp_dir / "dataset.nt"
        turtle_path = temp_dir / "dataset.ttl"

        graph.serialize(destination=ntriples_path, format="nt", encoding="utf-8")
        statements = ntriples_path.read_bytes().splitlines(keepends=True)
        statements.sort()
        ntriples_path.write_bytes(b"".join(statements))
        subprocess.run(["riot", "--validate", str(ntriples_path)], check=True)
        with turtle_path.open("wb") as turtle:
            subprocess.run(
                ["riot", "--formatted=TURTLE", str(ntriples_path)],
                stdout=turtle,
                check=True,
            )
        subprocess.run(["riot", "--validate", str(turtle_path)], check=True)

        with turtle_path.open("rb") as source, target.open("wb") as raw_target:
            with gzip.GzipFile(
                fileobj=raw_target, mode="wb", filename="", mtime=0
            ) as compressed_target:
                shutil.copyfileobj(source, compressed_target)

        return {
            "statements": len(statements),
            "uncompressedBytes": turtle_path.stat().st_size,
            "compressedBytes": target.stat().st_size,
            "sha256": sha256(target),
        }


def serialize_turtle(graph: Graph, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="zsr-opendata-catalog-") as temp_dir_name:
        ntriples_path = Path(temp_dir_name) / "catalog.nt"
        graph.serialize(destination=ntriples_path, format="nt", encoding="utf-8")
        statements = ntriples_path.read_bytes().splitlines(keepends=True)
        statements.sort()
        ntriples_path.write_bytes(b"".join(statements))
        with target.open("wb") as turtle:
            subprocess.run(
                ["riot", "--formatted=TURTLE", str(ntriples_path)],
                stdout=turtle,
                check=True,
            )
    subprocess.run(["riot", "--validate", str(target)], check=True)


def resolve_source(config: dict, source_override: Path | None) -> tuple[dict, Path]:
    source_ids = {
        item["source"]
        for item in config["datasets"]
        if item.get("status") == "ready"
    }
    if len(source_ids) != 1:
        raise ValueError("One build can currently use exactly one source")
    source_id = source_ids.pop()
    source_config = next(item for item in config["sources"] if item["id"] == source_id)
    source_path = source_override or repository_root() / source_config["artifact"]
    return source_config, source_path.resolve()


def build(config_path: Path, source_override: Path | None, output: Path | None) -> Path:
    config = load_config(config_path)
    dataset_definitions = definitions(config)
    source_config, source_path = resolve_source(config, source_override)
    if not source_path.is_file():
        raise FileNotFoundError(f"Source snapshot does not exist: {source_path}")

    output_dir = output or (
        repository_root()
        / "abox/semantickyweb/era-sk/zsr-opendata"
        / source_config["snapshotDate"]
    )
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    source_dataset = read_source(source_path)
    source_graph_iri = URIRef(source_config["graphIri"])
    source_graph = source_dataset.graph(source_graph_iri)
    iri_map, entities_by_dataset = build_iri_map(source_graph, dataset_definitions)

    catalog_graph = build_catalog_graph(config, source_config, dataset_definitions)
    serialize_turtle(catalog_graph, output_dir / "catalog.ttl")

    artifacts = []
    for definition in dataset_definitions:
        entities = entities_by_dataset[definition.dataset_id]
        output_graph = build_dataset_graph(
            source_graph,
            definition,
            entities,
            iri_map,
            source_graph_iri,
        )
        relative_path = Path("data") / f"{definition.dataset_id}.ttl.gz"
        statistics = serialize_turtle_gzip(output_graph, output_dir / relative_path)
        artifacts.append(
            {
                "datasetId": definition.dataset_id,
                "datasetIri": f'https://data.gov.sk/set/era/dataset/{definition.dataset_id}',
                "class": definition.class_slug,
                "classIri": str(definition.class_iri),
                "entities": len(entities),
                "path": relative_path.as_posix(),
                "mediaType": "text/turtle",
                "compression": "gzip",
                **statistics,
            }
        )
        print(
            f"{definition.dataset_id}: {len(entities)} entities, "
            f'{statistics["statements"]} statements'
        )

    manifest = {
        "schemaVersion": 1,
        "uriTemplate": config["uriTemplate"],
        "sourceGraph": str(source_graph_iri),
        "sourceArtifact": display_path(source_path),
        "snapshotDate": source_config["snapshotDate"],
        "idStrategy": SUPPORTED_ID_STRATEGY,
        "entityIrisRewritten": True,
        "provenance": {
            "property": str(PROV_WAS_DERIVED_FROM),
            "targets": ["source entity", "source graph"],
        },
        "catalog": "catalog.ttl",
        "artifacts": artifacts,
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return output_dir


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate ŽSR open data with data.gov.sk entity URIs"
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(__file__).with_name("datasets.json"),
    )
    parser.add_argument("--source", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    output_dir = build(args.config.resolve(), args.source, args.output)
    print(f"Generated: {output_dir}")


if __name__ == "__main__":
    main()
