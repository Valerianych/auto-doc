# Auto Doc

Приложение автоматически форматирует текстовые документы по описанным в методичке правилам. Решение включает:

- библиотеку для загрузки методички и применения форматирующих правил;
- консольный интерфейс на базе `argparse` для форматирования локальных файлов;
- лёгкий HTTP-сервер на стандартной библиотеке, принимающий файлы и возвращающий отформатированный текст.

## Быстрый старт

Проект не требует внешних зависимостей, поэтому достаточно активировать виртуальное окружение (при необходимости) и добавить каталог проекта в `PYTHONPATH`:

```bash
python -m venv .venv
source .venv/bin/activate
export PYTHONPATH=.
```

### Форматирование файла из CLI

```bash
python -m auto_doc format input.txt --output formatted.txt
```

По умолчанию используется методичка `auto_doc/resources/default_methodology.toml`. Для применения пользовательских правил передайте путь к TOML-файлу:

```bash
python -m auto_doc format input.txt --methodology custom_rules.toml
```

### Запуск HTTP-сервера

```bash
python -m auto_doc serve --host 0.0.0.0 --port 8080
```

Загрузите документ через POST `/format` с файлом `file` (тип `multipart/form-data`). Ответом будет отформатированный текст документа.

## Тестирование

```bash
PYTHONPATH=. pytest
```

## Структура методички

Методичка описывается в TOML-формате. Основные секции:

- `title` — правила для заголовка документа (`transform` — верхний регистр, `prefix`/`suffix` — дополнительные строки).
- `sections` — нумерация и формат заголовков разделов (`numbering`, `start_level`, `format`, `case`).
- `paragraphs` — отступы и количество пустых строк между абзацами (`indent`, `spacing`).
- `bullets` — символ маркированных списков (`marker`, `indent`).
- `text` — общие правила очистки (`collapse_whitespace`, `strip_trailing_spaces`).
- `replacements` — список регулярных замен (`pattern`, `replacement`, `flags`).

Пример настроек см. в `auto_doc/resources/default_methodology.toml`.
