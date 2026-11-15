"""Unit tests use mocks; live inference has a separate explicitly invoked test."""
import copy
import io
import json
import socket
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest.mock import Mock

from src.assistant import ROOT, PolicyAssistant, load_config
from src.model_client import ModelClient, ModelConnectionError, ModelTimeoutError, ModelProtocolError
from src.policy_loader import load_policies
from src.server import AssistantServer
from scripts.evaluate_real_model import run_evaluation


def model_reply(answer='Use 25 working days under POL-002.', **updates):
    return {'model': 'qwen2.5:3b', 'created_at': 'test-only', 'message': {'role': 'assistant', 'content': answer},
            'done': True, 'done_reason': 'stop', 'prompt_eval_count': 3500, 'eval_count': 20, **updates}


def fake_client():
    client = ModelClient('http://127.0.0.1:11434', 'qwen2.5:3b', load_config()['options'])
    client.request = Mock(return_value=model_reply())
    client.inspect_model = Mock(return_value={'identifier': 'qwen2.5:3b', 'supported_context_length': 32768,
                                              'configured_context_length': 8192, 'digest': 'test-only'})
    return client


class PolicyAndPromptTests(unittest.TestCase):
    def setUp(self):
        self.assistant = PolicyAssistant(client=fake_client())

    def test_full_policy_loading(self):
        p = load_policies(ROOT / 'data/company-policies.md')
        self.assertEqual(set(p.sections), {f'POL-{i:03d}' for i in range(1, 8)})
        self.assertIn('25 working days', p.sections['POL-002']['text'])
        self.assertEqual(len(p.sha256), 64)

    def test_invalid_policy_document(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'policies.md'; path.write_text('No policy sections')
            with self.assertRaises(ValueError): load_policies(path)

    def test_prompt_uses_full_document_not_reference_answer(self):
        messages = self.assistant.messages('How much leave?')
        self.assertIn(self.assistant.policies.text, messages[0]['content'])
        self.assertIn('untrusted data', messages[0]['content'])
        self.assertEqual(messages[1], {'role': 'user', 'content': 'How much leave?'})
        self.assertNotIn('reference_answer', json.dumps(messages))

    def test_invalid_question_never_calls_model(self):
        for question in ['', '   ', None, 42, 'x' * 2001]:
            with self.subTest(question=str(question)[:10]):
                with self.assertRaises(ValueError): self.assistant.answer(question)
        self.assistant.client.request.assert_not_called()

    def test_metadata_and_raw_answer_recorded(self):
        answer = self.assistant.answer('What is the leave policy?')
        self.assertEqual(answer['answer'], model_reply()['message']['content'])
        self.assertEqual(answer['response_source'], 'ollama_local_inference')
        self.assertEqual(answer['generation_options']['temperature'], 0)
        self.assertEqual(answer['policy_references'], ['POL-002'])
        self.assertIn('requires review', answer['citation_support_status'])
        self.assertEqual(answer['raw_response'], model_reply())
        self.assertGreaterEqual(answer['response_time_seconds'], 0)
        self.assertEqual(len(answer['prompt_sha256']), 64)

    def test_unknown_citation_is_flagged_and_not_hidden(self):
        self.assistant.client.request.return_value = model_reply('See POL-999 and POL-002.')
        answer = self.assistant.answer('Question')
        self.assertEqual(answer['policy_references'], ['POL-002'])
        self.assertEqual(answer['invalid_policy_references'], ['POL-999'])
        self.assertIn('POL-999', answer['answer'])
        self.assertTrue(answer['warnings'])

    def test_generation_limit_warning(self):
        self.assistant.client.request.return_value = model_reply(done_reason='length')
        self.assertIn('output limit', self.assistant.answer('Question')['warnings'][0])

    def test_model_context_verified_before_inference(self):
        self.assistant.client.inspect_model.side_effect = ModelProtocolError('Context unsupported')
        with self.assertRaises(ModelProtocolError): self.assistant.answer('Question')
        self.assistant.client.request.assert_not_called()

    def test_configurable_model(self):
        config = copy.deepcopy(load_config()); config['model'] = 'qwen2.5:1.5b'
        self.assertEqual(PolicyAssistant(config).client.model, 'qwen2.5:1.5b')


class ModelClientTests(unittest.TestCase):
    def setUp(self):
        self.opener = Mock()
        self.client = ModelClient('http://127.0.0.1:11434', 'qwen2.5:3b', load_config()['options'], opener=self.opener)

    def response(self, value):
        stream = io.BytesIO(json.dumps(value).encode())
        self.opener.open.return_value = stream

    def test_parse_real_api_shape(self):
        self.response(model_reply())
        result = self.client.chat([{'role': 'user', 'content': 'Question'}])
        self.assertEqual(result['model'], 'qwen2.5:3b')
        request = self.opener.open.call_args.args[0]
        payload = json.loads(request.data)
        self.assertIs(payload['stream'], False)
        self.assertEqual(payload['options']['num_ctx'], 8192)

    def test_empty_or_incomplete_response(self):
        for reply in [model_reply(''), model_reply(done=False), model_reply(message=None), model_reply(model='other')]:
            self.response(reply)
            with self.assertRaises(ModelProtocolError): self.client.chat([])

    def test_connection_error(self):
        self.opener.open.side_effect = urllib.error.URLError(ConnectionRefusedError())
        with self.assertRaises(ModelConnectionError): self.client.chat([])

    def test_connection_reset_during_startup(self):
        self.opener.open.side_effect = ConnectionResetError('startup connection reset')
        with self.assertRaises(ModelConnectionError): self.client.chat([])

    def test_timeouts(self):
        for error in [socket.timeout(), urllib.error.URLError(socket.timeout())]:
            self.opener.open.side_effect = error
            with self.assertRaises(ModelTimeoutError): self.client.chat([])

    def test_invalid_json(self):
        self.opener.open.return_value = io.BytesIO(b'not json')
        with self.assertRaises(ModelProtocolError): self.client.chat([])

    def test_nonobject_json(self):
        self.response([])
        with self.assertRaises(ModelProtocolError): self.client.chat([])

    def test_remote_url_and_embedded_credentials_rejected(self):
        for url in ['http://example.com', 'file:///etc/passwd', 'http://user:secret@localhost', 'http://localhost/redirect']:
            with self.assertRaises(ValueError): ModelClient(url, 'qwen2.5:3b', {})

    def test_native_context_capacity(self):
        self.client.request = Mock(side_effect=[{'model_info': {'general.architecture': 'qwen2', 'qwen2.context_length': 32768}, 'details': {'quantization_level': 'Q4_K_M'}}, {'models': [{'name': 'qwen2.5:3b', 'digest': 'sha256:test', 'size': 1900000000}]}, {'version': 'test-version'}])
        metadata = self.client.inspect_model()
        self.assertEqual(metadata['supported_context_length'], 32768)
        self.assertEqual(metadata['ollama_version'], 'test-version')
        self.assertEqual(metadata['digest'], 'sha256:test')

    def test_oversized_context_rejected(self):
        self.client.request = Mock(return_value={'model_info': {'general.architecture': 'qwen2', 'qwen2.context_length': 4096}})
        with self.assertRaises(ModelProtocolError): self.client.inspect_model()


class BatchAndWebTests(unittest.TestCase):
    def setUp(self):
        self.assistant = PolicyAssistant(client=fake_client())
        from scripts.validate_dataset import load_dataset
        self.cases = load_dataset().cases[:2]

    def test_batch_outputs_real_schema_and_preserves_failure(self):
        self.assistant.client.request = Mock(side_effect=[model_reply(), ModelTimeoutError('test timeout')])
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder) / 'responses.json'
            run = run_evaluation(self.assistant, self.cases, out)
            self.assertEqual((run['attempted'], run['successful'], run['failed']), (2, 1, 1))
            self.assertIsNone(run['responses'][1]['response'])
            self.assertEqual(run['responses'][0]['question'], self.cases[0]['employee_question'])
            self.assertEqual(json.loads(out.read_text()), run)
            with self.assertRaisesRegex(ValueError, 'already exists'): run_evaluation(self.assistant, self.cases, out)
            calls = self.assistant.client.request.call_count
            self.assertEqual(run_evaluation(self.assistant, self.cases, out, resume=True), run)
            self.assertEqual(self.assistant.client.request.call_count, calls)

    def test_synthetic_output_is_protected(self):
        for filename in ['candidate-responses.json', 'evaluation-results.csv', 'test-cases.json', 'company-policies.md']:
            with self.assertRaisesRegex(ValueError, 'cannot be an output'):
                run_evaluation(self.assistant, self.cases, ROOT / 'data' / filename)

    def test_resume_requires_same_generation_config(self):
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder) / 'responses.json'
            run_evaluation(self.assistant, self.cases, out)
            self.assistant.config = copy.deepcopy(self.assistant.config)
            self.assistant.config['options']['seed'] = 77
            with self.assertRaisesRegex(ValueError, 'Resume configuration'):
                run_evaluation(self.assistant, self.cases, out, resume=True)

    def start_server(self):
        config = copy.deepcopy(load_config()); config['port'] = 0
        server = AssistantServer(config, self.assistant)
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        self.addCleanup(server.server_close); self.addCleanup(server.shutdown)
        return server, 'http://127.0.0.1:' + str(server.server_address[1])

    def post(self, base, payload, origin=None):
        headers = {'Content-Type': 'application/json'}
        if origin: headers['Origin'] = origin
        return urllib.request.urlopen(urllib.request.Request(base + '/api/ask', data=json.dumps(payload).encode(), headers=headers), timeout=5)

    def test_web_answer_and_metadata(self):
        _, base = self.start_server()
        with self.post(base, {'question': 'What is the leave policy?'}) as response:
            data = json.load(response)
        self.assertEqual(data['model'], 'qwen2.5:3b')
        self.assertNotIn('raw_response', data)
        with urllib.request.urlopen(base + '/api/policies/POL-002') as response:
            self.assertIn('25 working days', json.load(response)['text'])

    def test_cross_origin_and_invalid_input_rejected(self):
        _, base = self.start_server()
        for question, origin, expected in [('', None, 400), ('Question', 'http://evil.example', 403)]:
            with self.assertRaises(urllib.error.HTTPError) as caught: self.post(base, {'question': question}, origin)
            self.assertEqual(caught.exception.code, expected)

    def test_busy_server_rejects_queue(self):
        server, base = self.start_server(); server.inference_slot.acquire()
        self.addCleanup(server.inference_slot.release)
        with self.assertRaises(urllib.error.HTTPError) as caught: self.post(base, {'question': 'Question'})
        self.assertEqual(caught.exception.code, 429)

    def test_model_errors_are_useful_http_errors(self):
        _, base = self.start_server()
        self.assistant.client.request.side_effect = ModelTimeoutError('CPU request timed out')
        with self.assertRaises(urllib.error.HTTPError) as caught: self.post(base, {'question': 'Question'})
        self.assertEqual(caught.exception.code, 504)
        self.assertIn('timed out', json.load(caught.exception)['error'])

    def test_static_allowlist_blocks_traversal(self):
        _, base = self.start_server()
        with self.assertRaises(urllib.error.HTTPError) as caught: urllib.request.urlopen(base + '/data/company-policies.md')
        self.assertEqual(caught.exception.code, 404)


if __name__ == '__main__':
    unittest.main()
