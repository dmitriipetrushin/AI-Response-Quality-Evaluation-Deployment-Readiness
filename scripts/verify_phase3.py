#!/usr/bin/env python3
"""Check frozen inputs, sealed real evidence, derived reports and final task bindings."""
import hashlib
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.assistant import ROOT, load_config
from src.experiments import validate_dataset, read_experiment, read_reviews, summarize, digest
from scripts.phase3_reports import collect


def main():
    manifest, cases = validate_dataset()
    preflight = json.loads((ROOT/'reports/phase-3-evidence/preflight.json').read_text())
    for filename, expected in preflight['historical_sha256'].items():
        assert hashlib.sha256((ROOT/filename).read_bytes()).hexdigest()==expected, filename
    assert hashlib.sha256((ROOT/'config/assistant-baseline.json').read_bytes()).hexdigest()==preflight['baseline_config_sha256']
    historical=json.loads((ROOT/'data/real-model-responses.json').read_text())['responses']
    reproduced=json.loads((ROOT/'data/phase-3/baseline-reproduction.json').read_text())['responses']
    assert len(historical)==len(reproduced)==30
    assert all(a['test_id']==b['test_id'] and a['response']['answer']==b['response']['answer'] for a,b in zip(historical,reproduced))
    payload=collect()
    assert payload==json.loads((ROOT/'reports/phase-3-metrics.json').read_text()), 'Stale phase-3 metrics'
    selection=payload['selection']; assert selection and selection['dataset_sha256']==digest(manifest)
    assert load_config()==selection['config'], 'App does not use the frozen selected recipe'
    for eid, hashes in selection['validation_evidence'].items():
        for kind,filename in [('responses','responses.jsonl'),('reviews','reviews.csv')]:
            assert hashlib.sha256((ROOT/'experiments/phase-3'/eid/filename).read_bytes()).hexdigest()==hashes[kind]
    prompts=set(); models=set(); response_count=0
    for experiment in payload['experiments']:
        assert (ROOT/'experiments/phase-3'/experiment['experiment_id']/'auxiliary-seal.json').exists()
        meta, rows=read_experiment(experiment['experiment_id'])
        reviews=read_reviews(experiment['experiment_id'],rows)
        assert experiment['complete_review'] and len(reviews)==experiment['successful']
        assert all(r['evaluation_method']=='provisional_agent_assisted_review' for r in reviews)
        assert all(r['response']['response_source']=='ollama_local_inference' for r in rows if r['status']=='success')
        assert all(r['response']['generated_content']==r['response']['raw_response']['message']['content'] for r in rows if r['status']=='success')
        if meta['split']=='validation':
            models.add(meta['config']['model']); assert len(rows)==30
        if meta['split']=='development': prompts.add(meta['config']['prompt_version'])
        response_count+=len(rows)
    assert len(models)>=3 and len(prompts)>=5
    final=payload['final']; control=payload['baseline_heldout']
    assert final and final['total']==100 and final['successful']==100 and final['reviewed']==100
    assert control and control['total']==30 and control['reviewed']==30
    meta, rows=read_experiment(final['experiment_id'])
    assert meta['config']==selection['config'] and set(meta['case_ids'])=={c['test_id'] for c in cases}
    assert meta['timestamp']>=selection['frozen_at'], 'Final inference predates selection'
    assert payload['heldout']['total']==30 and payload['heldout']['reviewed']==30
    tasks=json.loads((ROOT/'label-studio/phase-3-import-tasks.json').read_text())
    assert len(tasks)==100 and len({t['data']['test_id'] for t in tasks})==100
    by_id={r['test_id']:r for r in rows}
    for task in tasks:
        assert not task.get('annotations') and not task.get('predictions')
        data=task['data']; answer=by_id[data['test_id']]['response']['answer']
        assert data['candidate_response']==answer
        assert data['response_sha256']==hashlib.sha256(answer.encode()).hexdigest()
        assert data['experiment_id']==final['experiment_id']
    assert (ROOT/'app/phase3-dashboard.js').read_bytes()==(ROOT/'reports/phase-3-dashboard.js').read_bytes()
    assert 'phase-3-dashboard.html' in (ROOT/'reports/dashboard.html').read_text()
    for name in ['portfolio/phase-3-case-study.md','docs/phase-3-experiments.md','reports/phase-3-completion-report.md']:
        text=(ROOT/name).read_text()
        assert 'provisional' in text.lower() and 'NO-GO' in text, name
    result={'status':'passed','historical_files_preserved':len(preflight['historical_sha256']),
        'baseline_reproduction_identical_answers':30,'dataset_cases':100,'sealed_experiments':len(payload['experiments']),
        'experiment_case_attempts':response_count,'tested_validation_models':sorted(models),
        'tested_prompts':sorted(prompts),'final_responses':100,'heldout_control_responses':30,
        'unannotated_label_studio_tasks':100,'report_consistency':'passed',
        'semantic_review_status':'provisional agent-assisted; no independent human validation'}
    (ROOT/'reports/phase-3-evidence/artifact-verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__': main()
