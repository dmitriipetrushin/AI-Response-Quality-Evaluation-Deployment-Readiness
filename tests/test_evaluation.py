"""Regression tests for input integrity, release boundaries, and generated evidence."""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from scripts.validate_dataset import (ROOT, CATEGORY_COUNTS, DatasetValidationError,
                                      load_dataset, validate_records)
from scripts.generate_report import (acceptance_gates, calculate_metrics,
                                     generate_reports, html_dashboard)
from scripts.generate_label_studio import build_tasks


class DatasetTests(unittest.TestCase):
    def setUp(self):
        dataset = load_dataset()
        self.cases = copy.deepcopy(dataset.cases)
        self.responses = copy.deepcopy(dataset.responses)
        self.evaluations = copy.deepcopy(dataset.evaluations)
        self.policies = (ROOT / 'data/company-policies.md').read_text()

    def validate(self):
        return validate_records(self.cases, self.responses, self.evaluations, self.policies)

    def test_dataset_completeness(self):
        d = self.validate()
        self.assertEqual((len(d.cases), len(d.responses), len(d.evaluations)), (30, 30, 30))

    def test_unique_ids(self):
        self.cases[1]['test_id'] = self.cases[0]['test_id']
        with self.assertRaisesRegex(DatasetValidationError, 'duplicate test IDs'):
            self.validate()

    def test_duplicate_evaluation_is_rejected(self):
        self.evaluations.append(self.evaluations[0].copy())
        with self.assertRaisesRegex(DatasetValidationError, 'duplicate test IDs'):
            self.validate()

    def test_correct_category_counts(self):
        from collections import Counter
        self.assertEqual(Counter(c['category'] for c in self.cases), CATEGORY_COUNTS)
        self.cases[0]['category'] = 'ambiguous'
        with self.assertRaisesRegex(DatasetValidationError, 'category counts'):
            self.validate()

    def test_wrong_total(self):
        self.cases.pop()
        with self.assertRaisesRegex(DatasetValidationError, 'exactly 30'):
            self.validate()

    def test_invalid_classification(self):
        self.evaluations[0]['classification'] = 'Mostly fine'
        with self.assertRaisesRegex(DatasetValidationError, 'invalid classification'):
            self.validate()

    def test_missing_evaluation(self):
        self.evaluations.pop()
        with self.assertRaisesRegex(DatasetValidationError, 'evaluations: missing'):
            self.validate()

    def test_missing_response(self):
        self.responses.pop()
        with self.assertRaisesRegex(DatasetValidationError, 'responses: missing'):
            self.validate()

    def test_orphan_response(self):
        self.responses.append({**self.responses[0], 'test_id': 'TC-999'})
        with self.assertRaisesRegex(DatasetValidationError, 'orphaned'):
            self.validate()

    def test_required_fields(self):
        del self.cases[0]['reference_answer']
        with self.assertRaisesRegex(DatasetValidationError, 'missing fields'):
            self.validate()

    def test_unknown_policy(self):
        self.cases[0]['policy_references'] = ['POL-999']
        with self.assertRaisesRegex(DatasetValidationError, 'unknown referenced policies'):
            self.validate()

    def test_policy_reference_mismatch(self):
        self.evaluations[0]['policy_references'] = 'POL-002'
        with self.assertRaisesRegex(DatasetValidationError, 'references disagree'):
            self.validate()

    def test_context_is_verbatim(self):
        self.cases[0]['policy_context'] = 'An invented policy quotation.'
        with self.assertRaisesRegex(DatasetValidationError, 'verbatim'):
            self.validate()

    def test_invalid_boolean_values(self):
        for bad in ['yes', '1', '', 1, None, 'False']:
            with self.subTest(bad=bad):
                self.evaluations[0]['critical_failure'] = bad
                with self.assertRaisesRegex(DatasetValidationError, 'must be true or false'):
                    self.validate()

    def test_csv_boolean_false_is_not_truthy(self):
        self.evaluations[0]['critical_failure'] = 'false'
        self.evaluations[5]['critical_failure'] = 'true'
        d = self.validate()
        self.assertIs(d.evaluations[0]['critical_failure'], False)
        self.assertIs(d.evaluations[5]['critical_failure'], True)

    def test_provenance_cannot_claim_real_review(self):
        self.evaluations[0]['evaluation_method'] = 'human_review'
        with self.assertRaisesRegex(DatasetValidationError, 'simulated_review'):
            self.validate()

    def test_real_model_cannot_mix_into_baseline(self):
        self.responses[0]['response_source'] = 'local_model'
        with self.assertRaisesRegex(DatasetValidationError, 'synthetic_fixture'):
            self.validate()

    def test_category_mismatch(self):
        self.evaluations[0]['category'] = 'sensitive'
        with self.assertRaisesRegex(DatasetValidationError, 'category disagrees'):
            self.validate()


