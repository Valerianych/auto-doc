import json
import threading
import time
from http.client import HTTPConnection
from typing import Dict, Tuple
from uuid import uuid4

from auto_doc.server import create_server


def _build_multipart(
    files: Dict[str, Tuple[str, str, str]],
    fields: Dict[str, str] | None = None,
) -> Tuple[str, bytes]:
    boundary = f"----AutoDocBoundary{uuid4().hex}"
    lines: list[str] = []
    for name, value in (fields or {}).items():
        lines.append(f"--{boundary}")
        lines.append(f'Content-Disposition: form-data; name="{name}"')
        lines.append("")
        lines.append(value)
    for name, (filename, content, content_type) in files.items():
        if isinstance(content, bytes):
            content = content.decode("utf-8")
        lines.append(f"--{boundary}")
        lines.append(f'Content-Disposition: form-data; name="{name}"; filename="{filename}"')
        lines.append(f"Content-Type: {content_type}")
        lines.append("")
        lines.append(content)
    lines.append(f"--{boundary}--")
    lines.append("")
    body = "\r\n".join(lines).encode("utf-8")
    return boundary, body


def _start_server():
    server = create_server("127.0.0.1", 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.05)
    return server, thread


def _stop_server(server, thread):
    server.shutdown()
    server.server_close()
    thread.join(timeout=0.2)


def test_healthcheck():
    server, thread = _start_server()
    host, port = server.server_address
    conn = HTTPConnection(host, port)
    try:
        conn.request("GET", "/health")
        response = conn.getresponse()
        data = json.loads(response.read().decode("utf-8"))
        assert response.status == 200
        assert data["status"] == "ok"
    finally:
        conn.close()
        _stop_server(server, thread)


def test_format_endpoint():
    server, thread = _start_server()
    host, port = server.server_address
    boundary, body = _build_multipart({"file": ("doc.txt", "Документ\nРаздел\n", "text/plain")})
    headers = {
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        "Content-Length": str(len(body)),
    }
    conn = HTTPConnection(host, port)
    try:
        conn.request("POST", "/format", body=body, headers=headers)
        response = conn.getresponse()
        text = response.read().decode("utf-8")
        assert response.status == 200
        assert "ДОКУМЕНТ" in text
        assert "Раздел" in text
    finally:
        conn.close()
        _stop_server(server, thread)
