import csv
import hashlib

INPUT_CSV = "abox/semantickyweb/era/zsr-opendata/1-0/csv/Zoznam železničných tratí v SR za rok 2025.csv"
OUTPUT_SOL_TTL = "abox/semantickyweb/era/zsr-opendata/1-0/rdf/zeleznicne-trate-SR-2025.ttl"
OUTPUT_TTL = "abox/semantickyweb/era/zsr-opendata/1-0/rdf/zeleznicne-trate-SR-2025.ttl"

BASE_URI = "https://data.gov.sk/id/"
OP_BASE = BASE_URI + "operational-point/"
SOL_BASE = BASE_URI + "section-of-line/"
LINE_CATEGORY_BASE = "https://data.gov.sk/def/railways-line-category/"


def normalize(text: str) -> str:
    return " ".join(text.strip().split())


def hash_id(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def make_op_uri(name: str) -> str:
    norm = normalize(name)
    return OP_BASE + hash_id("operational-point|" + norm)


def make_sol_uri(line_code: str) -> str:
    return SOL_BASE + line_code.replace(" ", "-")


def make_line_category_uri(category_code: str) -> str:
    return LINE_CATEGORY_BASE + category_code.strip()


def parse_km(value: str) -> str:
    return value.strip().replace(",", ".")


def escape_ttl_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


operational_points = {}
section_triples = []

with open(INPUT_CSV, "r", encoding="utf-8-sig", newline="") as f:
    next(f)  # preskočí titulkový riadok: Zoznam železničných tratí za rok 2025;;;;
    reader = csv.DictReader(f, delimiter=";")

    print("Fieldnames:", reader.fieldnames)

    for row in reader:
        line_code = normalize(row["Číslo žel. tratí"])
        category = normalize(row["Kategória trate"])
        start = normalize(row["Začiatok trate"])
        end = normalize(row["Koniec trate"])
        length_raw = row[reader.fieldnames[4]]
        length = parse_km(length_raw)

        sol_uri = make_sol_uri(line_code)
        start_uri = make_op_uri(start)
        end_uri = make_op_uri(end)
        category_uri = make_line_category_uri(category)

        operational_points[start_uri] = start
        operational_points[end_uri] = end

        code_escaped = escape_ttl_string(line_code)

        section_triples.append(f"""
<{sol_uri}> a era:SectionOfLine ;
    era:opStart <{start_uri}> ;
    era:opEnd <{end_uri}> ;
    era:lengthOfSectionOfLine "{length}"^^xsd:decimal ;
    adms:identifier [
        skos:notation "{code_escaped}"
    ] ;
    rail:lineCategory <{category_uri}> .
""")


with open(OUTPUT_TTL, "w", encoding="utf-8") as out:
    out.write("""@prefix era: <http://data.europa.eu/949/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix adms: <http://www.w3.org/ns/adms#> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix rail: <https://data.gov.sk/def/ontology/railways/> .

""")

    for uri, name in sorted(operational_points.items()):
        name_escaped = escape_ttl_string(name)
        out.write(f"""
<{uri}> a era:OperationalPoint ;
    era:opName "{name_escaped}"@sk .
""")

    for triple in section_triples:
        out.write(triple)

print("TTL generated:", OUTPUT_TTL)