"""Explicit live test; excluded from default test_*.py unit-test discovery."""
import json
import unittest
from pathlib import Path
from src.assistant import ROOT, PolicyAssistant, load_config


class LiveInferenceTests(unittest.TestCase):
    def test_two_required_questions_generate_actual_answers(self):
        assistant = PolicyAssistant(load_config(ROOT / 'config/assistant-baseline.json'))
        results = []
        for question in ["What is the company's annual leave policy?", 'Can I share my company password with a colleague?']:
            with self.subTest(question=question):
                response = assistant.answer(question)
                self.assertTrue(response['answer'].strip())
                self.assertEqual(response['raw_response']['message']['content'], response['answer'])
                self.assertTrue(response['raw_response']['done'])
                self.assertGreater(response['token_usage']['eval_count'], 0)
                self.assertLess(response['token_usage']['prompt_eval_count'] + response['generation_options']['num_predict'], response['generation_options']['num_ctx'])
                results.append({'question': question, 'response': response})
        output = ROOT / 'reports/phase-3-evidence/legacy-live-inference-retest.json'
        output.write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    unittest.main()
