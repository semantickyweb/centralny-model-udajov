from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

from rdflib import Graph, URIRef
from rdflib.namespace import RDF


SCRIPT = Path(__file__).resolve().parents[1] / "build_zsr_opendata.py"
SPEC = importlib.util.spec_from_file_location("build_zsr_opendata", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class BuildZsrOpenDataTest(unittest.TestCase):
    def test_normalizes_nested_percent_encoding(self):
        iri = URIRef("http://data.europa.eu/949/track/line%252F1_%25C5%25A1")
        self.assertEqual(MODULE.iri_last_segment(iri), "line%2F1_%C5%A1")

    def test_uses_source_era_uri_for_local_identifier(self):
        source = URIRef("http://data.europa.eu/949/operationalPoint/abc123")
        self.assertEqual(
            MODULE.local_entity_iri("operational-point", source),
            URIRef("https://data.gov.sk/id/era/operational-point/abc123"),
        )

    def test_rewrites_links_and_adds_both_provenance_targets(self):
        graph = Graph()
        graph_iri = URIRef("http://data.europa.eu/949/graph/0056")
        class_iri = URIRef("http://data.europa.eu/949/OperationalPoint")
        relation = URIRef("http://data.europa.eu/949/relatedTo")
        first = URIRef("http://data.europa.eu/949/operationalPoint/a")
        second = URIRef("http://data.europa.eu/949/operationalPoint/b")
        local_first = URIRef("https://data.gov.sk/id/era/operational-point/a")
        local_second = URIRef("https://data.gov.sk/id/era/operational-point/b")
        graph.add((first, RDF.type, class_iri))
        graph.add((first, relation, second))
        iri_map = {first: local_first, second: local_second}
        definition = MODULE.DatasetDefinition(
            "operational-points",
            "operational-point",
            class_iri,
            "era-rinf-0056",
            MODULE.SUPPORTED_ID_STRATEGY,
            None,
        )

        output = MODULE.build_dataset_graph(
            graph, definition, [first], iri_map, graph_iri
        )

        self.assertIn((local_first, relation, local_second), output)
        self.assertIn(
            (local_first, MODULE.PROV_WAS_DERIVED_FROM, first), output
        )
        self.assertIn(
            (local_first, MODULE.PROV_WAS_DERIVED_FROM, graph_iri), output
        )


if __name__ == "__main__":
    unittest.main()
