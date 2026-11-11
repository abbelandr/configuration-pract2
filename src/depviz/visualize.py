"""Экспорт графа в Graphviz DOT и PNG."""

import shutil
import subprocess
from pathlib import Path

SUCCESS_CODE = 0
IMAGE_FORMAT = "png"


def to_dot(graph):
    """Преобразовать граф в текст Graphviz DOT."""
    lines = ["digraph dependencies {", "  rankdir=LR;", "  node [shape=box];"]
    for package in sorted(graph):
        if not graph[package]:
            lines.append(f"  {_quote(package)};")
        for dependency in graph[package]:
            lines.append(f"  {_quote(package)} -> {_quote(dependency)};")
    lines.append("}")
    return "\n".join(lines) + "\n"


def _quote(value):
    """Экранировать подпись вершины для DOT."""
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def render_png(graph, output):
    """Сохранить DOT и отрендерить PNG через Graphviz."""
    image_path = Path(output)
    dot_path = image_path.with_suffix(".dot")
    image_path.parent.mkdir(parents=True, exist_ok=True)
    dot_path.write_text(to_dot(graph), encoding="utf-8")

    executable = shutil.which("dot")
    if executable is None:
        msg = (
            "Graphviz не найден. Установите Graphviz и добавьте dot в PATH. "
            f"Файл DOT сохранён: {dot_path}"
        )
        raise RuntimeError(msg)

    command = [
        executable, f"-T{IMAGE_FORMAT}", str(dot_path), "-o", str(image_path)
    ]
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as error:
        detail = error.stderr.strip() or str(error)
        raise RuntimeError(f"Graphviz не смог создать PNG: {detail}") from error
    return image_path, dot_path