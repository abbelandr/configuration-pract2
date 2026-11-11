"""Тесты разбора POM XML без сетевых запросов."""

import sys
import unittest
import xml.etree.ElementTree as etree
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from depviz.maven import _namespace, _read_properties, _dependency_coordinates


class MavenTests(unittest.TestCase):
    """Проверка извлечения зависимостей и Maven properties."""

    def test_dependency_and_scope(self):
        """Compile-зависимость извлекается, test-зависимость пропускается."""
        project_xml = (
            '<project><properties><v>1.2</v></properties>'
            '<dependencies/></project>'
        )
        xml = etree.fromstring(project_xml)
        ns = _namespace(xml)
        props = _read_properties(xml, ns)

        good = etree.fromstring(
            '<dependency><groupId>org.demo</groupId>'
            '<artifactId>lib</artifactId><version>${v}</version>'
            '</dependency>'
        )
        bad = etree.fromstring(
            '<dependency><groupId>org.demo</groupId>'
            '<artifactId>test-lib</artifactId><version>1</version>'
            '<scope>test</scope></dependency>'
        )

        self.assertEqual(
            _dependency_coordinates(good, ns, props),
            "org.demo:lib:1.2"
        )
        self.assertIsNone(_dependency_coordinates(bad, ns, props))


if __name__ == "__main__":
    unittest.main()