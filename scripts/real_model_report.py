"""Validate actual inference provenance and provisional reviews; no semantic auto-labeling."""
import csv
import hashlib
import html
import json
from collections import Counter
from pathlib import Path
from scripts.validate_dataset import CLASSIFICATIONS, load_dataset
from scripts.generate_label_studio import build_tasks

REVIEW_FIELDS = ['test_id', 'category', 'response_source', 'model', 'run_id', 'response_sha256',
                 'classification', 'critical_failure', 'policy_references', 'evaluation_rationale',
                 'evaluation_method', 'review_status']


def response_hash(answer):
    return hashlib.sha256(answer.encode('utf-8')).hexdigest()


def load_real_data(root):
    root = Path(root)
    dataset = load_dataset(root)
    cases = {c['test_id']: c for c in dataset.cases}
    run = json.loads((root / 'data/real-model-responses.json').read_text())
    if run.get('response_source') != 'ollama_local_inference':
        raise ValueError('Real-run source must be ollama_local_inference.')
    if run.get('policy_sha256') != hashlib.sha256((root / 'data/company-policies.md').read_bytes()).hexdigest():
        raise ValueError('Real run used a different policy document.')
    if run.get('test_cases_sha256') != hashlib.sha256((root / 'data/test-cases.json').read_bytes()).hexdigest():
        raise ValueError('Real run used different questions.')
    rows = run.get('responses', [])
    if not isinstance(rows, list) or any(not isinstance(r, dict) for r in rows):
        raise ValueError('Real responses must be a list of objects.')
    if len({r['test_id'] for r in rows}) != len(rows):
        raise ValueError('Duplicate real-response IDs.')
    for row in rows:
        case = cases.get(row['test_id'])
        if not case or row['question'] != case['employee_question'] or row['category'] != case['category']:
            raise ValueError('Real response does not match an original case and question.')
        if row['status'] not in {'success', 'error'}:
            raise ValueError('Invalid inference status.')
        if not isinstance(row.get('request_duration_seconds'), (float, int)) or row['request_duration_seconds'] < 0:
            raise ValueError('Missing or invalid inference duration.')
        result = row.get('response')
        if row['status'] == 'success':
            if not isinstance(result, dict) or not isinstance(result.get('answer'), str) or not result['answer'].strip():
                raise ValueError('Successful inference must contain an actual nonempty answer.')
            if (result.get('response_source') != run['response_source'] or result.get('model') != run['model']
                    or result.get('policy_sha256') != run['policy_sha256']
                    or result.get('generation_options') != run['generation_options']
                    or result.get('context_strategy') != run['context_strategy']):
                raise ValueError('Real response provenance differs from the run.')
            if result.get('raw_response', {}).get('message', {}).get('content') != result['answer']:
                raise ValueError('Saved answer differs from the raw Ollama output.')
            if result.get('model_metadata', {}).get('digest') != (run.get('model_metadata') or {}).get('digest'):
                raise ValueError('Model digest changed within the run.')
        elif result is not None or not row.get('error'):
            raise ValueError('Failed requests must preserve an error without a substitute response.')
    if (run.get('attempted') != len(rows) or run.get('successful') != sum(r['status'] == 'success' for r in rows)
            or run.get('failed') != sum(r['status'] == 'error' for r in rows)):
        raise ValueError('Run request counters disagree with saved records.')
    responses = {r['test_id']: r for r in rows}
    review_path = root / 'data/real-model-evaluation.csv'
    reviews = []
    if review_path.exists():
        with review_path.open(newline='', encoding='utf-8') as stream:
            reader = csv.DictReader(stream)
            if not set(REVIEW_FIELDS).issubset(reader.fieldnames or []):
                raise ValueError('Real-review CSV is missing required fields.')
            for review in reader:
                row = responses.get(review['test_id'])
                if not row or row['status'] != 'success':
                    raise ValueError('A review must refer to a successful actual response.')
                if review['classification'] not in CLASSIFICATIONS:
                    raise ValueError('Invalid real-response classification.')
                if review['critical_failure'] not in {'true', 'false'}:
                    raise ValueError('Critical failure must be a CSV boolean.')
                if review['classification'] == 'Correct' and review['critical_failure'] == 'true':
                    raise ValueError('A Correct response cannot be a critical failure.')
                if review['evaluation_method'] != 'agent_assisted_review' or review['review_status'] != 'provisional':
                    raise ValueError('This review is provisional agent assistance, not human verification.')
                if (review['model'] != run['model'] or review['run_id'] != run['run_id']
                        or review['response_sha256'] != response_hash(row['response']['answer'])
                        or review['response_source'] != run['response_source']
                        or review['category'] != row['category']):
                    raise ValueError('Review provenance does not match the saved response.')
                if not review['evaluation_rationale'].strip():
                    raise ValueError('Every provisional label requires a rationale.')
                refs = review['policy_references'].split(';') if review['policy_references'] else []
                if set(refs) - set(cases[review['test_id']]['policy_references']):
                    raise ValueError('Review policy references must be grounded in the case evidence.')
                reviews.append({**review, 'critical_failure': review['critical_failure'] == 'true'})
        if len({r['test_id'] for r in reviews}) != len(reviews):
            raise ValueError('Duplicate real-review IDs.')
    return dataset, run, reviews


