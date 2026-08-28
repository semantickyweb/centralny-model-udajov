#!/usr/bin/env python3
"""Generate Slovpedia ERA class views and DCAT-AP-SK metadata."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import urlencode


PREFIXES = """@prefix dcat: <http://www.w3.org/ns/dcat#> .
@prefix dct: <http://purl.org/dc/terms/> .
@prefix foaf: <http://xmlns.com/foaf/0.1/> .
@prefix leg: <https://data.gov.sk/def/ontology/legislation/> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix filetype: <http://publications.europa.eu/resource/authority/file-type/> .
@prefix frequency: <http://publications.europa.eu/resource/authority/frequency/> .
@prefix theme: <http://publications.europa.eu/resource/authority/data-theme/> .
@prefix licence: <http://publications.europa.eu/resource/authority/licence/> .
"""


def literal(value: str, language: str) -> str:
    return f"{json.dumps(value, ensure_ascii=False)}@{language}"


def construct_query(
    graph_iri: str, class_iri: str, incoming_property_iri: str | None = None
) -> str:
    incoming_construct = ""
    incoming_where = ""
    if incoming_property_iri:
        incoming_construct = (
            f"  ?referringEntity <{incoming_property_iri}> ?entity .\n"
        )
        incoming_where = (
            f"    OPTIONAL {{ ?referringEntity <{incoming_property_iri}> ?entity . }}\n"
        )
    return f"""CONSTRUCT {{
  ?entity ?predicate ?object .
{incoming_construct}}}
WHERE {{
  GRAPH <{graph_iri}> {{
    ?entity a <{class_iri}> ;
            ?predicate ?object .
{incoming_where}  }}
}}
"""


def terms_of_use(indent: str = "    ") -> list[str]:
    return [
        f"{indent}leg:termsOfUse [",
        f"{indent}    a leg:TermsOfUse ;",
        f"{indent}    leg:authorsWorkType licence:CC_BY_4_0 ;",
        f"{indent}    leg:originalDatabaseType licence:CC_BY_4_0 ;",
        f"{indent}    leg:databaseProtectedBySpecialRightsType licence:CC_BY_4_0 ;",
        f"{indent}    leg:personalDataContainmentType <https://data.gov.sk/def/personal-data-occurence-type/2> ;",
        f"{indent}    leg:authorName \"European Union Agency for Railways\"@en ;",
        f"{indent}    leg:originalDatabaseAuthorName \"European Union Agency for Railways\"@en",
        f"{indent}] ;",
    ]


def generate(config_path: Path, output_dir: Path) -> None:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    output_dir.mkdir(parents=True, exist_ok=True)
    query_dir = output_dir / "queries"
    query_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "data" / "manifest.json"
    materialized = {}
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        materialized = {item["datasetId"]: item for item in manifest["artifacts"]}

    datasets = config["datasets"]
    dataset_iris = [f'{config["datasetBaseIri"]}/{item["id"]}' for item in datasets]
    generated_at = f'{config["snapshotDate"]}T00:00:00Z'

    lines = [PREFIXES.rstrip(), ""]
    lines.extend(
        [
            f'<{config["catalogIri"]}> a dcat:Catalog ;',
            f'    dct:title {literal("Slovpedia – slovenské železničné dáta ERA", "sk")},',
            f'        {literal("Slovpedia – Slovak ERA railway data", "en")} ;',
            f'    dct:description {literal("Logické datasety slovenského grafu ERA 0056 rozdelené podľa dôležitých tried ERA. Pôvodné ERA URI sa nemenia.", "sk")},',
            f'        {literal("Logical datasets from Slovak ERA graph 0056, separated by important ERA classes. Original ERA IRIs are preserved.", "en")} ;',
            f'    dct:publisher <{config["publisherIri"]}> ;',
            f'    foaf:homepage <{config["catalogHomepage"]}> ;',
            "    dcat:dataset",
            "        " + ",\n        ".join(f"<{iri}>" for iri in dataset_iris) + " .",
            "",
        ]
    )

    for item, dataset_iri in zip(datasets, dataset_iris):
        query = construct_query(
            config["sourceGraphIri"],
            item["classIri"],
            item.get("incomingPropertyIri"),
        )
        query_path = query_dir / f'{item["id"]}.rq'
        query_path.write_text(query, encoding="utf-8")

        query_url = config["sparqlEndpoint"] + "?" + urlencode({"query": query})
        query_doc_url = f'{config["queryDocumentBaseUrl"]}/{item["id"]}.rq'
        snapshot_distribution = f"{dataset_iri}/distribution/snapshot-turtle-gzip"
        live_distribution = f"{dataset_iri}/distribution/sparql-construct-live"
        service_distribution = f"{dataset_iri}/distribution/sparql-service"
        service_iri = f'{config["serviceBaseIri"]}/{item["id"]}'
        dataset_page = f'{config["datasetBaseIri"]}/{item["id"]}'
        snapshot_url = f'{config["dataDownloadBaseUrl"]}/{item["id"]}.ttl.gz'

        lines.extend(
            [
                f"<{dataset_iri}> a dcat:Dataset ;",
                f'    dct:title {literal(item["titleSk"], "sk")}, {literal(item["titleEn"], "en")} ;',
                f'    dct:description {literal(item["descriptionSk"], "sk")},',
                f'        {literal(item["descriptionEn"], "en")} ;',
                f'    dct:publisher <{config["publisherIri"]}> ;',
                f'    dct:creator <{config["eraPublisherIri"]}> ;',
                f'    dct:issued "{generated_at}"^^xsd:dateTime ;',
                f'    dct:modified "{generated_at}"^^xsd:dateTime ;',
                "    dcat:theme theme:TRAN ;",
                "    dct:accrualPeriodicity frequency:IRREG ;",
                "    dct:spatial <http://publications.europa.eu/resource/authority/country/SVK> ;",
                f'    dcat:keyword {literal("ERA", "sk")}, {literal("RINF", "sk")}, {literal("železničná infraštruktúra", "sk")},',
                f'        {literal("ERA", "en")}, {literal("RINF", "en")}, {literal("railway infrastructure", "en")} ;',
                f"    dcat:landingPage <{dataset_page}> ;",
                "    foaf:page <https://rinf.data.era.europa.eu/era-vocabulary/rinf-appGuide/> ;",
                "    dct:conformsTo <http://data.europa.eu/949/> ;",
                f'    dct:relation <{item["classIri"]}> ;',
                f'    dct:source <{config["zenodoRecord"]}> ;',
                f'    prov:wasDerivedFrom <{config["sourceGraphIri"]}> ;',
                f"    dcat:distribution <{snapshot_distribution}>, <{live_distribution}>, <{service_distribution}> .",
                "",
                f"<{snapshot_distribution}> a dcat:Distribution ;",
                f'    dct:title {literal("Uložený výsledok datasetového CONSTRUCT dotazu", "sk")},',
                f'        {literal("Stored result of the dataset CONSTRUCT query", "en")} ;',
            ]
        )
        lines.extend(terms_of_use())
        lines.extend(
            [
                f"    dcat:accessURL <{snapshot_url}> ;",
                f"    dcat:downloadURL <{snapshot_url}> ;",
                "    dct:format filetype:RDF_TURTLE ;",
                "    dcat:mediaType <http://www.iana.org/assignments/media-types/text/turtle> ;",
                "    dcat:compressFormat <http://www.iana.org/assignments/media-types/application/gzip> ;",
            ]
        )
        artifact = materialized.get(item["id"])
        if artifact:
            lines.append(f'    dcat:byteSize "{artifact["compressedBytes"]}"^^xsd:nonNegativeInteger ;')
        lines.extend(
            [
                "    dct:conformsTo <http://data.europa.eu/949/> .",
                "",
                f"<{live_distribution}> a dcat:Distribution ;",
                f'    dct:title {literal("Výsledok datasetového SPARQL CONSTRUCT v N-Triples", "sk")},',
                f'        {literal("Dataset-specific SPARQL CONSTRUCT result in N-Triples", "en")} ;',
            ]
        )
        lines.extend(terms_of_use())
        lines.extend(
            [
                f"    dcat:accessURL <{query_url}> ;",
                f"    dcat:downloadURL <{query_url}> ;",
                "    dct:format filetype:RDF_N_TRIPLES ;",
                "    dcat:mediaType <http://www.iana.org/assignments/media-types/application/n-triples> ;",
                "    dct:conformsTo <http://data.europa.eu/949/> .",
                "",
                f"<{service_distribution}> a dcat:Distribution ;",
                f'    dct:title {literal("SPARQL služba pre tento dataset", "sk")},',
                f'        {literal("SPARQL service for this dataset", "en")} ;',
            ]
        )
        lines.extend(terms_of_use())
        lines.extend(
            [
                f'    dcat:accessURL <{config["sparqlEndpoint"]}> ;',
                f"    dcat:accessService <{service_iri}> .",
                "",
                f"<{service_iri}> a dcat:DataService ;",
                f'    dct:title {literal("SPARQL pohľad – " + item["titleSk"], "sk")},',
                f'        {literal("SPARQL view – " + item["titleEn"], "en")} ;',
                f'    dcat:endpointURL <{config["sparqlEndpoint"]}> ;',
                f"    dcat:endpointDescription <{query_doc_url}> ;",
                f"    dcat:servesDataset <{dataset_iri}> ;",
                f"    foaf:page <{query_doc_url}> ;",
                "    dct:conformsTo <https://www.w3.org/TR/sparql11-protocol/> .",
                "",
            ]
        )

    (output_dir / "catalog.ttl").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(__file__).with_name("dcat-datasets.json"),
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    generate(args.config.resolve(), args.output.resolve())


if __name__ == "__main__":
    main()
