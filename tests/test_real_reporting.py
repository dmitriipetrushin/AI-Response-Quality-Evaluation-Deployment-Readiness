"""Report tests use temporary mocked outputs, never the committed actual run."""
import copy
import csv
import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from src.assistant import ROOT, PolicyAssistant
from scripts.evaluate_real_model import run_evaluation
from scripts.generate_report import generate_reports, html_dashboard, calculate_metrics
from scripts.real_model_report import REVIEW_FIELDS, generate_real_reports, load_real_data, real_summary, response_hash
from scripts.validate_dataset import load_dataset


class RealReportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for folder in ['data', 'reports', 'label-studio']:
            (self.root / folder).mkdir()
        for name in ['company-policies.md', 'test-cases.json', 'candidate-responses.json', 'evaluation-results.csv']:
            shutil.copy(ROOT / 'data' / name, self.root / 'data' / name)
        shutil.copy(ROOT / 'label-studio/labeling-config.xml', self.root / 'label-studio/labeling-config.xml')
        self.dataset = load_dataset(self.root)
        self.assistant = PolicyAssistant(root=self.root)
        # Mock lives only inside this temporary unit-test fixture.
        self.assistant._metadata = {'digest': 'unit-test-only'}
        self.assistant.client.chat = Mock(return_value={'answer': 'A mocked unit-test answer.', 'model': 'qwen2.5:3b',
            'response_time_seconds': 0.5, 'created_at': 'unit-test', 'done_reason': 'stop',
            'token_usage': {'prompt_eval_count': 3500, 'eval_count': 10},
            'raw_response': {'message': {'content': 'A mocked unit-test answer.'}, 'done': True}})
        self.run = run_evaluation(self.assistant, self.dataset.cases, self.root / 'data/real-model-responses.json', root=self.root)

    def reviews(self):
        rows = []
        for case, response in zip(self.dataset.cases, self.run['responses']):
            rows.append({'test_id': case['test_id'], 'category': case['category'],
                'response_source': 'ollama_local_inference', 'model': self.run['model'], 'run_id': self.run['run_id'],
                'response_sha256': response_hash(response['response']['answer']), 'classification': 'Correct',
                'critical_failure': 'false', 'policy_references': ';'.join(case['policy_references']),
                'evaluation_rationale': 'Unit-test label only; not a genuine response review.',
                'evaluation_method': 'agent_assisted_review', 'review_status': 'provisional'})
        return rows

    def write_reviews(self, rows):
        with (self.root / 'data/real-model-evaluation.csv').open('w', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=REVIEW_FIELDS, lineterminator='\n')
            writer.writeheader(); writer.writerows(rows)

    def test_unreviewed_results_remain_unknown(self):
        summary = real_summary(self.root)
        self.assertEqual(summary['successful'], 30)
        self.assertIsNone(summary['correct_rate'])
        self.assertIsNone(summary['critical_failures'])
        self.assertEqual(summary['coverage'], 0)
        self.assertEqual(summary['gates']['correct_rate'], 'PENDING')
        self.assertTrue(summary['decision'].startswith('HOLD'))

    def test_provisional_passing_score_cannot_authorize_production(self):
        self.write_reviews(self.reviews())
        summary = real_summary(self.root)
        self.assertEqual(summary['correct_rate'], 100)
        self.assertEqual(summary['coverage'], 100)
        self.assertTrue(all(v == 'PASS' for v in summary['gates'].values()))
        self.assertTrue(summary['decision'].startswith('HOLD'))

    def test_failed_gates_and_critical_count(self):
        rows = self.reviews()
        for row in rows[:4]: row['classification'] = 'Unsupported'
        for row in rows[4:6]: row['classification'] = 'Incorrect'; row['critical_failure'] = 'true'
        self.write_reviews(rows)
        summary = real_summary(self.root)
        self.assertEqual(summary['counts']['Correct'], 24)
        self.assertAlmostEqual(summary['unsupported_rate'], 4 / 30 * 100)
        self.assertEqual(summary['critical_failures'], 2)
        self.assertTrue(summary['decision'].startswith('NO-GO'))

    def test_partial_review_does_not_silently_pass_gates(self):
        self.write_reviews(self.reviews()[:1])
        summary = real_summary(self.root)
        self.assertAlmostEqual(summary['coverage'], 100 / 30)
        self.assertEqual(summary['gates']['unsupported_rate'], 'PENDING')

    def test_provenance_and_answer_hash_required(self):
        rows = self.reviews(); rows[0]['response_sha256'] = 'wrong'
        self.write_reviews(rows)
        with self.assertRaisesRegex(ValueError, 'provenance'): load_real_data(self.root)

    def test_human_review_claim_rejected(self):
        rows = self.reviews(); rows[0]['review_status'] = 'human_verified'
        self.write_reviews(rows)
        with self.assertRaisesRegex(ValueError, 'not human verification'): load_real_data(self.root)

    def test_duplicate_reviews_rejected(self):
        rows = self.reviews(); rows.append(rows[0].copy()); self.write_reviews(rows)
        with self.assertRaisesRegex(ValueError, 'Duplicate'): load_real_data(self.root)

    def test_reporting_and_dashboard_separate_sources(self):
        self.write_reviews(self.reviews())
        hashes = {name: hashlib.sha256((self.root / 'data' / name).read_bytes()).hexdigest() for name in ['candidate-responses.json', 'evaluation-results.csv']}
        summary = generate_real_reports(self.root)
        synthetic = generate_reports(self.root)
        self.assertEqual(synthetic['counts']['Correct'], 17)
        dashboard = (self.root / 'reports/dashboard.html').read_text()
        self.assertIn('Synthetic Evaluation Baseline', dashboard)
        self.assertIn('Real LLM Evaluation', dashboard)
        self.assertIn('not measured model improvement', dashboard)
        self.assertEqual(dashboard.count('<details>'), 30)
        self.assertTrue((self.root / 'reports/real-model-evaluation.md').exists())
        tasks = json.loads((self.root / 'label-studio/real-model-import-tasks.json').read_text())
        self.assertEqual(len(tasks), 30)
        self.assertEqual(tasks[0]['data']['candidate_response'], 'A mocked unit-test answer.')
        self.assertNotIn('annotations', tasks[0])
        self.assertEqual(hashes, {name: hashlib.sha256((self.root / 'data' / name).read_bytes()).hexdigest() for name in hashes})

    def test_altered_raw_answer_is_rejected(self):
        path = self.root / 'data/real-model-responses.json'
        self.run['responses'][0]['response']['answer'] = 'Edited after inference'
        path.write_text(json.dumps(self.run))
        with self.assertRaisesRegex(ValueError, 'raw Ollama output'): load_real_data(self.root)

    def test_unrelated_question_is_rejected(self):
        path = self.root / 'data/real-model-responses.json'
        self.run['responses'][0]['question'] = 'A different question'
        path.write_text(json.dumps(self.run))
        with self.assertRaisesRegex(ValueError, 'original case'): load_real_data(self.root)


if __name__ == '__main__':
    unittest.main()
