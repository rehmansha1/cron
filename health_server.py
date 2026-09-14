"""
Binds to $PORT (or 10000 by default) so cloud Web Service port scanners pass immediately.
"""
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"OK - Career Watchdog is alive\n")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

    def log_message(self, format, *args):
        # Silence access logs to keep console output clean
        return

def start_health_server(port: int = None) -> int:
    """
    Spawns the dummy HTTP health-check server in a background daemon thread.
    Returns the port number bound.
    """
    if port is None:
        port = int(os.environ.get("PORT", 10000))

    try:
        server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True, name="RenderHealthCheckServer")
        thread.start()
        return port
    except Exception as e:
        print(f"[HealthCheck] Warning: could not bind to port {port}: {e}")
        return port
