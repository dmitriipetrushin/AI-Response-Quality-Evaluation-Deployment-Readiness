#!/usr/bin/env python3
"""Run the unchanged 30 questions through the same assistant used by the local UI."""
import argparse
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.assistant import ROOT, PolicyAssistant, SYSTEM_INSTRUCTIONS, load_config
from scripts.validate_dataset import load_dataset


def fingerprint(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temp.replace(path)


def run_evaluation(assistant, cases, output, root=ROOT, resume=False):
    output = Path(output)
    root = Path(root)
    protected = {root / 'data' / name for name in ['candidate-responses.json', 'test-cases.json', 'evaluation-results.csv', 'company-policies.md']}
    if output.resolve() in {p.resolve() for p in protected}:
        raise ValueError('The original synthetic baseline and policies cannot be an output target.')
    provenance = {'model': assistant.config['model'], 'generation_options': assistant.config['options'],
                  'context_strategy': assistant.config['context_strategy'], 'policy_sha256': assistant.policies.sha256,
                  'test_cases_sha256': fingerprint(root / 'data/test-cases.json'),
                  'system_instructions_sha256': hashlib.sha256(SYSTEM_INSTRUCTIONS.encode()).hexdigest()}
    if output.exists():
        if not resume:
            raise ValueError('Output already exists. Use --resume or a new --output path; existing runs are not overwritten.')
        run = json.loads(output.read_text())
        if any(run.get(k) != v for k, v in provenance.items()):
            raise ValueError('Resume configuration, policy, or questions differ from the saved run.')
        existing = [row['test_id'] for row in run['responses']]
        if len(set(existing)) != len(existing) or set(existing) - {c['test_id'] for c in cases}:
            raise ValueError('Saved run has duplicate or unknown case IDs.')
    else:
        now = datetime.now(timezone.utc).isoformat()
        run = {'schema_version': 1, 'run_id': 'northstar-' + now, 'started_at': now,
               'response_source': 'ollama_local_inference', 'review_status': 'not_reviewed',
               **provenance, 'model_metadata': None, 'responses': []}
    seen = {r['test_id'] for r in run['responses']}
    for case in cases:
        if case['test_id'] in seen:
            continue
        row = {'test_id': case['test_id'], 'category': case['category'],
               'question': case['employee_question'], 'attempted_at': datetime.now(timezone.utc).isoformat()}
        started = time.perf_counter()
        try:
            result = assistant.answer(case['employee_question'])
            row.update(status='success', response=result, error=None)
            run['model_metadata'] = result['model_metadata']
        except Exception as exc:
            # Each failed request is preserved; no generated or cached substitute is used.
            row.update(status='error', response=None, error={'type': type(exc).__name__, 'message': str(exc)})
        row['request_duration_seconds'] = round(time.perf_counter() - started, 6)
        run['responses'].append(row)
        run['attempted'] = len(run['responses'])
        run['successful'] = sum(r['status'] == 'success' for r in run['responses'])
        run['failed'] = run['attempted'] - run['successful']
        run['completed_at'] = datetime.now(timezone.utc).isoformat() if run['attempted'] == len(cases) else None
        save_json(output, run)
        print(f"{row['test_id']} {row['status']} {row['request_duration_seconds']:.2f}s", flush=True)
    return run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path)
    parser.add_argument('--output', type=Path, default=ROOT / 'data/real-model-responses.json')
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    try:
        assistant = PolicyAssistant(load_config(args.config))
        run = run_evaluation(assistant, load_dataset().cases, args.output, resume=args.resume)
    except (ValueError, OSError) as exc:
        print(str(exc), file=sys.stderr); return 1
    print(f"Attempted {run['attempted']}; successful {run['successful']}; failed {run['failed']}")
    return 0 if run['failed'] == 0 and run['attempted'] == 30 else 1


if __name__ == '__main__':
    sys.exit(main())
