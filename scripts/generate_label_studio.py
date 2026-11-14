#!/usr/bin/env python3
"""Generate unannotated Label Studio tasks, preserving portable case IDs in data."""
import argparse
import json
from pathlib import Path
if __package__:
    from .validate_dataset import ROOT, load_dataset
else:
    from validate_dataset import ROOT, load_dataset


def build_tasks(dataset):
    responses = {r['test_id']: r for r in dataset.responses}
    return [{'id': int(c['test_id'].split('-')[1]), 'data': {
        'test_id': c['test_id'], 'category': c['category'],
        'question': c['employee_question'], 'policy_context': c['policy_context'],
        'policy_references': ';'.join(c['policy_references']),
        'reference_answer': c['reference_answer'],
        'acceptance_criteria': c['acceptance_criteria'],
        'expected_behavior': c['expected_behavior'], 'risk_level': c['risk_level'],
        'candidate_response': responses[c['test_id']]['candidate_response'],
        'response_source': 'synthetic_fixture',
    }} for c in dataset.cases]


def generate_tasks(root=ROOT):
    root = Path(root)
    tasks = build_tasks(load_dataset(root))
    path = root / 'label-studio/import-tasks.json'
    path.write_text(json.dumps(tasks, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return tasks


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args()
    print(f'Generated {len(generate_tasks(args.root))} unannotated synthetic Label Studio tasks.')
