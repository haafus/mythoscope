import webbrowser
import http.server
import socketserver
import threading

html_dir = '.'
PORT = 8000

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=html_dir, **kwargs)

def start_server():
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Serving at port {PORT}")
        httpd.serve_forever()

def start_home_page():
    webbrowser.open(f'http://localhost:{PORT}/template/home.html')
    threading.Thread(target=start_server).start()
