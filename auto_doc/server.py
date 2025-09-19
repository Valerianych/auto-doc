"""HTTP-сервер для форматирования документов."""

from __future__ import annotations

import cgi
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Optional
from urllib.parse import parse_qs, urlparse

from .formatter import DocumentFormatter
from .methodology import Methodology, load_methodology


class FormatterRequestHandler(BaseHTTPRequestHandler):
    """Обработчик HTTP-запросов."""

    server_version = "AutoDoc/0.1"
    protocol_version = "HTTP/1.1"
    default_methodology: Optional[Path] = None

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            self._send_json({"status": "ok"})
        else:
            self.send_error(HTTPStatus.NOT_FOUND, "Маршрут не найден")

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path != "/format":
            self.send_error(HTTPStatus.NOT_FOUND, "Маршрут не найден")
            return

        content_type = self.headers.get("Content-Type")
        if not content_type:
            self.send_error(HTTPStatus.BAD_REQUEST, "Отсутствует заголовок Content-Type")
            return
        ctype, _ = cgi.parse_header(content_type)
        if ctype != "multipart/form-data":
            self.send_error(HTTPStatus.BAD_REQUEST, "Используйте multipart/form-data")
            return

        environ = {
            "REQUEST_METHOD": "POST",
            "CONTENT_TYPE": content_type,
            "CONTENT_LENGTH": self.headers.get("Content-Length", "0"),
        }
        form = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ=environ, keep_blank_values=True)
        if "file" not in form:
            self.send_error(HTTPStatus.BAD_REQUEST, "Файл не найден в запросе")
            return

        file_item = form["file"]
        raw_data = file_item.file.read() if getattr(file_item, "file", None) else file_item.value
        if isinstance(raw_data, str):
            raw_bytes = raw_data.encode("utf-8")
        else:
            raw_bytes = raw_data
        try:
            text = raw_bytes.decode("utf-8")
        except UnicodeDecodeError:
            self.send_error(HTTPStatus.BAD_REQUEST, "Файл должен быть в кодировке UTF-8")
            return

        methodology_override = None
        if "methodology" in form:
            methodology_override = form.getvalue("methodology") or None
        elif parsed.query:
            methodology_override = parse_qs(parsed.query).get("methodology", [None])[0]

        try:
            formatter = self._get_formatter(methodology_override)
        except FileNotFoundError as exc:
            self.send_error(HTTPStatus.NOT_FOUND, str(exc))
            return
        except ValueError as exc:
            self.send_error(HTTPStatus.BAD_REQUEST, str(exc))
            return

        formatted = formatter.format_text(text)
        if not formatted:
            self.send_error(HTTPStatus.BAD_REQUEST, "Документ пуст или не содержит текста")
            return
        self._send_text(formatted)

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        """Подавить стандартный вывод логов тестов."""

        return

    def _get_formatter(self, override: Optional[str]) -> DocumentFormatter:
        path = Path(override) if override else self.default_methodology
        rules: Methodology = load_methodology(path)
        return DocumentFormatter(rules)

    def _send_json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_text(self, payload: str, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = payload.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def create_server(host: str = "0.0.0.0", port: int = 8000, methodology: Optional[str] = None) -> ThreadingHTTPServer:
    """Создать HTTP-сервер без запуска."""

    handler = FormatterRequestHandler
    handler.default_methodology = Path(methodology) if methodology else None
    return ThreadingHTTPServer((host, port), handler)


def serve(host: str = "0.0.0.0", port: int = 8000, methodology: Optional[str] = None) -> None:
    """Запустить HTTP-сервер и обрабатывать запросы."""

    server = create_server(host, port, methodology)
    try:
        server.serve_forever()
    except KeyboardInterrupt:  # pragma: no cover - ручная остановка
        pass
    finally:
        server.server_close()


__all__ = ["create_server", "serve", "FormatterRequestHandler"]
