#!/usr/bin/env python3
"""Verify phase-2 artifacts against actual saved outputs and preserved baseline hashes."""
import hashlib
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.assistant import ROOT, PolicyAssistant
from scripts.real_model_report import load_real_data, real_summary
from scripts.verify_project import verify_project


def verify_phase2(root=ROOT):
    root = Path(root)
    preflight = json.loads((root / 'reports/phase-2-evidence/preflight.json').read_text())
    for name, digest in preflight['original_input_sha256'].items():
        if hashlib.sha256((root / name).read_bytes()).hexdigest() != digest:
            raise ValueError('Original input changed: ' + name)
    dataset, run, reviews = load_real_data(root)
    if run['attempted'] != 30:
        raise ValueError('Not all 30 original questions were attempted.')
    if len(reviews) != run['successful']:
        raise ValueError('Not all successful responses have provisional review.')
    metadata = run.get('model_metadata') or {}
    if not metadata.get('digest') or metadata['supported_context_length'] < run['generation_options']['num_ctx']:
        raise ValueError('Missing model identity or context verification.')
    assistant = PolicyAssistant(root=root)
    for row in run['responses']:
        if row['status'] != 'success': continue
        response = row['response']
        if response['token_usage']['eval_count'] <= 0:
            raise ValueError('No generated tokens recorded.')
        if response['token_usage']['prompt_eval_count'] + run['generation_options']['num_predict'] >= run['generation_options']['num_ctx']:
            raise ValueError('Insufficient observed context headroom.')
        messages = assistant.messages(row['question'])
        expected = hashlib.sha256(json.dumps(messages, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
        if response['prompt_sha256'] != expected:
            raise ValueError('Recorded prompt differs from the shared interactive strategy.')
    if json.loads((root / 'reports/real-model-metrics.json').read_text()) != real_summary(root):
        raise ValueError('Real metrics are stale.')
    tasks = json.loads((root / 'label-studio/real-model-import-tasks.json').read_text())
    expected_answers = {r['test_id']: r['response']['answer'] for r in run['responses'] if r['status'] == 'success'}
    if {t['data']['test_id']: t['data']['candidate_response'] for t in tasks} != expected_answers:
        raise ValueError('Real-model Label Studio tasks differ from raw answers.')
    if any('annotations' in t or 'predictions' in t or t['data']['response_source'] != 'ollama_local_inference' for t in tasks):
        raise ValueError('Real tasks must remain unannotated actual outputs.')
    ET.parse(root / 'label-studio/real-model-labeling-config.xml')
    for filename in ['phase-2-implementation-plan.md', 'phase-2-risk-assessment.md',
                     'phase-2-acceptance-criteria.md', 'phase-2-executive-report.md']:
        if not (root / 'project-management' / filename).is_file(): raise ValueError('Missing phase-2 management document.')
    for filename in ['README.md', 'portfolio/case-study.md']:
        text = (root / filename).read_text()
        if 'Phase 2 — Real AI Model Integration' not in text or run['model'] not in text or 'provisional' not in text:
            raise ValueError('Incomplete phase-2 portfolio narrative: ' + filename)
        current = text.split('# Phase 2 — Real AI Model Integration', 1)[1]
        summary = real_summary(root)
        for value in [f"{summary['correct_rate']:.1f}%", f"{summary['unsupported_rate']:.1f}%",
                      f"{summary['coverage']:.1f}%", f"{summary['average_response_time_seconds']:.2f}"]:
            if value not in current:
                raise ValueError('Stale real-model metric in ' + filename + ': ' + value)
    verify_project(root)
    return {'baseline_inputs_unchanged': True, 'questions_attempted': run['attempted'],
            'actual_answers': run['successful'], 'failed_requests': run['failed'],
            'provisional_reviews': len(reviews), 'model_digest': metadata['digest'],
            'shared_prompt_verified': True, 'label_studio_actual_tasks': len(tasks), 'status': 'passed'}


if __name__ == '__main__':
    try: print(json.dumps(verify_phase2(), indent=2))
    except (ValueError, OSError, KeyError) as exc:
        print(f'Phase-2 verification failed: {exc}', file=sys.stderr); sys.exit(1)
