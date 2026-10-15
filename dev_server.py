# Local stand-in for Vercel: serves index.html and routes POST /api/tm_core to api/tm_core.py.
# Usage: python dev_server.py [port]   then open http://127.0.0.1:8000/
import os
import sys
from http.server import ThreadingHTTPServer

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, 'api'))
from tm_core import handler  # noqa: E402


class DevHandler(handler):
    def do_GET(self):
        with open(os.path.join(ROOT, 'index.html'), 'rb') as f:
            body = f.read()
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path.split('?')[0] != '/api/tm_core':
            self._send(404, {'error': 'Not found'})
            return
        super().do_POST()


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    print(f'Serving on http://127.0.0.1:{port}/')
    ThreadingHTTPServer(('127.0.0.1', port), DevHandler).serve_forever()
