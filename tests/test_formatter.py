from pathlib import Path

from auto_doc.formatter import DocumentFormatter
from auto_doc.methodology import load_methodology


def make_formatter() -> DocumentFormatter:
    rules = load_methodology(Path(__file__).resolve().parents[1] / "auto_doc" / "resources" / "default_methodology.toml")
    return DocumentFormatter(rules)


def test_title_and_paragraph_formatting():
    formatter = make_formatter()
    text = "Документ\nПервый абзац без форматирования."
    formatted = formatter.format_text(text)
    lines = formatted.splitlines()
    assert lines[0] == "ДОКУМЕНТ"
    assert lines[1] == ""
    assert lines[2].startswith("    ")


def test_section_numbering():
    formatter = make_formatter()
    text = "# Документ\n## Раздел\nСодержимое\n### Подраздел\nТекст\n## Второй раздел\n"
    formatted = formatter.format_text(text)
    lines = formatted.splitlines()
    assert "## 1. Раздел" in lines
    assert "### 1.1. Подраздел" in lines
    assert "## 2. Второй Раздел" in lines


def test_bullet_and_spacing():
    formatter = make_formatter()
    text = "Документ\n- пункт\n* второй пункт\nФинальный абзац\n"
    formatted = formatter.format_text(text)
    lines = formatted.splitlines()
    assert lines[2].startswith("  - ")
    assert lines[3].startswith("  - ")
    assert lines[-1].startswith("    ")


def test_replacements():
    formatter = make_formatter()
    text = "Документ\nФраза , с пробелами .\n"
    formatted = formatter.format_text(text)
    assert ", с" in formatted
    assert " ." not in formatted
    assert " ," not in formatted
