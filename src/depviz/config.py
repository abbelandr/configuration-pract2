"""Разбор и проверка параметров командной строки."""

import argparse
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

DEFAULT_REPOSITORY = "https://repo.maven.apache.org/maven2"
EXPECTED_COORDINATES = 3


@dataclass(frozen=True)
class Config:
    """Неизменяемые настройки запуска."""
    package: str
    repository: str
    test_mode: bool
    test_file: str
    output: str
    ascii_tree: bool
    filter_text: str
    reverse: bool


def parse_config(arguments=None):
    """Разобрать аргументы и проверить их."""
    parser = argparse.ArgumentParser(
        description="Визуализация графа зависимостей Maven."
    )
    parser.add_argument("--package", required=True)
    parser.add_argument("--repository", default=DEFAULT_REPOSITORY)
    parser.add_argument("--test-mode", action="store_true")
    parser.add_argument("--test-file", default="data/test_repository.json")
    parser.add_argument("--output", default="dependencies.png")
    parser.add_argument("--ascii-tree", action="store_true")
    parser.add_argument("--filter", dest="filter_text", default="")
    parser.add_argument("--reverse", action="store_true")
    args = parser.parse_args(arguments)

    _validate_package(args.package, args.test_mode)
    _validate_repository(args.repository, args.test_mode)
    _validate_output(args.output)
    _validate_test_file(args.test_file, args.test_mode)
    return Config(**vars(args))


def _validate_package(value, test_mode):
    """Проверить имя пакета или координаты."""
    if not value.strip():
        raise ValueError("Имя пакета не может быть пустым.")
    if test_mode:
        if not value.isalpha() or not value.isupper():
            raise ValueError("В тестовом режиме имя должно быть A-Z.")
        return

    parts = value.split(":")
    if len(parts) != EXPECTED_COORDINATES:
        raise ValueError("Ожидаются координаты groupId:artifactId:version.")
    if not all(part.strip() for part in parts):
        raise ValueError("Части координат не могут быть пустыми.")


def _validate_repository(value, test_mode):
    """Проверить URL репозитория."""
    if test_mode:
        return
    parsed = urlparse(value)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError("Репозиторий должен быть HTTP(S)-URL.")


def _validate_output(value):
    """Проверить имя PNG-файла."""
    if not value.strip() or Path(value).suffix.lower() != ".png":
        raise ValueError("Выходной файл должен иметь расширение .png.")


def _validate_test_file(value, test_mode):
    """Проверить наличие тестового файла."""
    if test_mode and not Path(value).is_file():
        raise ValueError(f"Тестовый файл не найден: {value}")


def print_config(config):
    """Напечатать настройки ключ-значение."""
    for key, value in vars(config).items():
        print(f"{key} = {value}")