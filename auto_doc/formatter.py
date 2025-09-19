"""Основная логика форматирования документов."""

from __future__ import annotations

import re
from typing import List, Sequence

from .methodology import Methodology


class DocumentFormatter:
    """Применяет правила методички к тексту документа."""

    def __init__(self, methodology: Methodology) -> None:
        self.methodology = methodology
        self._compiled_replacements: Sequence[tuple[re.Pattern[str], str]] = [
            (rule.compile(), rule.replacement) for rule in methodology.replacements
        ]

    def format_text(self, text: str) -> str:
        """Отформатировать строку с текстом документа."""

        if not text:
            return ""

        normalized = text.replace("\r\n", "\n").replace("\r", "\n")
        lines = [line.rstrip() for line in normalized.split("\n")]

        lines = self._apply_title(lines)
        lines = self._format_headings(lines)
        lines = self._format_bullets(lines)
        lines = self._indent_paragraphs(lines)
        lines = self._apply_spacing(lines)

        result = "\n".join(lines)
        result = self._cleanup_text(result)
        cleaned = result.strip()
        return cleaned + "\n" if cleaned else ""

    def format_file(self, path: str, output_path: str | None = None) -> str:
        """Загрузить файл, отформатировать и сохранить результат."""

        with open(path, "r", encoding="utf-8") as fh:
            source = fh.read()
        formatted = self.format_text(source)
        target_path = output_path or path
        with open(target_path, "w", encoding="utf-8") as fh:
            fh.write(formatted)
        return formatted

    # --- внутренние этапы форматирования ---

    def _apply_title(self, lines: List[str]) -> List[str]:
        result = list(lines)
        for idx, line in enumerate(result):
            stripped = line.strip()
            if not stripped:
                continue
            formatted = self._format_title_line(stripped)
            result[idx] = formatted
            if idx + 1 < len(result):
                if result[idx + 1].strip():
                    result.insert(idx + 1, "")
            else:
                result.append("")
            break
        return result

    def _format_title_line(self, line: str) -> str:
        prefix = self.methodology.title_prefix or ""
        suffix = self.methodology.title_suffix or ""
        if line.startswith("#"):
            match = re.match(r"^(#+)\s*(.+)$", line)
            if match:
                hashes, text = match.groups()
                text = self._transform_case(text.strip(), self.methodology.title_transform)
                return f"{hashes} {prefix}{text}{suffix}".rstrip()
        text = self._transform_case(line.strip(), self.methodology.title_transform)
        return f"{prefix}{text}{suffix}".strip()

    def _format_headings(self, lines: List[str]) -> List[str]:
        result: List[str] = []
        counters: List[int] = []
        heading_pattern = re.compile(r"^(\s*)(#+)\s*(.+)$")

        for line in lines:
            match = heading_pattern.match(line)
            if match:
                indent, hashes, title = match.groups()
                if result and result[-1].strip():
                    result.append("")
                clean_title = self._strip_existing_numbering(title.strip())
                clean_title = self._transform_case(clean_title, self.methodology.section_case)
                number = ""
                if self.methodology.section_numbering:
                    number = self._next_section_number(counters, len(hashes))
                else:
                    counters.clear()
                if number:
                    body = self.methodology.section_format.format(number=number, title=clean_title)
                else:
                    body = clean_title
                formatted = f"{indent}{hashes} {body}".rstrip()
                result.append(formatted)
                result.append("")
            else:
                result.append(line)
        return result

    def _format_bullets(self, lines: List[str]) -> List[str]:
        bullet_pattern = re.compile(r"^(\s*)[\-*+•]\s+(.+)$")
        result: List[str] = []
        for line in lines:
            match = bullet_pattern.match(line)
            if match:
                indent, body = match.groups()
                indent_to_use = indent if indent else " " * self.methodology.bullet_indent
                result.append(f"{indent_to_use}{self.methodology.bullet_marker} {body.strip()}")
            else:
                result.append(line)
        return result

    def _indent_paragraphs(self, lines: List[str]) -> List[str]:
        indent = " " * self.methodology.paragraph_indent
        result: List[str] = []
        for line in lines:
            stripped = line.strip()
            if not stripped:
                result.append("")
                continue
            lstripped = line.lstrip()
            if self._is_structural_line(lstripped):
                result.append(line)
                continue
            if line.startswith(" "):
                result.append(line)
                continue
            result.append(f"{indent}{stripped}")
        return result

    def _apply_spacing(self, lines: List[str]) -> List[str]:
        result: List[str] = []
        blank_count = 0
        max_blank = self.methodology.paragraph_spacing
        for line in lines:
            if line.strip():
                if blank_count:
                    allowed = max_blank if max_blank > 0 else 0
                    result.extend([""] * min(blank_count, allowed))
                    blank_count = 0
                result.append(line.rstrip())
            else:
                blank_count += 1
        while result and not result[-1].strip():
            result.pop()
        return result

    def _cleanup_text(self, text: str) -> str:
        cleaned = text
        if self.methodology.text_strip_trailing_spaces:
            cleaned = "\n".join(line.rstrip() for line in cleaned.splitlines())
        if self.methodology.text_collapse_whitespace:
            collapsed_lines = []
            for line in cleaned.splitlines():
                if not line.strip():
                    collapsed_lines.append("")
                    continue
                indent = len(line) - len(line.lstrip(" "))
                body = re.sub(r"[ \t]{2,}", " ", line.lstrip(" "))
                collapsed_lines.append(" " * indent + body)
            cleaned = "\n".join(collapsed_lines)
        cleaned = re.sub(r"\s+,", ",", cleaned)
        cleaned = re.sub(r",\s+", ", ", cleaned)
        cleaned = re.sub(r"\s+\.", ".", cleaned)
        for pattern, replacement in self._compiled_replacements:
            cleaned = pattern.sub(replacement, cleaned)
        return cleaned

    def _transform_case(self, text: str, mode: str) -> str:
        mode_lower = (mode or "").lower()
        if mode_lower == "upper":
            return text.upper()
        if mode_lower == "lower":
            return text.lower()
        if mode_lower == "title":
            return text.title()
        if mode_lower == "capitalize":
            return text.capitalize()
        if mode_lower == "sentence":
            return text[:1].upper() + text[1:]
        return text

    def _strip_existing_numbering(self, text: str) -> str:
        pattern = re.compile(r"^\d+(?:\.\d+)*(?:[\.)-])?\s+")
        return pattern.sub("", text, count=1).strip()

    def _next_section_number(self, counters: List[int], level: int) -> str:
        relative = level - self.methodology.section_start_level
        if relative < 0:
            counters.clear()
            return ""
        while len(counters) <= relative:
            counters.append(0)
        counters[relative] += 1
        for idx in range(relative + 1, len(counters)):
            counters[idx] = 0
        numbers = [str(num) for num in counters[: relative + 1] if num]
        return ".".join(numbers)

    def _is_structural_line(self, line: str) -> bool:
        if not line:
            return True
        if line.startswith("#"):
            return True
        if line.startswith((">", "`")):
            return True
        if re.match(r"^[-*+]\s", line):
            return True
        if re.match(r"^\d+[\.)]\s", line):
            return True
        return False


__all__ = ["DocumentFormatter"]
