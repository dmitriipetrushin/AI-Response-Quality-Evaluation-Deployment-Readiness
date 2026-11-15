#!/usr/bin/env python3
"""Connect/start the local Ollama service and launch the loopback policy assistant."""
import argparse
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.assistant import ROOT, load_config
from src.model_client import ModelClient, ModelConnectionError, ModelError
from src.server import serve

CONTAINER = 'northstar-ollama'
IMAGE_FILE = ROOT / 'config/ollama-image.txt'


def command(args):
    return subprocess.run(args, check=True)


def ensure_model(config, setup=False):
    client = ModelClient(config['service_url'], config['model'], config['options'], config['timeout_seconds'])
    try:
        client.request('/api/version', timeout=3)
    except ModelError:
        if config['service_url'] != 'http://127.0.0.1:11434':
            raise ModelConnectionError('Start the model service at the configured loopback URL, or use the default for Docker startup.')
        existing = subprocess.run(['docker', 'container', 'inspect', CONTAINER], capture_output=True).returncode == 0
        if existing:
            command(['docker', 'start', CONTAINER])
        elif setup:
            cache = ROOT / '.runtime/ollama'
            cache.mkdir(parents=True, exist_ok=True)
            image = IMAGE_FILE.read_text().strip()
            command(['docker', 'run', '-d', '--name', CONTAINER, '-p', '127.0.0.1:11434:11434',
                     '-v', f'{cache}:/root/.ollama', '-e', 'OLLAMA_NO_CLOUD=1',
                     '-e', 'OLLAMA_NUM_PARALLEL=1', '-e', 'OLLAMA_MAX_LOADED_MODELS=1', image])
        else:
            raise ModelConnectionError('Ollama is not available. Run python3 scripts/start_assistant.py --setup-model.')
        for _ in range(60):
            try:
                client.request('/api/version', timeout=2); break
            except ModelError:
                time.sleep(1)
        else:
            raise ModelConnectionError('Ollama did not become ready within 60 seconds. Inspect the named container logs.')
    tags = client.request('/api/tags', timeout=10).get('models', [])
    if not any(m.get('name') == config['model'] for m in tags):
        if not setup:
            raise ModelConnectionError('Configured model is not installed. Rerun with --setup-model.')
        if config['model'] not in {'qwen2.5:3b', 'qwen2.5:1.5b', 'llama3.2:3b', 'qwen3:4b-instruct-2507-q4_K_M'}:
            raise ValueError('Automatic download is limited to the evaluated small Qwen/Llama models (under approximately 3 GB). Install other models separately.')
        print(f"Downloading {config['model']} into the local Ollama cache (no paid API).", flush=True)
        # HTTP pull works for a native Ollama installation as well as the named container.
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        req = urllib.request.Request(config['service_url'] + '/api/pull',
                                     data=json.dumps({'model': config['model'], 'stream': True}).encode(),
                                     headers={'Content-Type': 'application/json'})
        previous = None
        with opener.open(req, timeout=600) as stream:
            for line in stream:
                message = json.loads(line)
                if message.get('error'):
                    raise ModelConnectionError('Model pull failed: ' + message['error'])
                if message.get('total', 0) > 3_000_000_000:
                    raise ModelConnectionError('Model layer exceeds the automatic-download size limit.')
                status = message.get('status')
                if status != previous:
                    print(status, flush=True); previous = status
        if previous != 'success':
            raise ModelConnectionError('Model download did not report success.')
    metadata = client.inspect_model()
    print(f"Verified {metadata['identifier']} · native context {metadata['supported_context_length']} · configured {metadata['configured_context_length']}", flush=True)
    return metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path)
    parser.add_argument('--setup-model', action='store_true', help='Allow initial Docker setup and one model download below approximately 3 GB.')
    parser.add_argument('--model-only', action='store_true', help='Prepare/check the model service without starting the app.')
    parser.add_argument('--open', action='store_true', help='Open the local app in the default browser.')
    args = parser.parse_args()
    try:
        config = load_config(args.config)
        ensure_model(config, args.setup_model)
        if args.model_only:
            return 0
        if args.open:
            webbrowser.open(f"http://{config['host']}:{config['port']}")
        serve(args.config)
    except (ModelError, ValueError, OSError, subprocess.CalledProcessError) as exc:
        print(f'Startup failed: {exc}', file=sys.stderr); return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
