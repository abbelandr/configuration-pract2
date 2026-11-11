"""Командный интерфейс и последовательность выполнения этапов."""

import sys

from depviz.config import parse_config, print_config
from depviz.graph import (
    ascii_tree,
    build_graph,
    load_test_graph,
    reverse_dependencies,
    test_provider,
)
from depviz.maven import direct_dependencies
from depviz.visualize import render_png


def _provider_for(config):
    """Подготовить источник зависимостей для выбранного режима."""
    if config.test_mode:
        graph = load_test_graph(config.test_file)
        return test_provider(graph), graph

    cache = {}

    def provide(package):
        if package not in cache:
            cache[package] = direct_dependencies(package, config.repository)
        return cache[package]

    return provide, None


def _show_direct(config, provider):
    """Вывести прямые зависимости корневого пакета."""
    direct = provider(config.package)
    print("\nПрямые зависимости:")
    if direct:
        for dependency in direct:
            print(f"  - {dependency}")
    else:
        print("  (нет)")


def _show_reverse(graph, package):
    """Вывести обратные зависимости выбранного пакета."""
    result = reverse_dependencies(graph, package)
    print(f"\nОбратные зависимости для {package}:")
    for dependency in result:
        print(f"  - {dependency}")
    if not result:
        print("  (нет)")


def run(config):
    """Выполнить сбор данных, обход, обратный анализ и визуализацию."""
    provider, test_graph = _provider_for(config)
    if config.test_mode and config.package not in test_graph:
        msg = f"Пакет {config.package} отсутствует в тестовом графе."
        raise ValueError(msg)

    _show_direct(config, provider)
    graph = build_graph(config.package, provider, config.filter_text)

    print(f"\nПостроено вершин: {len(graph)}")
    if config.reverse:
        _show_reverse(graph, config.package)

    if config.ascii_tree:
        print("\nASCII-дерево:")
        print(ascii_tree(graph, config.package))

    image, dot = render_png(graph, config.output)
    print(f"\nDOT: {dot}")
    print(f"PNG: {image}")


def main():
    """Точка входа CLI с единообразной обработкой ошибок."""
    try:
        config = parse_config()
        print("Параметры запуска:")
        print_config(config)
        run(config)
    except (ValueError, RuntimeError) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 1
    return 0