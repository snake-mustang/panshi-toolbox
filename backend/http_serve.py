# -*- coding: utf-8 -*-
"""本地 HTTP 服务：用于提供 frontend/dist，使 QWebChannel 在 http 下稳定工作。"""
import os
import socket
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler


def _find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class _Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, directory=None, **kwargs):
        self.directory = directory or os.getcwd()
        super().__init__(*args, directory=self.directory, **kwargs)

    def log_message(self, format, *args):
        pass  # 静默


_server = None
_port = None


def start_server(dist_dir: str) -> int:
    """在后台线程启动 HTTP 服务，返回端口。"""
    global _server, _port
    _port = _find_free_port()
    def handler(*args):
        return _Handler(*args, directory=dist_dir)

    _server = HTTPServer(("127.0.0.1", _port), handler)
    t = threading.Thread(target=_server.serve_forever, daemon=True)
    t.start()
    return _port


def get_url() -> str:
    """返回当前服务根 URL。"""
    return f"http://127.0.0.1:{_port}/" if _port else ""