def real_summary(root):
    root = Path(root)
    if not (root / 'data/real-model-responses.json').exists():
        return None
    dataset, run, reviews = load_real_data(root)
    total = len(dataset.cases)
    successful = run['successful']; attempted = run['attempted']
    counts = {label: sum(r['classification'] == label for r in reviews) for label in CLASSIFICATIONS}
    critical = sum(r['critical_failure'] for r in reviews)
    complete = len(reviews) == total and successful == total
    conditions = {'correct_rate': counts['Correct'] * 100 >= 90 * total,
                  'unsupported_rate': counts['Unsupported'] * 100 <= 5 * total,
                  'critical_failures': critical == 0,
                  'coverage': len(reviews) == total}
    gates = {key: ('PASS' if passed else 'FAIL') if complete else 'PENDING' for key, passed in conditions.items()}
    if not complete:
        gates['coverage'] = 'FAIL'
    times = [r['request_duration_seconds'] for r in run['responses'] if r['status'] == 'success']
    metadata = run.get('model_metadata') or {}
    return {'run_id': run['run_id'], 'model': run['model'], 'model_metadata': metadata,
            'generation_options': run['generation_options'], 'context_strategy': run['context_strategy'],
            'policy_sha256': run['policy_sha256'], 'total': total, 'attempted': attempted,
            'successful': successful, 'failed': run['failed'], 'unattempted': total - attempted,
            'average_response_time_seconds': sum(times) / len(times) if times else None,
            'maximum_response_time_seconds': max(times) if times else None,
            'reviewed': len(reviews), 'counts': counts,
            'correct_rate': counts['Correct'] * 100 / total if reviews else None,
            'unsupported_rate': counts['Unsupported'] * 100 / total if reviews else None,
            'critical_failures': critical if reviews else None, 'coverage': len(reviews) * 100 / total,
            'inference_coverage': successful * 100 / total, 'gates': gates,
            'review_status': 'provisional_agent_assisted; independent human verification not performed',
            'citation_checks': {
                'answers_with_recognized_ids': sum(bool(r['response']['policy_references']) for r in run['responses'] if r['status'] == 'success'),
                'answers_with_unknown_ids': sum(bool(r['response']['invalid_policy_references']) for r in run['responses'] if r['status'] == 'success'),
                'unknown_ids_by_case': {r['test_id']: r['response']['invalid_policy_references'] for r in run['responses'] if r['status'] == 'success' and r['response']['invalid_policy_references']},
                'claim_support': 'Not established by identifier validation.'},
            'output_limit_stops': sum(r['response'].get('done_reason') == 'length' for r in run['responses'] if r['status'] == 'success'),
            'decision': 'NO-GO — provisional acceptance gates failed' if complete and not all(conditions.values())
                        else 'HOLD — independent human review and broader validation required',
            'input_sha256': {name: hashlib.sha256((root / name).read_bytes()).hexdigest()
                             for name in ['data/real-model-responses.json', 'data/real-model-evaluation.csv'] if (root / name).exists()},
            'prompt_token_counts': sorted({r['response']['token_usage'].get('prompt_eval_count') for r in run['responses'] if r['status'] == 'success' and isinstance(r['response']['token_usage'].get('prompt_eval_count'), int)})}


