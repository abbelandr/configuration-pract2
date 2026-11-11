"""Тесты проверки параметров командной строки."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from depviz.config import parse_config


class ConfigTests(unittest.TestCase):
    """Проверки обязательных и некорректных параметров."""

    def test_valid_test_configuration(self):
        """Корректная конфигурация тестового режима принимается."""
        config = parse_config([
            "--package", "A",
            "--test-mode",
            "--test-file", "data/test_repository.json"
        ])
        self.assertTrue(config.test_mode)

    def test_invalid_package_coordinates(self):
        """Сетевой режим требует три части Maven-координат."""
        with self.assertRaises(ValueError):
            parse_config(["--package", "wrong"])

    def test_invalid_png_extension(self):
        """Имя результата должно оканчиваться на PNG."""
        with self.assertRaises(ValueError):
            parse_config([
                "--package", "A",
                "--test-mode",
                "--test-file", "data/test_repository.json",
                "--output", "graph.jpg"
            ])


if __name__ == "__main__":
    unittest.main()