class ReportingTests(unittest.TestCase):
    def setUp(self):
        self.dataset = load_dataset()

    def test_metric_calculations(self):
        m = calculate_metrics(self.dataset)
        self.assertEqual(m['counts'], {'Correct': 17, 'Partially correct': 4, 'Incorrect': 5, 'Unsupported': 4})
        self.assertAlmostEqual(m['correct_rate'], 100 * 17 / 30)
        self.assertAlmostEqual(m['unsupported_rate'], 100 * 4 / 30)
        self.assertEqual(m['coverage'], 100)
        self.assertEqual(m['categories']['multi_step']['counts']['Partially correct'], 2)
        self.assertEqual(m['categories']['sensitive']['correct_rate'], 60)

    def test_critical_failure_count(self):
        self.assertEqual(calculate_metrics(self.dataset)['critical_failures'], 4)
        self.assertEqual([r['test_id'] for r in self.dataset.evaluations if r['critical_failure']],
                         ['TC-006', 'TC-013', 'TC-027', 'TC-029'])

    def test_acceptance_boundary(self):
        self.assertTrue(all(g['passed'] for g in acceptance_gates(30, 27, 1, 0, 30).values()))
        self.assertFalse(acceptance_gates(30, 26, 1, 0, 30)['correct_rate']['passed'])
        self.assertFalse(acceptance_gates(30, 27, 2, 0, 30)['unsupported_rate']['passed'])
        self.assertFalse(acceptance_gates(30, 29, 0, 1, 30)['critical_failures']['passed'])
        self.assertFalse(acceptance_gates(30, 27, 1, 0, 29)['coverage']['passed'])
        self.assertFalse(any(g['passed'] for g in acceptance_gates(0, 0, 0, 0, 0).values()))

    def test_failure_decision(self):
        m = calculate_metrics(self.dataset)
        self.assertTrue(m['decision'].startswith('NO-GO'))
        self.assertEqual(sum(g['passed'] for g in m['gates'].values()), 1)

    def test_all_correct_still_requires_independent_validation(self):
        for row in self.dataset.evaluations:
            row['classification'] = 'Correct'; row['critical_failure'] = False
        m = calculate_metrics(self.dataset)
        self.assertIn('independent real-model validation still required', m['decision'])
        self.assertNotIn('fixtures fail', html_dashboard(self.dataset, m))

    def test_report_generation_and_determinism(self):
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder)
            m = generate_reports(output_dir=out)
            md = (out / 'quality-report.md').read_text()
            dashboard = (out / 'dashboard.html').read_text()
            self.assertIn('56.7%', md)
            self.assertIn('13.3%', dashboard)
            self.assertIn('simulated review', dashboard)
            self.assertIn('NO-GO', md)
            self.assertEqual(dashboard.count('<details>'), 30)
            self.assertEqual(json.loads((out / 'metrics.json').read_text()), m)
            before = {p.name: p.read_bytes() for p in out.iterdir()}
            generate_reports(output_dir=out)
            self.assertEqual(before, {p.name: p.read_bytes() for p in out.iterdir()})

    def test_dashboard_escapes_untrusted_text(self):
        self.dataset.responses[0]['candidate_response'] = '<script>alert("unsafe")</script>'
        dashboard = html_dashboard(self.dataset, calculate_metrics(self.dataset))
        self.assertNotIn('<script>', dashboard)
        self.assertIn('&lt;script&gt;', dashboard)

    def test_invalid_input_does_not_publish_reports(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'data').mkdir()
            (root / 'data/test-cases.json').write_text('{bad json')
            with self.assertRaisesRegex(DatasetValidationError, 'Cannot load dataset'):
                generate_reports(root)
            self.assertFalse((root / 'reports').exists())

    def test_cli_fails_cleanly_for_missing_inputs(self):
        with tempfile.TemporaryDirectory() as folder:
            result = subprocess.run([sys.executable, str(ROOT / 'scripts/validate_dataset.py'), '--root', folder], capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn('INVALID', result.stderr)
            self.assertNotIn('Traceback', result.stderr)

    def test_label_studio_tasks_are_unannotated_and_traceable(self):
        tasks = build_tasks(self.dataset)
        self.assertEqual(len(tasks), 30)
        self.assertEqual(len({task['id'] for task in tasks}), 30)
        self.assertEqual({t['data']['test_id'] for t in tasks}, {c['test_id'] for c in self.dataset.cases})
        self.assertTrue(all('annotations' not in t and 'predictions' not in t for t in tasks))


if __name__ == '__main__':
    unittest.main()
