"""Построение графа зависимостей итеративным DFS."""

from collections import defaultdict


def build_graph(root, provider, filter_text=""):
    """Обойти зависимости DFS без рекурсии и вернуть граф смежности."""
    graph = {}
    visited = set()
    stack = [root]
    while stack:
        package = stack.pop()
        if package in visited:
            continue
        visited.add(package)
        children = provider(package)
        accepted = _filter_packages(children, filter_text)
        graph[package] = accepted
        for child in reversed(accepted):
            if child not in visited:
                stack.append(child)
    return graph


def _filter_packages(packages, filter_text):
    """Исключить пакеты, содержащие фильтруемую подстроку."""
    if not filter_text:
        return sorted(set(packages))
    return sorted(
        package for package in set(packages)
        if filter_text.casefold() not in package.casefold()
    )


def load_test_graph(path):
    """Загрузить тестовый граф из JSON и проверить имена вершин."""
    import json
    from pathlib import Path

    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        msg = f"Не удалось прочитать тестовый граф: {error}"
        raise ValueError(msg) from error

    if not isinstance(data, dict):
        raise ValueError("Корень тестового JSON должен быть объектом.")

    graph = {}
    for node, children in data.items():
        _validate_test_node(node)
        if not isinstance(children, list):
            msg = f"Список зависимостей узла {node} должен быть массивом."
            raise ValueError(msg)
        for child in children:
            _validate_test_node(child)
        graph[node] = sorted(set(children))
    return graph


def _validate_test_node(node):
    """Проверить имя тестового пакета: только заглавные буквы."""
    if not isinstance(node, str) or not node.isalpha() or not node.isupper():
        raise ValueError(f"Недопустимое имя узла тестового графа: {node!r}")


def test_provider(graph):
    """Создать функцию получения зависимостей из тестового графа."""
    def provide(package):
        return graph.get(package, [])
    return provide


def reverse_dependencies(graph, target):
    """Найти все пакеты, имеющие прямой путь к выбранному узлу."""
    reverse = defaultdict(set)
    for package, dependencies in graph.items():
        for dependency in dependencies:
            reverse[dependency].add(package)
    found = set()
    stack = list(reverse.get(target, set()))
    while stack:
        package = stack.pop()
        if package in found or package == target:
            continue
        found.add(package)
        stack.extend(reverse.get(package, set()))
    return sorted(found)


def ascii_tree(graph, root):
    """Сформировать дерево зависимостей с защитой от циклов."""
    lines = [str(root)]
    stack = [(root, "", frozenset({root}), False, "")]
    while stack:
        node, prefix, ancestors, is_root, label = stack.pop()
        if not is_root:
            lines.append(prefix + label)
        children = graph.get(node, [])
        for index in range(len(children) - 1, -1, -1):
            child = children[index]
            is_last = index == len(children) - 1
            branch = "└── " if is_last else "├── "
            marker = " (cycle)" if child in ancestors else ""
            next_prefix = prefix + ("    " if is_last else "│   ")
            if child not in ancestors:
                stack.append((
                    child, next_prefix, ancestors | {child}, False,
                    branch + child
                ))
            else:
                lines.append(prefix + branch + child + marker)
    return "\n".join(lines)