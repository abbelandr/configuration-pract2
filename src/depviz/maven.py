"""Получение прямых зависимостей из POM без Maven и внешних библиотек."""

import re
import ssl
import urllib.error
import urllib.request
import xml.etree.ElementTree as etree
from pathlib import Path

TIMEOUT_SECONDS = 15
MAX_RESOLVE_DEPTH = 5
EXPECTED_PARTS = 3
SKIPPED_SCOPES = {"test", "provided", "system", "import"}
PROPERTY_PATTERN = re.compile(r"\$\{([^}]+)\}")


def parse_coordinates(coordinates):
    """Разделить Maven-координаты groupId:artifactId:version."""
    parts = coordinates.split(":")
    if len(parts) != EXPECTED_PARTS or not all(parts):
        msg = "Координаты должны иметь вид groupId:artifactId:version."
        raise ValueError(msg)
    return tuple(parts)


def pom_url(coordinates, repository):
    """Построить URL POM-файла по Maven-координатам."""
    group, artifact, version = parse_coordinates(coordinates)
    group_path = group.replace(".", "/")
    base = repository.rstrip("/")
    filename = f"{artifact}-{version}.pom"
    return f"{base}/{group_path}/{artifact}/{version}/{filename}"


def _get_local_path(coordinates):
    """Сформировать путь к локальному файлу POM в папке data."""
    _, artifact, version = parse_coordinates(coordinates)
    local_filename = f"{artifact}-{version}.pom"
    return Path(__file__).parent.parent.parent / "data" / local_filename


def _load_network_pom(address):
    """Скачать и распарсить POM из сети (игнорируя ошибки SSL)."""
    request = urllib.request.Request(
        address, headers={"User-Agent": "DependencyVisualizer/1.0"}
    )
    context = ssl._create_unverified_context()

    try:
        print(f"[*] Скачивание из сети: {address}")
        with urllib.request.urlopen(
            request, timeout=TIMEOUT_SECONDS, context=context
        ) as response:
            content = response.read()
        return etree.fromstring(content)
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        msg = f"Не удалось загрузить POM {address}: {error}"
        raise RuntimeError(msg) from error
    except etree.ParseError as error:
        msg = f"Некорректный XML в POM {address}: {error}"
        raise RuntimeError(msg) from error


def fetch_pom(coordinates, repository):
    """Загрузить POM. Сначала проверяем локальный файл, потом сеть."""
    address = pom_url(coordinates, repository)
    local_path = _get_local_path(coordinates)

    if local_path.is_file():
        print(f"[*] Используется локальный POM: {local_path}")
        return etree.fromstring(local_path.read_bytes())

    return _load_network_pom(address)


def direct_dependencies(coordinates, repository):
    """Получить список прямых зависимостей указанной версии пакета."""
    root = fetch_pom(coordinates, repository)
    namespace = _namespace(root)
    properties = _read_properties(root, namespace)
    result = []
    dependencies = root.find(f"{namespace}dependencies")
    if dependencies is None:
        return result

    for dependency in dependencies.findall(f"{namespace}dependency"):
        item = _dependency_coordinates(dependency, namespace, properties)
        if item:
            result.append(item)
    return sorted(set(result))


def _namespace(root):
    """Определить XML namespace Maven POM."""
    if root.tag.startswith("{"):
        return root.tag.split("}", 1)[0] + "}"
    return ""


def _read_properties(root, namespace):
    """Считать простые свойства из секции properties."""
    section = root.find(f"{namespace}properties")
    if section is None:
        return {}
    return {
        child.tag.split("}")[-1]: (child.text or "").strip()
        for child in list(section)
    }


def _resolve(value, properties):
    """Подставить известные Maven properties в значение."""
    if not value:
        return ""
    for _ in range(MAX_RESOLVE_DEPTH):
        match = PROPERTY_PATTERN.search(value)
        if not match:
            break
        replacement = properties.get(match.group(1))
        if replacement is None:
            return ""
        value = value[:match.start()] + replacement + value[match.end():]
    return value.strip()


def _dependency_coordinates(dependency, namespace, properties):
    """Извлечь координаты зависимости и отфильтровать служебные scope."""
    values = {}
    for name in ("groupId", "artifactId", "version", "scope", "optional"):
        node = dependency.find(f"{namespace}{name}")
        if node is not None:
            values[name] = (node.text or "").strip()
        else:
            values[name] = ""

    scope = _resolve(values["scope"], properties)
    optional = _resolve(values["optional"], properties).lower()
    if scope in SKIPPED_SCOPES or optional == "true":
        return None

    group = _resolve(values["groupId"], properties)
    artifact = _resolve(values["artifactId"], properties)
    version = _resolve(values["version"], properties)

    if not group or not artifact or not version:
        return None
    return f"{group}:{artifact}:{version}"