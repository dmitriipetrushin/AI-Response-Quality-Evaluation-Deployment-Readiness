"""Loopback-only web UI and bounded inference endpoint, using the standard library."""
import json
import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
from .assistant import ROOT, PolicyAssistant, load_config
from .model_client import ModelError


class AssistantServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, config, assistant=None):
        self.assistant = assistant or PolicyAssistant(config)
        self.inference_slot = threading.BoundedSemaphore(1)
        super().__init__((config['host'], config['port']), Handler)


class Handler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def log_message(self, format, *args):
        # Do not log questions, answers, or request bodies.
        pass

    def _origin_ok(self):
        try:
            host = urlsplit('http://' + self.headers.get('Host', '')).hostname
            if host not in {'127.0.0.1', 'localhost', '::1'}:
                return False
            origin = self.headers.get('Origin')
            return origin is None or origin == 'http://' + self.headers['Host']
        except ValueError:
            return False

    def _send(self, status, body, content_type='application/json; charset=utf-8'):
        if not isinstance(body, bytes):
            body = json.dumps(body, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if not self._origin_ok():
            self._send(403, {'error': 'Use the loopback application address.'}); return
        path = urlsplit(self.path).path
        files = {'/': ('app/index.html', 'text/html; charset=utf-8'),
                 '/assets/style.css': ('app/style.css', 'text/css; charset=utf-8'),
                 '/assets/app.js': ('app/app.js', 'text/javascript; charset=utf-8')}
        report_names = ['dashboard.html', 'quality-report.md', 'metrics.json',
                        'real-model-dashboard.html', 'real-model-evaluation.md', 'real-model-metrics.json']
        for name in report_names:
            files['/reports/' + name] = ('reports/' + name, 'text/html; charset=utf-8' if name.endswith('.html') else 'application/json' if name.endswith('.json') else 'text/plain; charset=utf-8')
        if path in files:
            filename, mime = files[path]
            try:
                self._send(200, (ROOT / filename).read_bytes(), mime)
            except FileNotFoundError:
                self._send(404, {'error': 'Report not generated yet. Run the reporting command.'})
        elif path == '/api/health':
            assistant = self.server.assistant
            try:
                tags = assistant.client.request('/api/tags', timeout=3)
                installed = any(m.get('name') == assistant.config['model'] for m in tags.get('models', []))
                self._send(200, {'status': 'ready' if installed else 'model_missing', 'model': assistant.config['model']})
            except ModelError as exc:
                self._send(503, {'status': 'unavailable', 'model': assistant.config['model'], 'error': str(exc)})
        elif path.startswith('/api/policies/'):
            key = path.removeprefix('/api/policies/')
            section = self.server.assistant.policies.sections.get(key)
            self._send(200 if section else 404, section or {'error': 'Unknown policy identifier.'})
        else:
            self._send(404, {'error': 'Not found.'})

    def do_POST(self):
        self.close_connection = True
        if not self._origin_ok():
            self._send(403, {'error': 'Cross-origin inference requests are not permitted.'}); return
        if self.path != '/api/ask':
            self._send(404, {'error': 'Not found.'}); return
        if self.headers.get_content_type() != 'application/json':
            self._send(415, {'error': 'Send application/json.'}); return
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if not 1 <= size <= 16_384:
                self._send(413, {'error': 'Request body must be between 1 and 16,384 bytes.'}); return
            self.connection.settimeout(5)
            raw = self.rfile.read(size)
            payload = json.loads(raw)
            if not isinstance(payload, dict):
                raise ValueError('Send a JSON object containing a question.')
            question = payload.get('question')
            self.server.assistant.messages(question)
        except (ValueError, UnicodeError, socket.timeout):
            self._send(400, {'error': 'Enter a nonempty question within 2,000 characters in valid JSON.'}); return
        if not self.server.inference_slot.acquire(blocking=False):
            self._send(429, {'error': 'The model is answering another question. Wait for it to finish and retry.'}); return
        try:
            result = self.server.assistant.answer(question)
            # Preserve exact raw responses in evaluation artifacts, not in the browser payload.
            self._send(200, {k: v for k, v in result.items() if k != 'raw_response'})
        except ModelError as exc:
            self._send(504 if exc.code == 'inference_timeout' else 503, {'error': str(exc), 'code': exc.code})
        finally:
            self.server.inference_slot.release()


def serve(config_path=None):
    config = load_config(config_path)
    server = AssistantServer(config)
    print(f"Northstar AI Policy Assistant: http://{config['host']}:{config['port']}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    serve()
