#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Transform ŠVP PDF (Matematika – 2. stupeň ZŠ) into Turtle (TTL).

What it produces (per your current modeling):
- main ConceptScheme: minedu:scheme-matematika-2-stupen-zs
  - topConcepts: minedu:rocnik-5 .. minedu:rocnik-9
  - each grade has narrower themes (minedu:theme-*)
- VS ConceptScheme: minedu:svp-vykonovy-standard-matematika-2-stupen-zs
  - VS concepts are skos:narrower of themes; each VS has skos:relatedMatch to OS concepts
- OS ConceptScheme: minedu:svp-obsahovy-standard-matematika-2-stupen-zs
- LO/LAS per (grade, theme)
- edu:studyGrade links (https://data.gov.sk/def/ontology/education/studyGrade)
- noise removed (page numbers, repeated header/footer fragments)

Usage:
    python svp_pdf_to_ttl.py /path/to/input.pdf -o output.ttl

Dependencies:
    pip install pdfplumber rdflib
"""

import argparse
import re
import unicodedata
from collections import defaultdict, OrderedDict
from pathlib import Path

import pdfplumber
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, SKOS, DCTERMS


# -----------------------------
# Configuration (edit if needed)
# -----------------------------

THEMES = [
    "Vytvorenie oboru prirodzených čísel do a nad milión",
    "Počtové výkony s prirodzenými číslami",
    "Geometria a meranie",
    "Súmernosť v rovine (osová a stredová)",
    "Riešenie aplikačných úloh a úloh rozvíjajúcich špecifické matematické myslenie",
    "Počtové výkony s prirodzenými číslami, deliteľnosť",
    "Desatinné čísla, počtové výkony (operácie) s desatinnými číslami",
    "Obsah obdĺžnika, štvorca a pravouhlého trojuholníka v desatinných číslach, jednotky obsahu",
    "Uhol a jeho veľkosť, operácie s uhlami",
    "Trojuholník, zhodnosť trojuholníkov",
    "Kombinatorika v kontextových úlohách",
    "Zlomky, počtové výkony so zlomkami, kladné racionálne čísla",
    "Percentá, promile",
    "Kváder a kocka, ich povrch a objem v desatinných číslach, premieňanie jednotiek objemu",
    "Pomer, priama a nepriama úmernosť",
    "Kombinatorika",
    "Kladné a záporné čísla, počtové výkony s celými a desatinnými číslami, racionálne čísla",
    "Premenná, výraz",
    "Rovnobežník, lichobežník, obvod a obsah rovnobežníka, lichobežníka a trojuholníka",
    "Kruh, kružnica",
    "Hranol",
    "Pravdepodobnosť, štatistika",
    "Mocniny a odmocniny, zápis veľkých čísel",
    "Pytagorova veta",
    "Ihlan, valec, kužeľ, guľa, ich objem a povrch",
    "Riešenie lineárnych rovníc a nerovníc s jednou neznámou",
    "Podobnosť trojuholníkov",
    "Štatistika",
    "Grafické znázorňovanie závislostí",
]

# Column split: left (VS) / right (OS). Adjust if your PDF layout differs.
DEFAULT_XSPLIT = 400

# ELM / subject / education level (as per your current mapping)
ISCEDF_MATH = URIRef("http://data.europa.eu/snb/isced-f/054")
EDU_LEVEL_ISCED2 = URIRef("http://publications.europa.eu/resource/authority/education-level/ISCED_2")

# Namespaces
MINEDU = Namespace("http://minedu.sk/def/")
ELM = Namespace("http://data.europa.eu/snb/model/ontology/")
EDU = Namespace("https://data.gov.sk/def/ontology/education/")

SCHEME_MAIN = MINEDU["scheme-matematika-2-stupen-zs"]
SCHEME_VS = MINEDU["svp-vykonovy-standard-matematika-2-stupen-zs"]
SCHEME_OS = MINEDU["svp-obsahovy-standard-matematika-2-stupen-zs"]


# -----------------------------
# Helpers
# -----------------------------

def norm(s: str) -> str:
    s = s.strip().replace("–", "-")
    s = re.sub(r"\s+", " ", s)
    return s.lower()

def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    text = re.sub(r"-{2,}", "-", text)
    return text

def theme_iri(theme: str) -> URIRef:
    return MINEDU[f"theme-{slugify(theme)}"]

def grade_iri(grade: int) -> URIRef:
    return MINEDU[f"rocnik-{grade}"]

def lo_iri(theme: str, grade: int) -> URIRef:
    return URIRef(f"http://minedu.sk/id/learning-opportunity/matematika-{grade}-rocnik-{slugify(theme)}")

def las_iri(theme: str, grade: int) -> URIRef:
    return URIRef(f"http://minedu.sk/id/learning-achievement-specification/{slugify(theme)}-las-{grade}")

def vs_iri(label: str) -> URIRef:
    return URIRef(f"http://minedu.sk/def/vykonovy-standard/{slugify(label.rstrip('.'))}")

def os_iri(label: str) -> URIRef:
    return URIRef(f"http://minedu.sk/def/obsahovy-standard/{slugify(label.rstrip('.'))}")

def study_grade_uri(grade: int) -> URIRef:
    return URIRef(f"https://data.gov.sk/def/study-grade/{grade}")

# Noise patterns (header/footer/pages) – aggressively removed from VS/OS concepts
NOISE_PATTERNS = [
    re.compile(r"^\s*\d{1,3}\s*$"),  # page number
    re.compile(r"nižšie\s*stredné\s*vzdelanie", re.IGNORECASE),
    re.compile(r"matematika\s*[–-]\s*nižšie\s*stredné\s*vzdelanie", re.IGNORECASE),
    re.compile(r"štátny\s*pedagogický\s*ústav", re.IGNORECASE),
    re.compile(r"pedagogický\s*ústav", re.IGNORECASE),
    re.compile(r"^©", re.IGNORECASE),
]

def is_noise_text(text: str) -> bool:
    s = (text or "").strip()
    return any(p.search(s) for p in NOISE_PATTERNS)

def split_lines(page, xsplit: int = DEFAULT_XSPLIT, ytol: float = 2.0):
    """
    Extract lines as (left_text, right_text) using word positions and a vertical splitter.
    """
    words = page.extract_words(use_text_flow=True, keep_blank_chars=False)
    if not words:
        return []

    ys = sorted(set(w["top"] for w in words))
    clusters = []
    for y in ys:
        for c in clusters:
            if abs(c["y"] - y) <= ytol:
                c["ys"].append(y)
                break
        else:
            clusters.append({"y": y, "ys": [y]})

    lines = []
    for c in sorted(clusters, key=lambda x: x["y"]):
        ws = [w for w in words if any(abs(w["top"] - yy) <= ytol for yy in c["ys"])]
        left = [w for w in ws if w["x0"] < xsplit]
        right = [w for w in ws if w["x0"] >= xsplit]

        def join(parts):
            return " ".join(w["text"] for w in sorted(parts, key=lambda x: x["x0"])).strip()

        lt, rt = join(left), join(right)
        if lt or rt:
            lines.append((lt, rt))
    return lines


# -----------------------------
# PDF -> records
# -----------------------------

def parse_pdf(pdf_path: Path, xsplit: int = DEFAULT_XSPLIT):
    """
    Returns list of records:
      { theme: str, grade: int, vs: [str], os: [str] }
    """
    themes_norm = [(norm(t), t) for t in THEMES]

    records = []
    current_theme = None
    current_grade = None
    collecting = False
    pending_bullet = False
    vs_buf, os_buf = [], []

    def flush():
        nonlocal vs_buf, os_buf, current_theme, current_grade
        if current_theme and current_grade and (vs_buf or os_buf):
            # remove obvious noise from buffers (in case it slipped in)
            vs_clean = [v for v in vs_buf if not is_noise_text(v)]
            os_clean = [o for o in os_buf if not is_noise_text(o)]
            if vs_clean or os_clean:
                records.append({"theme": current_theme, "grade": current_grade, "vs": vs_clean, "os": os_clean})
        vs_buf, os_buf = [], []

    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            for lt, rt in split_lines(page, xsplit=xsplit):
                line = (lt + " " + rt).strip()
                nline = norm(line)

                # Theme start
                matched = None
                for tn, torig in themes_norm:
                    if nline.startswith(tn):
                        matched = torig
                        break
                if matched:
                    flush()
                    current_theme = matched
                    current_grade = None
                    collecting = False
                    pending_bullet = False
                    continue

                # Grade marker
                m = re.search(r"Žiak na konci\s+(\d+)\.\s*ročníka", line)
                if m:
                    current_grade = int(m.group(1))
                    collecting = True
                    pending_bullet = False
                    continue

                if not collecting:
                    continue

                # OS content tends to be right column
                if rt and "Obsahový štandard" not in rt and "Výkonový štandard" not in rt:
                    txt = rt.strip().rstrip(",")
                    if txt and txt not in os_buf:
                        os_buf.append(txt)

                # VS bullets are on the left with the check mark
                if "" in lt.split():
                    pending_bullet = True
                    rest = lt.replace("", "").strip().rstrip(",")
                    if rest:
                        vs_buf.append(rest)
                        pending_bullet = False
                    continue

                if pending_bullet and lt:
                    txt = lt.strip().rstrip(",")
                    if txt:
                        vs_buf.append(txt)
                    pending_bullet = False

    flush()
    return records


# -----------------------------
# Records -> RDF graph
# -----------------------------

def build_graph(records):
    g = Graph()
    g.bind("elm", ELM)
    g.bind("skos", SKOS)
    g.bind("dct", DCTERMS)
    g.bind("minedu", MINEDU)
    g.bind("edu", EDU)

    # Schemes
    g.add((SCHEME_MAIN, RDF.type, SKOS.ConceptScheme))
    g.add((SCHEME_MAIN, SKOS.prefLabel, Literal("Matematika – 2. stupeň ZŠ (ISCED 2)", lang="sk")))
    g.add((SCHEME_MAIN, DCTERMS.subject, ISCEDF_MATH))
    g.add((SCHEME_MAIN, DCTERMS.source, Literal("Štátny vzdelávací program pre 2. stupeň ZŠ", lang="sk")))

    g.add((SCHEME_VS, RDF.type, SKOS.ConceptScheme))
    g.add((SCHEME_VS, SKOS.prefLabel, Literal("ŠVP – výkonový štandard – Matematika – 2. stupeň ZŠ", lang="sk")))
    g.add((SCHEME_VS, DCTERMS.subject, ISCEDF_MATH))
    g.add((SCHEME_VS, DCTERMS.source, Literal("Štátny vzdelávací program pre 2. stupeň ZŠ", lang="sk")))

    g.add((SCHEME_OS, RDF.type, SKOS.ConceptScheme))
    g.add((SCHEME_OS, SKOS.prefLabel, Literal("ŠVP – obsahový štandard – Matematika – 2. stupeň ZŠ", lang="sk")))
    g.add((SCHEME_OS, DCTERMS.subject, ISCEDF_MATH))
    g.add((SCHEME_OS, DCTERMS.source, Literal("Štátny vzdelávací program pre 2. stupeň ZŠ", lang="sk")))

    # index structures
    grade_to_theme = defaultdict(set)
    theme_to_vs = defaultdict(set)
    vs_to_os = defaultdict(set)
    theme_labels = OrderedDict()
    vs_labels = OrderedDict()
    os_labels = OrderedDict()

    las_to_vs = defaultdict(set)
    las_to_os = defaultdict(set)

    # Collect
    for r in records:
        theme = r["theme"]
        grade = int(r["grade"])
        t = theme_iri(theme)
        theme_labels.setdefault(t, theme)
        grade_to_theme[grade_iri(grade)].add(t)

        lo = lo_iri(theme, grade)
        las = las_iri(theme, grade)

        # LO
        g.add((lo, RDF.type, ELM.LearningOpportunity))
        g.add((lo, ELM.learningActivitySpecification, las))
        g.add((lo, SKOS.related, t))
        g.add((lo, ELM.educationLevel, EDU_LEVEL_ISCED2))
        g.add((lo, EDU.studyGrade, study_grade_uri(grade)))
        g.add((lo, DCTERMS.subject, ISCEDF_MATH))
        g.add((lo, SKOS.prefLabel, Literal(f"Matematika – {grade}. ročník – {theme}", lang="sk")))

        # LAS
        g.add((las, RDF.type, ELM.LearningAchievementSpecification))
        g.add((las, SKOS.related, lo))
        g.add((las, SKOS.related, t))
        g.add((las, ELM.ISCEDFCode, ISCEDF_MATH))
        g.add((las, EDU.studyGrade, study_grade_uri(grade)))
        g.add((las, SKOS.prefLabel, Literal(f"{theme} – {grade}. ročník (LAS)", lang="sk")))

        local_vs = set()
        local_os = set()

        for v in r.get("vs", []):
            if is_noise_text(v):
                continue
            vu = vs_iri(v)
            vs_labels.setdefault(vu, v.strip().rstrip(","))
            theme_to_vs[t].add(vu)
            local_vs.add(vu)
            las_to_vs[las].add(vu)

        for o in r.get("os", []):
            if is_noise_text(o):
                continue
            ou = os_iri(o)
            os_labels.setdefault(ou, o.strip().rstrip(","))
            local_os.add(ou)
            las_to_os[las].add(ou)

        for vu in local_vs:
            vs_to_os[vu].update(local_os)

    # Grade concepts (topConcepts)
    grades = sorted({int(str(gc).split("-")[-1]) for gc in grade_to_theme.keys() if "-" in str(gc)})
    for gr in range(5, 10):
        if gr not in grades:
            grades.append(gr)
    grades = sorted(set(grades))

    for gr in grades:
        gc = grade_iri(gr)
        g.add((gc, RDF.type, SKOS.Concept))
        g.add((gc, SKOS.inScheme, SCHEME_MAIN))
        g.add((gc, SKOS.topConceptOf, SCHEME_MAIN))
        g.add((gc, SKOS.prefLabel, Literal(f"{gr}. ročník", lang="sk")))
        g.add((gc, SKOS.exactMatch, study_grade_uri(gr)))
        g.add((SCHEME_MAIN, SKOS.hasTopConcept, gc))

    # Theme concepts and navigation grade->theme
    for t, label in theme_labels.items():
        g.add((t, RDF.type, SKOS.Concept))
        g.add((t, SKOS.inScheme, SCHEME_MAIN))
        g.add((t, SKOS.prefLabel, Literal(label, lang="sk")))

    for gc, themes in grade_to_theme.items():
        for t in sorted(themes, key=str):
            g.add((gc, SKOS.narrower, t))
            g.add((t, SKOS.broader, gc))

    # VS concepts, linked under themes (narrower) + related to LAS
    for vu, label in vs_labels.items():
        g.add((vu, RDF.type, SKOS.Concept))
        g.add((vu, SKOS.inScheme, SCHEME_VS))
        g.add((vu, SKOS.prefLabel, Literal(label, lang="sk")))

    for t, vsset in theme_to_vs.items():
        for vu in sorted(vsset, key=str):
            g.add((t, SKOS.narrower, vu))
            g.add((vu, SKOS.broader, t))

    for las, vsset in las_to_vs.items():
        for vu in vsset:
            g.add((vu, SKOS.related, las))

    # OS concepts + related to LAS
    for ou, label in os_labels.items():
        g.add((ou, RDF.type, SKOS.Concept))
        g.add((ou, SKOS.inScheme, SCHEME_OS))
        g.add((ou, SKOS.prefLabel, Literal(label, lang="sk")))

    for las, osset in las_to_os.items():
        for ou in osset:
            g.add((ou, SKOS.related, las))

    # VS -> OS mapping (same section)
    for vu, targets in vs_to_os.items():
        if not targets:
            continue
        for ou in sorted(targets, key=str):
            g.add((vu, SKOS.relatedMatch, ou))

    return g


# -----------------------------
# Post-clean (safety net)
# -----------------------------

def clean_graph(g: Graph) -> Graph:
    """
    Second-pass cleaning: remove any VS/OS concept whose prefLabel matches noise patterns.
    """
    to_remove = set()

    for c in set(g.subjects(RDF.type, SKOS.Concept)):
        in_vs = (c, SKOS.inScheme, SCHEME_VS) in g
        in_os = (c, SKOS.inScheme, SCHEME_OS) in g
        if not (in_vs or in_os):
            continue
        labels = list(g.objects(c, SKOS.prefLabel))
        if any(is_noise_text(str(l)) for l in labels):
            to_remove.add(c)

    for c in to_remove:
        for p, o in list(g.predicate_objects(c)):
            g.remove((c, p, o))
        for s, p in list(g.subject_predicates(c)):
            g.remove((s, p, c))

    # remove dangling relatedMatch
    def has_preflabel(u: URIRef) -> bool:
        return any(True for _ in g.objects(u, SKOS.prefLabel))

    for s, o in list(g.subject_objects(SKOS.relatedMatch)):
        if (not has_preflabel(s)) or (not has_preflabel(o)):
            g.remove((s, SKOS.relatedMatch, o))

    return g


# -----------------------------
# CLI
# -----------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf", type=Path, help="Input PDF path")
    ap.add_argument("-o", "--out", type=Path, default=Path("minedu_matematika_2stupen.ttl"), help="Output TTL path")
    ap.add_argument("--xsplit", type=int, default=DEFAULT_XSPLIT, help="X position separating VS/OS columns")
    args = ap.parse_args()

    if not args.pdf.exists():
        raise SystemExit(f"PDF not found: {args.pdf}")

    records = parse_pdf(args.pdf, xsplit=args.xsplit)
    g = build_graph(records)
    g = clean_graph(g)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    g.serialize(destination=str(args.out), format="turtle")
    print(f"Wrote: {args.out} (records={len(records)})")


if __name__ == "__main__":
    main()