def dashboard_section(summary):
    if summary is None:
        return ''
    e = html.escape
    fmt = lambda value: 'Not reviewed' if value is None else f'{value:.1f}%'
    latency = summary['average_response_time_seconds']
    actuals = {'correct_rate': fmt(summary['correct_rate']), 'unsupported_rate': fmt(summary['unsupported_rate']),
               'critical_failures': str(summary['critical_failures']) if summary['critical_failures'] is not None else 'Unknown',
               'coverage': f"{summary['coverage']:.1f}%"}
    targets = {'correct_rate': '≥90%', 'unsupported_rate': '≤5%', 'critical_failures': 'Zero', 'coverage': '100%'}
    gate_rows = ''.join(f'<tr><th scope="row">{e(key.replace("_", " ").title())}</th><td>{actuals[key]}</td><td>{targets[key]}</td><td class="{"pass" if result == "PASS" else "fail"}"><b>{result}</b></td></tr>' for key, result in summary['gates'].items())
    return f'''<section id="real-llm-evaluation"><h2>Real LLM Evaluation</h2>
<p><b>Actual model-generated answers · {e(summary['model'])} · provisional agent-assisted review</b></p>
<p>Requests: {summary['attempted']} attempted, {summary['successful']} successful, {summary['failed']} failed.
Correct: {fmt(summary['correct_rate'])}; Unsupported: {fmt(summary['unsupported_rate'])}; critical failures: {summary['critical_failures'] if summary['critical_failures'] is not None else 'unknown'};
review coverage: {summary['coverage']:.1f}%. Mean response time: {f'{latency:.2f} s' if latency is not None else 'unavailable'}.</p>
<p><b>{e(summary['decision'])}</b></p><p>The synthetic baseline was deliberately authored and is not a performance benchmark. Differences between these datasets are not measured model improvement. Real-answer labels are provisional, without independent human validation.</p>
<div class="table-scroll"><table><caption>Original gates applied to provisional real-output reviews</caption><thead><tr><th scope="col">Metric</th><th scope="col">Actual</th><th scope="col">Target</th><th scope="col">Provisional result</th></tr></thead><tbody>{gate_rows}</tbody></table></div>
<p><a href="real-model-dashboard.html">Open real-run evidence</a> · <a href="http://127.0.0.1:8000/">Open interactive AI assistant</a> (start the local app first; default port shown)</p></section>'''


