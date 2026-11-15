"""Explicit real-inference verification of the frozen Phase-3 application recipe."""
import json
import unittest
from src.assistant import ROOT, PolicyAssistant, load_config


class SelectedLiveInferenceTests(unittest.TestCase):
    def test_selected_recipe_generates_real_answers(self):
        selection = json.loads((ROOT/'experiments/phase-3/selection.json').read_text())
        config = load_config()
        self.assertEqual(config, selection['config'])
        assistant = PolicyAssistant(config)
        records = []
        for question in ['How many annual leave days does the handbook provide?',
                         'Does the handbook establish a pet insurance benefit?']:
            response = assistant.answer(question)
            self.assertTrue(response['answer'].strip())
            self.assertEqual(response['model'], config['model'])
            self.assertEqual(response['prompt_version'], config['prompt_version'])
            self.assertTrue(response['raw_response']['done'])
            self.assertGreater(response['token_usage']['eval_count'], 0)
            self.assertEqual(response['generated_content'], response['raw_response']['message']['content'])
            self.assertLess(response['token_usage']['prompt_eval_count'] + config['options']['num_predict'], config['options']['num_ctx'])
            records.append({'question': question, 'response': response})
        (ROOT/'reports/phase-3-evidence/selected-live-inference.json').write_text(
            json.dumps(records, ensure_ascii=False, indent=2)+'\n')


if __name__ == '__main__':
    unittest.main()
