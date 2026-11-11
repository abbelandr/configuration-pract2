"""Получение прямых зависимостей из POM без Maven и внешних библиотек."""

import re
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
import ssl

TIMEOUT_SECONDS = 15
MAX_RESOLVE_DEPTH = 5
SKIPPED_SCOPES = {"test", "provided", "system", "import"}
PROPERTY_PATTERN = re.compile(r"\$\{([^}]+)\}")


def parse_coordinates(coordinates):
    """Разделить Maven-координаты groupId:artifactId:version."""
    parts = coordinates.split(":")
    if len(parts) != 3 or not all(parts):
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


def fetch_pom(coordinates, repository):
    """Загрузить POM по HTTP и вернуть его XML-дерево."""
    address = pom_url(coordinates, repository)
    request = urllib.request.Request(
        address, headers={"User-Agent": "DependencyVisualizer/1.0"}
    )

    # Создаем контекст, который игнорирует проверку SSL
    context = ssl._create_unverified_context()

    try:
        with urllib.request.urlopen(
                request, timeout=TIMEOUT_SECONDS, context=context  # <--- Передаем context
        ) as response:
            content = response.read()
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        msg = f"Не удалось загрузить POM {address}: {error}"
        raise RuntimeError(msg) from error

    try:
        return ET.fromstring(content)
    except ET.ParseError as error:
        msg = f"Некорректный XML в POM {address}: {error}"
        raise RuntimeError(msg) from error


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
        values[name] = (node.text or "").strip() if node is not None else ""
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