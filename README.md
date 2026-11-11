# Maven Dependency Visualizer — вариант №2

Консольная программа на Python для получения и визуализации графа 
зависимостей Java-пакетов из Maven-репозитория. Зависимости извлекаются 
напрямую из POM-файлов через HTTP и XML. Maven и сторонние библиотеки 
не используются.

## Требования
- Python 3.10 или новее.
- Для создания PNG нужен Graphviz (`dot` в PATH).
- Внешние библиотеки Python не требуются.

## Структура
- `src/depviz/` — исходный код.
- `tests/` — автотесты.
- `data/` — тестовые данные.
- `main.py`, `run.sh`, `run.bat` — запуск.

## Этапы
1. **Конфигурация:** `config.py`. Аргументы CLI: `--package`, `--repository`, 
   `--test-mode`, `--test-file`, `--output`, `--ascii-tree`, `--filter`, 
   `--reverse`. Вывод ключ-значение.
2. **Сбор данных:** `maven.py`. Скачивание POM через `urllib`, парсинг XML 
   через `xml.etree`. Вывод прямых зависимостей.
3. **Граф:** `graph.py`. DFS без рекурсии (через стек). Учет фильтра. 
   Тестовый режим (JSON с A-Z).
4. **Обратные зависимости:** `graph.py`. Инверсия графа и поиск 
   зависимых пакетов.
5. **Визуализация:** `visualize.py`. Генерация Graphviz DOT и PNG.

## Запуск
Тестовый режим:
`python main.py --package A --test-mode --test-file data/test_repository.json --ascii-tree`

Реальный режим:
`python main.py --package org.apache.commons:commons-lang3:3.14.0 --output commons.png`

## Сравнение с Maven
Реальный Maven (`mvn dependency:tree`) учитывает BOM, профили и 
наследование родительских POM. Наш инструмент разбирает только прямые 
зависимости из POM конкретного артефакта (без разрешения свойств из 
родительских POM), что является учебным упрощением.

## Тесты
`python -m unittest discover -s tests -v`