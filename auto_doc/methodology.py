"""Загрузка и описание методических правил."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import os
from pathlib import Path
import re
from typing import Any, List, Optional

import tomllib

_FLAG_MAP: dict[str, int] = {
    "IGNORECASE": re.IGNORECASE,
    "MULTILINE": re.MULTILINE,
    "DOTALL": re.DOTALL,
}


@dataclass
class ReplacementRule:
    """Регулярное выражение и подстановка."""

    pattern: str
    replacement: str
    flags: List[str] = field(default_factory=list)

    def compile(self) -> re.Pattern[str]:
        flag_value = 0
        for name in self.flags:
            flag_value |= _FLAG_MAP.get(name.upper(), 0)
        pattern_text = self.pattern.encode("utf-8").decode("unicode_escape")
        return re.compile(pattern_text, flags=flag_value)


@dataclass
class Methodology:
    """Набор правил форматирования."""

    title_transform: str = "upper"
    title_prefix: str = ""
    title_suffix: str = ""
    section_numbering: bool = True
    section_start_level: int = 2
    section_format: str = "{number}. {title}"
    section_case: str = "title"
    paragraph_indent: int = 4
    paragraph_spacing: int = 1
    bullet_marker: str = "-"
    bullet_indent: int = 2
    text_collapse_whitespace: bool = True
    text_strip_trailing_spaces: bool = True
    replacements: List[ReplacementRule] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Methodology":
        title = data.get("title", {}) or {}
        sections = data.get("sections", {}) or {}
        paragraphs = data.get("paragraphs", {}) or {}
        bullets = data.get("bullets", {}) or {}
        text = data.get("text", {}) or {}
        replacements = [
            ReplacementRule(
                pattern=item.get("pattern", ""),
                replacement=item.get("replacement", ""),
                flags=list(item.get("flags", []) or []),
            )
            for item in data.get("replacements", []) or []
        ]

        return cls(
            title_transform=str(title.get("transform", "upper")),
            title_prefix=str(title.get("prefix", "")),
            title_suffix=str(title.get("suffix", "")),
            section_numbering=bool(sections.get("numbering", True)),
            section_start_level=int(sections.get("start_level", 2)),
            section_format=str(sections.get("format", "{number}. {title}")),
            section_case=str(sections.get("case", "title")),
            paragraph_indent=int(paragraphs.get("indent", 4)),
            paragraph_spacing=max(0, int(paragraphs.get("spacing", 1))),
            bullet_marker=str(bullets.get("marker", "-")),
            bullet_indent=int(bullets.get("indent", 2)),
            text_collapse_whitespace=bool(text.get("collapse_whitespace", True)),
            text_strip_trailing_spaces=bool(text.get("strip_trailing_spaces", True)),
            replacements=replacements,
        )

    @classmethod
    def from_path(cls, path: Path) -> "Methodology":
        suffix = path.suffix.lower()
        if suffix in {".toml", ".tml"}:
            with path.open("rb") as fh:
                content = tomllib.load(fh) or {}
        elif suffix == ".json":
            with path.open("r", encoding="utf-8") as fh:
                content = json.load(fh) or {}
        else:
            raise ValueError("Поддерживаются файлы TOML или JSON")
        if not isinstance(content, dict):
            raise ValueError("Методичка должна быть словарём")
        return cls.from_dict(content)


def load_methodology(path: Optional[Path | str] = None) -> Methodology:
    """Загрузить методичку из файла или переменной окружения."""

    resolved: Optional[Path] = None
    env_path = os.getenv("AUTO_DOC_METHOD_PATH")
    if path is not None:
        resolved = Path(path)
    elif env_path:
        resolved = Path(env_path)

    if resolved is None:
        resolved = Path(__file__).resolve().parent / "resources" / "default_methodology.toml"

    if not resolved.exists():
        raise FileNotFoundError(f"Файл методички не найден: {resolved}")

    return Methodology.from_path(resolved)


__all__ = ["Methodology", "ReplacementRule", "load_methodology"]
