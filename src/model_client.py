"""Small loopback-only Ollama HTTP client with bounded, explicit failure handling."""
import json
import http.client
import socket
import time
import urllib.error
import urllib.parse
import urllib.request


class ModelError(RuntimeError):
    code = 'model_error'


class ModelConnectionError(ModelError):
    code = 'model_unavailable'


class ModelTimeoutError(ModelError):
    code = 'inference_timeout'


class ModelProtocolError(ModelError):
    code = 'invalid_model_response'


class NoRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ModelConnectionError('The local model service returned an unexpected redirect.')


class ModelClient:
    def __init__(self, service_url, model, options, timeout=180, opener=None):
        parsed = urllib.parse.urlsplit(service_url)
        if (parsed.scheme not in {'http', 'https'} or parsed.hostname not in {'127.0.0.1', 'localhost', '::1'}
                or parsed.username or parsed.password or parsed.query or parsed.fragment
                or parsed.path not in {'', '/'}):
            raise ValueError('Model service_url must be a loopback HTTP(S) origin without credentials.')
        if not isinstance(model, str) or not model.strip():
            raise ValueError('A model identifier is required.')
        if not 1 <= timeout <= 600:
            raise ValueError('Model timeout must be between 1 and 600 seconds.')
        self.service_url = service_url.rstrip('/')
        self.model = model
        self.options = dict(options)
        self.timeout = timeout
        self.opener = opener or urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirects())

    def request(self, endpoint, data=None, timeout=None):
        body = json.dumps(data).encode() if data is not None else None
        request = urllib.request.Request(self.service_url + endpoint, data=body,
                                         headers={'Content-Type': 'application/json', 'Accept': 'application/json'})
        try:
            with self.opener.open(request, timeout=timeout or self.timeout) as response:
                raw = response.read(2_000_001)
            if len(raw) > 2_000_000:
                raise ModelProtocolError('The model response exceeded the response-size limit.')
            result = json.loads(raw)
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                raise ModelConnectionError(f'Model {self.model} or its endpoint is unavailable. Run the model setup command.') from exc
            raise ModelConnectionError(f'The local model service returned HTTP {exc.code}. Check its logs.') from exc
        except (TimeoutError, socket.timeout) as exc:
            raise ModelTimeoutError('Inference timed out. The CPU may be busy; retry after the current request finishes.') from exc
        except urllib.error.URLError as exc:
            if isinstance(exc.reason, (TimeoutError, socket.timeout)):
                raise ModelTimeoutError('The local model service timed out.') from exc
            raise ModelConnectionError('Cannot reach Ollama. Run python3 scripts/start_assistant.py --setup-model.') from exc
        except (OSError, http.client.HTTPException) as exc:
            raise ModelConnectionError('The local model connection was interrupted. Wait for Ollama to start and retry.') from exc
        except (json.JSONDecodeError, UnicodeError) as exc:
            raise ModelProtocolError('Ollama returned invalid JSON.') from exc
        if not isinstance(result, dict):
            raise ModelProtocolError('Ollama must return a JSON object.')
        if result.get('error'):
            raise ModelConnectionError('Ollama could not complete this request; check the model service logs.')
        return result

    def inspect_model(self):
        info = self.request('/api/show', {'model': self.model})
        architecture = info.get('model_info', {}).get('general.architecture')
        supported = info.get('model_info', {}).get(f'{architecture}.context_length')
        configured = self.options.get('num_ctx', 0)
        if not isinstance(supported, int) or not 1 <= configured <= supported:
            raise ModelProtocolError('Configured context exceeds model support, or context metadata is unavailable.')
        tags = self.request('/api/tags', timeout=10).get('models', [])
        tag = next((m for m in tags if m.get('name') == self.model or m.get('model') == self.model), {})
        version = self.request('/api/version', timeout=10).get('version', 'unknown')
        return {'identifier': self.model, 'digest': tag.get('digest'), 'size_bytes': tag.get('size'),
                'details': info.get('details', {}), 'supported_context_length': supported,
                'configured_context_length': configured, 'ollama_version': version,
                'thinking_controls': info.get('thinking'), 'capabilities': info.get('capabilities', [])}

    def chat(self, messages, response_format=None, think=None):
        started = time.perf_counter()
        payload = {'model': self.model, 'messages': messages,
                   'stream': False, 'keep_alive': '15m', 'options': self.options}
        if response_format is not None:
            payload['format'] = response_format
        if think is not None:
            payload['think'] = think
        result = self.request('/api/chat', payload)
        duration = time.perf_counter() - started
        answer = result.get('message', {}).get('content') if isinstance(result.get('message'), dict) else None
        if not isinstance(answer, str) or not answer.strip() or result.get('done') is not True:
            raise ModelProtocolError('Ollama returned an empty or incomplete answer.')
        returned_model = result.get('model')
        if returned_model != self.model:
            raise ModelProtocolError('The response model identifier differs from the requested model.')
        token_fields = ['prompt_eval_count', 'eval_count', 'total_duration', 'load_duration',
                        'prompt_eval_duration', 'eval_duration']
        return {'answer': answer, 'response_time_seconds': round(duration, 6),
                'model': returned_model, 'created_at': result.get('created_at'),
                'done_reason': result.get('done_reason'),
                'token_usage': {k: result.get(k) for k in token_fields}, 'raw_response': result}
