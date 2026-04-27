import csv
import hashlib

INPUT_CSV = "abox/semantickyweb/era/zsr-opendata/1-0/csv/zoznam-stanic-a-zastavok.csv"
OUTPUT_OP_TTL = "abox/semantickyweb/era/zsr-opendata/1-0/rdf/zoznam-stanic-a-zastavok.ttl"

BASE_URI = "https://data.gov.sk/id/"
OP_BASE = BASE_URI + "operational-point/"

ERA_OP_TYPES = {
    "železničná stanica": "http://data.europa.eu/949/concepts/op-types/10",
    "zastávka": "http://data.europa.eu/949/concepts/op-types/70",
}


def normalize(text: str) -> str:
    return " ".join(text.strip().split())


def hash_id(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def make_op_uri(name: str) -> str:
    norm = normalize(name)
    return OP_BASE + hash_id("operational-point|" + norm)


def escape_ttl_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def map_op_type(raw_type: str) -> str:
    key = normalize(raw_type).lower()
    if key not in ERA_OP_TYPES:
        raise ValueError(f"Unknown operational point type: {raw_type}")
    return ERA_OP_TYPES[key]


def map_prm_access(raw_value: str) -> str:
    key = normalize(raw_value).upper()
    if key in ["ÁNO", "ANO"]:
        return "true"
    if key in ["N/A", "NIE"]:
        return "false"
    raise ValueError(f"Unknown PRM access value: {raw_value}")


def parse_timetable_lines(raw_value: str) -> list[str]:
    raw_value = normalize(raw_value)
    if not raw_value:
        return []
    return [part.strip() for part in raw_value.split(",") if part.strip()]


operational_points = {}

with open(INPUT_CSV, "r", encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f, delimiter=";")
    print("Fieldnames:", reader.fieldnames)

    for row in reader:
        name = normalize(row["Názov"])
        raw_type = normalize(row["Druh"])
        raw_prm = normalize(row["PRM prístup"])
        raw_timetable = normalize(row["Cestovné poriadky"])

        op_uri = make_op_uri(name)

        operational_points[op_uri] = {
            "name": name,
            "op_type_uri": map_op_type(raw_type),
            "has_prm": map_prm_access(raw_prm),
            "timetable_lines": parse_timetable_lines(raw_timetable),
        }

with open(OUTPUT_OP_TTL, "w", encoding="utf-8") as out:
    out.write("""@prefix era: <http://data.europa.eu/949/> .
@prefix rail: <https://data.gov.sk/def/ontology/railways/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

""")

    for uri, data in sorted(operational_points.items(), key=lambda item: item[1]["name"]):
        name_escaped = escape_ttl_string(data["name"])

        out.write(f"<{uri}> a era:OperationalPoint ;\n")
        out.write(f'    era:opName "{name_escaped}"@sk ;\n')
        out.write(f'    era:opType <{data["op_type_uri"]}> ;\n')
        out.write(f'    rail:hasPrmAccess "{data["has_prm"]}"^^xsd:boolean')

        timetable_lines = data["timetable_lines"]
        if timetable_lines:
            out.write(" ;\n")
            for i, line in enumerate(timetable_lines):
                end = " ;\n" if i < len(timetable_lines) - 1 else " .\n\n"
                out.write(f'    rail:timetableLine "{escape_ttl_string(line)}"{end}')
        else:
            out.write(" .\n\n")

print("TTL generated:", OUTPUT_OP_TTL)