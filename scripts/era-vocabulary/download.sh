#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd -- "${script_dir}/../.." && pwd)"
output_dir="${1:-${repo_root}/tbox/international/era}"

version="3.3.4"
version_tag="v${version}"
repository_url="https://graph.data.era.europa.eu/repositories/ERA-Onto"
statements_url="${repository_url}/statements"
ontology_graph="http://data.europa.eu/949/graph/ontology"
rinf_shacl_graph="http://data.europa.eu/949/graph/shacl"
gitlab_raw_base="https://gitlab.com/era-europa-eu/public/interoperable-data-programme/era-ontology/era-ontology/-/raw/${version_tag}"

for command_name in arq curl jq riot sha256sum; do
  if ! command -v "${command_name}" >/dev/null 2>&1; then
    echo "Missing required command: ${command_name}" >&2
    exit 1
  fi
done

temporary_dir="$(mktemp -d)"
trap 'rm -rf -- "${temporary_dir}"' EXIT

ontology_file="${temporary_dir}/ontology.ttl"
rinf_file="${temporary_dir}/ERA-RINF-shapes.ttl"
eratv_file="${temporary_dir}/ERA-ERATV-shapes.ttl"
evr_file="${temporary_dir}/ERA-EVR-shapes.ttl"
eradis_file="${temporary_dir}/ERA-ERADIS-shapes.ttl"

curl --fail --silent --show-error --max-time 180 --get \
  --header 'Accept: text/turtle' \
  --data-urlencode "context=<${ontology_graph}>" \
  --output "${ontology_file}" \
  "${statements_url}"

curl --fail --silent --show-error --max-time 180 --get \
  --header 'Accept: text/turtle' \
  --data-urlencode "context=<${rinf_shacl_graph}>" \
  --output "${rinf_file}" \
  "${statements_url}"

for domain in ERATV EVR ERADIS; do
  target_variable="${domain,,}_file"
  target_file="${!target_variable}"
  curl --fail --silent --show-error --max-time 180 --location \
    --output "${target_file}" \
    "${gitlab_raw_base}/era-shacl/ERA-${domain}-shapes.ttl"
done

for rdf_file in \
  "${ontology_file}" \
  "${rinf_file}" \
  "${eratv_file}" \
  "${evr_file}" \
  "${eradis_file}"; do
  riot --validate "${rdf_file}"
done

detected_version="$(
  arq \
    --data="${ontology_file}" \
    --query="${script_dir}/sparql/version.rq" \
    --results=TSV |
    awk 'NR == 2 { gsub(/"/, "", $1); print $1 }'
)"
if [[ "${detected_version}" != "${version_tag}" ]]; then
  echo "Expected ERA Ontology ${version_tag}, got ${detected_version:-no version}." >&2
  exit 1
fi

triple_count() {
  riot --count "$1" 2>&1 | awk '/Triples =/ { gsub(/,/, "", $NF); print $NF }'
}

sha256() {
  sha256sum "$1" | awk '{ print $1 }'
}

mkdir -p -- "${output_dir}/shacl"
install -m 0644 "${ontology_file}" "${output_dir}/ontology.ttl"
install -m 0644 "${rinf_file}" "${output_dir}/shacl/ERA-RINF-shapes.ttl"
install -m 0644 "${eratv_file}" "${output_dir}/shacl/ERA-ERATV-shapes.ttl"
install -m 0644 "${evr_file}" "${output_dir}/shacl/ERA-EVR-shapes.ttl"
install -m 0644 "${eradis_file}" "${output_dir}/shacl/ERA-ERADIS-shapes.ttl"

jq -n \
  --arg version "${version_tag}" \
  --arg repository "${repository_url}" \
  --arg ontologyGraph "${ontology_graph}" \
  --arg rinfShaclGraph "${rinf_shacl_graph}" \
  --arg release "https://gitlab.com/era-europa-eu/public/interoperable-data-programme/era-ontology/era-ontology/-/releases/${version_tag}" \
  --arg ontologySha256 "$(sha256 "${ontology_file}")" \
  --arg rinfSha256 "$(sha256 "${rinf_file}")" \
  --arg eratvSha256 "$(sha256 "${eratv_file}")" \
  --arg evrSha256 "$(sha256 "${evr_file}")" \
  --arg eradisSha256 "$(sha256 "${eradis_file}")" \
  --argjson ontologyTriples "$(triple_count "${ontology_file}")" \
  --argjson rinfTriples "$(triple_count "${rinf_file}")" \
  --argjson eratvTriples "$(triple_count "${eratv_file}")" \
  --argjson evrTriples "$(triple_count "${evr_file}")" \
  --argjson eradisTriples "$(triple_count "${eradis_file}")" \
  '{
    schemaVersion: 1,
    version: $version,
    artifacts: [
      {
        path: "ontology.ttl",
        domain: "shared",
        source: {repository: $repository, namedGraph: $ontologyGraph},
        triples: $ontologyTriples,
        sha256: $ontologySha256
      },
      {
        path: "shacl/ERA-RINF-shapes.ttl",
        domain: "RINF",
        source: {repository: $repository, namedGraph: $rinfShaclGraph},
        triples: $rinfTriples,
        sha256: $rinfSha256
      },
      {
        path: "shacl/ERA-ERATV-shapes.ttl",
        domain: "ERATV",
        source: {release: $release},
        triples: $eratvTriples,
        sha256: $eratvSha256
      },
      {
        path: "shacl/ERA-EVR-shapes.ttl",
        domain: "EVR",
        source: {release: $release},
        triples: $evrTriples,
        sha256: $evrSha256
      },
      {
        path: "shacl/ERA-ERADIS-shapes.ttl",
        domain: "ERADIS",
        source: {release: $release},
        triples: $eradisTriples,
        sha256: $eradisSha256
      }
    ]
  }' > "${output_dir}/manifest.json"

(
  cd -- "${output_dir}"
  sha256sum \
    ontology.ttl \
    shacl/ERA-RINF-shapes.ttl \
    shacl/ERA-ERATV-shapes.ttl \
    shacl/ERA-EVR-shapes.ttl \
    shacl/ERA-ERADIS-shapes.ttl \
    manifest.json > checksums.sha256
)

echo "ERA Ontology ${version_tag} exported to ${output_dir}"