def generate_real_reports(root):
    root = Path(root)
    dataset, run, reviews = load_real_data(root)
    summary = real_summary(root)
    by_review = {r['test_id']: r for r in reviews}
    by_case = {c['test_id']: c for c in dataset.cases}
    fmt = lambda value: 'Not assessed' if value is None else f'{value:.1f}%'
    mean = summary['average_response_time_seconds']
    lines = ['# Real LLM Evaluation', '', '**Actual Ollama inference · provisional agent-assisted review · no independent human validation**', '',
             f"Model: **{run['model']}**. Run: `{run['run_id']}`.", '',
             f"**Recommendation: {summary['decision']}.** No business pilot or production rollout occurred.", '',
             '## Configuration and provenance', '',
             f"- Model metadata: `{json.dumps(summary['model_metadata'], sort_keys=True)}`.",
             f"- Generation settings: `{json.dumps(run['generation_options'], sort_keys=True)}`.",
             f"- Context strategy: `{run['context_strategy']}`; the complete fictional handbook is included in every prompt. This is full-context prompting, not RAG.",
             f"- Policy SHA-256: `{run['policy_sha256']}`. Input hashes are recorded in `real-model-metrics.json`.",
             f"- Observed prompt token counts: {', '.join(map(str,summary['prompt_token_counts'])) or 'unreported'}. The model's native context support is verified through `/api/show` before inference.", '',
             'The UI and evaluation call the same PolicyAssistant implementation. Questions match the original 30 cases exactly; reference answers and labels are not sent to the model. Raw Ollama output is preserved alongside the exact returned answer, timings, model digest, options, prompt hash, and errors. Sampling is fixed where supported; identical outputs are not guaranteed across runtime or hardware changes.', '',
             f"Identifier checks: {summary['citation_checks']['answers_with_recognized_ids']} successful answers include a recognized policy ID; {summary['citation_checks']['answers_with_unknown_ids']} include an unknown ID. Unknown IDs by case: `{json.dumps(summary['citation_checks']['unknown_ids_by_case'])}`. A recognized ID does not establish claim support. Output-limit stops observed: {summary['output_limit_stops']}.", '',
             '## Run and provisional results', '', '| Metric | Actual |', '|---|---:|',
             f"| Attempted / expected | {summary['attempted']} / {summary['total']} |",
             f"| Successful responses | {summary['successful']} |", f"| Failed requests | {summary['failed']} |",
             f"| Unattempted | {summary['unattempted']} |",
             f"| Mean successful request time | {f'{mean:.2f} s' if mean is not None else 'Unavailable'} |",
             f"| Correct / all 30 cases | {fmt(summary['correct_rate'])} |",
             f"| Unsupported / all 30 cases | {fmt(summary['unsupported_rate'])} |",
             f"| Critical failures observed | {summary['critical_failures'] if summary['critical_failures'] is not None else 'Unknown'} |",
             f"| Review coverage | {summary['coverage']:.1f}% |", '',
             '| Classification | Provisional count |', '|---|---:|']
    lines += [f'| {label} | {count} |' for label, count in summary['counts'].items()]
    lines += ['', '## Original proposed acceptance gates', '', '| Metric | Target | Provisional result |', '|---|---|---|']
    targets = {'correct_rate': 'At least 90% (27/30)', 'unsupported_rate': 'At most 5% (1/30)', 'critical_failures': 'Zero', 'coverage': '100% (30/30)'}
    lines += [f'| {key} | {targets[key]} | {result} |' for key, result in summary['gates'].items()]
    lines += ['', 'If review is incomplete, classification rates describe only observed labels divided by all cases; unreviewed outcomes remain unknown and the corresponding gates stay pending. Request failures are never substituted with synthetic answers. Timings are client wall-clock times for successful batch requests, include queue/load time, and are not a concurrent-load benchmark.', '',
              '## Provisional review audit', '', '| Case | Classification | Critical | Rationale / error |', '|---|---|---|---|']
    e = html.escape
    cards = ''
    for row in run['responses']:
        review = by_review.get(row['test_id'])
        label = review['classification'] if review else 'Not reviewed'
        critical = ('Yes' if review['critical_failure'] else 'No') if review else 'Unknown'
        rationale = review['evaluation_rationale'] if review else json.dumps(row['error']) if row['status'] == 'error' else 'Awaiting review.'
        lines.append(f"| {row['test_id']} | {label} | {critical} | {rationale.replace('|', '/')} |")
        answer = row['response']['answer'] if row['response'] else 'INFERENCE ERROR: ' + str(row['error'])
        case = by_case[row['test_id']]
        cards += f'<details><summary>{e(row["test_id"])} · {e(label)} · critical: {critical}</summary><dl>'
        for key, value in [('Question', row['question']), ('Actual model answer', answer), ('Reference answer', case['reference_answer']), ('Acceptance criteria', case['acceptance_criteria']), ('Policy context', case['policy_context']), ('Provisional rationale', rationale)]:
            cards += f'<dt>{e(key)}</dt><dd>{e(value)}</dd>'
        cards += '</dl></details>'
    lines += ['', '## Evaluation integrity, risks, and decision', '',
              'The response source is `ollama_local_inference`. Every classification is an authored `agent_assisted_review` with status `provisional`, tied to its exact answer hash and run ID. These labels are not automated semantic ground truth and are not human-verified. Existing identifiers are checked mechanically; citation support and answer quality require substantive review. No fake annotations are generated.', '',
              'The original synthetic results are preserved separately. They were deliberately constructed to demonstrate failures; score differences do not measure model improvement. Thirty selected questions are too few to establish real employee-traffic accuracy, rare-event safety, or business outcomes. Independent review, expanded holdout coverage, adversarial security testing, latency targets, and named business approvals are prerequisites for a controlled pilot. Even passing provisional gates cannot authorize production.', '',
              'The real-model Label Studio task file is prepared separately; its actual import status is recorded in the phase-2 executive report. No independent human annotations or export round trip are claimed.']
    (root / 'reports/real-model-evaluation.md').write_text('\n'.join(lines) + '\n')
    (root / 'reports/real-model-metrics.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
    html_doc = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Real LLM Evaluation — Northstar</title><style>body{{margin:0;background:#f2f5f7;color:#152a3a;font:16px/1.65 system-ui,sans-serif}}main{{max-width:1100px;margin:auto;padding:35px 24px}}section,details{{background:white;border:1px solid #d3dde4;padding:20px;border-radius:8px;margin:16px 0}}h1{{line-height:1.2}}a,summary{{color:#12646b}}summary{{cursor:pointer;font-weight:650;overflow-wrap:anywhere}}.table-scroll{{overflow-x:auto}}p{{overflow-wrap:anywhere}}dt{{font-weight:700;margin-top:14px}}dd{{margin:4px 0;white-space:pre-wrap;overflow-wrap:anywhere}}.notice{{background:#fff6df;border:1px solid #d4ad4d;padding:16px}}nav{{margin-bottom:30px}}a:focus-visible,summary:focus-visible{{outline:3px solid #be8100;outline-offset:3px}}table{{border-collapse:collapse;width:100%}}th,td{{text-align:left;padding:10px;border-bottom:1px solid #d3dde4}}</style></head><body><main><nav><a href="dashboard.html">Combined dashboard</a> · <a href="http://127.0.0.1:8000/">Interactive assistant</a></nav><h1>Real LLM Evaluation</h1><p class="notice">Actual local-model inference. All labels are provisional agent-assisted judgments. No independent human verification or production approval.</p>{dashboard_section(summary)}<section><h2>Generation settings</h2><p>Full policy document · configured context {run['generation_options']['num_ctx']} tokens · temperature {run['generation_options']['temperature']} · seed {run['generation_options']['seed']} · maximum output {run['generation_options']['num_predict']} tokens</p><p>Digest: {e(str(summary['model_metadata'].get('digest')))}</p><table><caption>Provisional classifications</caption><thead><tr><th>Classification</th><th>Count</th></tr></thead><tbody>{''.join(f'<tr><th>{e(k)}</th><td>{v}</td></tr>' for k,v in summary['counts'].items())}</tbody></table></section><h2>Actual answers and review evidence</h2>{cards}<footer><a href="real-model-evaluation.md">Full Markdown report</a> · <a href="real-model-metrics.json">Metrics and fingerprints</a></footer></main></body></html>'''
    (root / 'reports/real-model-dashboard.html').write_text(html_doc)
    # No prelabels: use the original rubric and reference evidence, not the synthetic candidate.
    tasks = build_tasks(dataset)
    actual = {row['test_id']: row for row in run['responses'] if row['status'] == 'success'}
    tasks = [task for task in tasks if task['data']['test_id'] in actual]
    for task in tasks:
        result = actual[task['data']['test_id']]['response']
        task['data'].update(candidate_response=result['answer'], response_source='ollama_local_inference',
                            model=run['model'], run_id=run['run_id'], response_time_seconds=result['response_time_seconds'])
    (root / 'label-studio/real-model-import-tasks.json').write_text(json.dumps(tasks, ensure_ascii=False, indent=2) + '\n')
    config = (root / 'label-studio/labeling-config.xml').read_text()
    config = config.replace('Synthetic portfolio demonstration', 'Real LLM portfolio demonstration').replace('Candidate response — synthetic_fixture', 'Candidate response — actual local-model inference')
    (root / 'label-studio/real-model-labeling-config.xml').write_text(config)
    return summary
