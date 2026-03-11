import webbrowser
import http.server
import socketserver
import threading
import socket
import time
import os

html_dir = os.path.dirname(os.path.abspath(__file__))
PORT = 8000
_server_running = False


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=html_dir, **kwargs)


def find_free_port(start_port=8000, max_port=9000):
    for port in range(start_port, max_port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("", port))
                return port
            except OSError:
                continue
    raise RuntimeError("Не удалось найти свободный порт")


def start_server(port):
    global _server_running
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", port), Handler) as httpd:
        _server_running = True
        print(f"Serving at port {port}")
        httpd.serve_forever()


def start_home_page():
    global PORT, _server_running

    if _server_running:
        url = f'http://localhost:{PORT}/template/home.html'
        webbrowser.open(url)
        return

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("", PORT))
    except OSError:
        old_port = PORT
        PORT = find_free_port(PORT + 1)
        print(f"Порт {old_port} занят, используем порт {PORT}")

    server_thread = threading.Thread(target=start_server, args=(PORT,), daemon=False)
    server_thread.start()
    time.sleep(0.5)

    url = f'http://localhost:{PORT}/template/home.html'
    print(f"Открываем {url}")
    webbrowser.open(url)