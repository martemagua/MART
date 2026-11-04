"""A real server on a real port, plus the MART.bat commands."""

import http.client
import socket
import threading
from pathlib import Path

import jinja2

from mart import VENDOR_DIR
from mart.__main__ import main
from mart.services import backup_service
from mart.startup import has_fatal, run_checks
from mart.web import server


def _start(port_hint: int = 0):
    httpd = server.bind(port_hint or _free_port())
    port = httpd.server_address[1]
    httpd.RequestHandlerClass = server.make_handler(
        server.create_app(server.allowed_hosts_for(port)))
    t = threading.Thread(target=httpd.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True)
    t.start()
    return httpd, port


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _get(port: int, path: str):
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    conn.request("GET", path)
    resp = conn.getresponse()
    body = resp.read()
    conn.close()
    return resp.status, resp.getheaders(), body


def test_server_serves_pages_static_files_and_health(configured):
    httpd, port = _start()
    try:
        status, _, body = _get(port, "/")
        assert status == 200 and b"MART" in body
        status, headers, _ = _get(port, "/static/mart.css")
        assert status == 200 and ("Content-Type", "text/css; charset=utf-8") in headers
        assert server.running_mart(port)["app"] == "MART"
    finally:
        httpd.shutdown()
        httpd.server_close()


def test_static_files_cannot_escape_their_folder(configured):
    httpd, port = _start()
    try:
        assert _get(port, "/static/../settings.py")[0] == 404
        assert _get(port, "/static/%2e%2e/settings.py")[0] == 404
    finally:
        httpd.shutdown()
        httpd.server_close()


def test_busy_port_moves_to_the_next_one():
    port = _free_port()
    blocker = socket.socket()
    blocker.bind(("127.0.0.1", port))
    blocker.listen()
    try:
        httpd = server.bind(port)
        assert httpd.server_address[1] != port
        httpd.server_close()
    finally:
        blocker.close()


def test_nothing_is_running_on_a_free_port():
    assert server.running_mart(_free_port()) is None


def test_the_shipped_template_library_is_the_one_used():
    assert Path(jinja2.__file__).resolve().is_relative_to(VENDOR_DIR)


def test_start_up_check_passes_here():
    assert not has_fatal(run_checks())


def test_cli_check_and_backup(configured, capsys):
    assert main(["check"]) == 0
    assert main(["backup"]) == 0
    assert "Backup written" in capsys.readouterr().out
    assert len(backup_service.list_backups(Path(configured.backup_dir))) == 1


def test_cli_backup_before_setup_explains(capsys):
    assert main(["backup"]) == 1
    assert "not set up" in capsys.readouterr().out


def test_cli_restore(configured, tmp_path, capsys):
    main(["backup"])
    file = backup_service.list_backups(Path(configured.backup_dir))[0].path
    assert main(["restore", str(file)]) == 0
    assert "Restored" in capsys.readouterr().out
