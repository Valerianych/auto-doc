"""CLI для форматирования документов."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional, Sequence

from .formatter import DocumentFormatter
from .methodology import load_methodology
from .server import serve as run_server


def _handle_format(args: argparse.Namespace) -> None:
    input_path = Path(args.input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Файл не найден: {input_path}")

    methodology_path: Optional[Path] = Path(args.methodology) if args.methodology else None
    rules = load_methodology(methodology_path)
    formatter = DocumentFormatter(rules)
    source_text = input_path.read_text(encoding="utf-8")
    formatted = formatter.format_text(source_text)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(formatted, encoding="utf-8")
        print(f"Документ сохранён в {output_path}")
    else:
        sys.stdout.write(formatted)


def _handle_serve(args: argparse.Namespace) -> None:
    run_server(host=args.host, port=args.port, methodology=args.methodology)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Инструменты автоматического форматирования документов")
    subparsers = parser.add_subparsers(dest="command")

    format_parser = subparsers.add_parser("format", help="Отформатировать локальный документ")
    format_parser.add_argument("input_path", help="Путь к исходному файлу")
    format_parser.add_argument("-o", "--output", help="Путь для сохранения результата")
    format_parser.add_argument("-m", "--methodology", help="Путь к TOML/JSON методичке")
    format_parser.set_defaults(func=_handle_format)

    serve_parser = subparsers.add_parser("serve", help="Запустить HTTP-сервер форматирования")
    serve_parser.add_argument("--host", default="0.0.0.0", help="Адрес сервера")
    serve_parser.add_argument("--port", type=int, default=8000, help="Порт сервера")
    serve_parser.add_argument("-m", "--methodology", help="Путь к методичке, применяемой по умолчанию")
    serve_parser.set_defaults(func=_handle_serve)

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 0
    try:
        args.func(args)
        return 0
    except Exception as exc:  # pylint: disable=broad-except
        print(f"Ошибка: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())


__all__ = ["main", "build_parser"]
