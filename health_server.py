"""
Lightweight background HTTP health check server and self-ping keep-alive for cloud hosting (Render, Railway, etc.).
1. Binds to $PORT (or 10000 by default) so Render Web Service port check passes immediately.
2. Runs a 10-minute self-ping loop to prevent Render Free Tier from going to sleep after 14 minutes.
"""
import os
import time
import threading
import urllib.request
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

def _self_ping_worker(interval_seconds: int = 600):
    """
    Periodically sends an HTTP GET request to this service's external public URL.
    Render free tier puts web services to sleep after 14 minutes of inactivity.
    Pinging every 10 minutes resets the inactivity timer and keeps the service alive 24/7.
    """
    # Wait 60s for server to finish booting and DNS to be ready
    time.sleep(60)

    while True:
        url = (
            os.environ.get("RENDER_EXTERNAL_URL")
            or os.environ.get("SELF_PING_URL")
            or os.environ.get("PING_URL")
        )

        if url:
            url = url.strip()
            if not url.startswith("http://") and not url.startswith("https://"):
                url = f"https://{url}"

            try:
                req = urllib.request.Request(
                    url,
                    headers={"User-Agent": "CareerWatchdogKeepAlive/1.0"}
                )
                with urllib.request.urlopen(req, timeout=20) as resp:
                    pass
            except Exception as e:
                # Fail silently; will retry on next interval
                pass

        time.sleep(interval_seconds)

def start_health_server(port: int = None) -> int:
    """
    Spawns the dummy HTTP health-check server and anti-sleep self-ping loop in daemon background threads.
    Returns the port number bound.
    """
    if port is None:
        port = int(os.environ.get("PORT", 10000))

    try:
        server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True, name="RenderHealthCheckServer")
        thread.start()
    except Exception as e:
        print(f"[HealthCheck] Warning: could not bind to port {port}: {e}")
        return port

    # Start self-ping anti-sleep worker (runs every 10 minutes / 600 seconds)
    ping_thread = threading.Thread(target=_self_ping_worker, args=(600,), daemon=True, name="RenderSelfPingKeepAlive")
    ping_thread.start()

    target_url = os.environ.get("RENDER_EXTERNAL_URL") or os.environ.get("SELF_PING_URL")
    if target_url:
        print(f"[Keep-Alive] Self-ping active for {target_url} (every 10m to prevent Render 14m inactivity sleep)")
    else:
        print("[Keep-Alive] Anti-sleep self-pinger active (reads RENDER_EXTERNAL_URL or SELF_PING_URL)")

    return port
