"""Тесты DFS, фильтра, циклов и обратных зависимостей."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from depviz.graph import build_graph, reverse_dependencies, ascii_tree


class GraphTests(unittest.TestCase):
    """Проверки построения графа на небольших фикстурах."""

    data = {
        "A": ["B", "C"],
        "B": ["D"],
        "C": ["D"],
        "D": ["A"],
    }

    def test_dfs_visits_cycle_once(self):
        """Цикл A-B-D-A не вызывает бесконечный обход."""
        graph = build_graph("A", lambda node: self.data[node])
        self.assertEqual(set(graph), {"A", "B", "C", "D"})

    def test_filter_excludes_matching_names(self):
        """Подстрока фильтра исключает соответствующие вершины."""
        graph = build_graph(
            "A", lambda node: self.data[node], filter_text="C"
        )
        self.assertNotIn("C", graph["A"])

    def test_reverse_dependencies(self):
        """Обратный обход находит узлы, зависящие от D."""
        graph = build_graph("A", lambda node: self.data[node])
        self.assertEqual(reverse_dependencies(graph, "D"), ["A", "B", "C"])

    def test_ascii_tree_marks_cycle(self):
        """ASCII-дерево отмечает повторное попадание в предка."""
        graph = build_graph("A", lambda node: self.data[node])
        tree = ascii_tree(graph, "A")

        self.assertIn("(cycle)", tree)
        self.assertLess(tree.index("B"), tree.index("D"))


if __name__ == "__main__":
    unittest.main()