#!/usr/bin/env python3
"""Generate deterministic Markdown, standalone HTML, and JSON from validated fixtures."""
import argparse
import hashlib
import html
import json
import sys
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

if __package__:
    from .validate_dataset import ROOT, CATEGORY_COUNTS, CLASSIFICATIONS, DatasetValidationError, load_dataset
else:
    from validate_dataset import ROOT, CATEGORY_COUNTS, CLASSIFICATIONS, DatasetValidationError, load_dataset

CATEGORY_NAMES = {'factual': 'Straightforward factual', 'multi_step': 'Multi-step policy',
                  'ambiguous': 'Ambiguous', 'out_of_scope': 'Outside the knowledge base',
                  'sensitive': 'Sensitive / high risk'}
INPUTS = ['data/company-policies.md', 'data/test-cases.json',
          'data/candidate-responses.json', 'data/evaluation-results.csv']


def acceptance_gates(total, correct, unsupported, critical, evaluated):
    """Integer comparisons avoid rounding a failing result into a passing gate."""
    return {
        'correct_rate': {'target': 'At least 90%', 'passed': total > 0 and correct * 100 >= 90 * total},
        'unsupported_rate': {'target': 'No more than 5%', 'passed': total > 0 and unsupported * 100 <= 5 * total},
        'critical_failures': {'target': 'Zero', 'passed': total > 0 and critical == 0},
        'coverage': {'target': '100%', 'passed': total > 0 and evaluated == total},
    }


def calculate_metrics(dataset):
    total = len(dataset.cases)
    counts = {label: 0 for label in CLASSIFICATIONS}
    counts.update(Counter(row['classification'] for row in dataset.evaluations))
    critical = sum(row['critical_failure'] for row in dataset.evaluations)
    pct = lambda n: n * 100 / total if total else 0.0
    categories = {}
    for category in CATEGORY_COUNTS:
        cases = [c for c in dataset.cases if c['category'] == category]
        rows = [r for r in dataset.evaluations if r['category'] == category]
        categories[category] = {
            'total': len(cases), 'evaluated': len(rows),
            'counts': {label: sum(r['classification'] == label for r in rows) for label in CLASSIFICATIONS},
            'correct_rate': sum(r['classification'] == 'Correct' for r in rows) * 100 / len(cases) if cases else 0.0,
            'critical_failures': sum(r['critical_failure'] for r in rows),
        }
    gates = acceptance_gates(total, counts['Correct'], counts['Unsupported'], critical, len(dataset.evaluations))
    return {'total': total, 'evaluated': len(dataset.evaluations), 'counts': counts,
            'correct_rate': pct(counts['Correct']), 'unsupported_rate': pct(counts['Unsupported']),
            'critical_failures': critical, 'coverage': pct(len(dataset.evaluations)),
            'categories': categories, 'gates': gates,
            'decision': 'GATES MET — independent real-model validation still required' if all(g['passed'] for g in gates.values()) else 'NO-GO — acceptance gates failed',
            'response_source': 'synthetic_fixture', 'evaluation_method': 'simulated_review',
            'disclosure': 'Synthetic demonstration responses with simulated review labels; not production-model accuracy or independent human annotation.'}


def markdown_report(dataset, metrics):
    m = metrics
    lines = ['# Quality Evaluation Report', '', '**Independent portfolio simulation · Northstar Business Services (fictional)**', '',
             m['disclosure'], '', f"**Deployment recommendation: {m['decision']}.**", '',
             'Synthetic fixtures validate the evaluation process and demonstrate failure handling. They cannot establish the safety of any model. No deployment occurred.', '',
             '| Classification | Count | Share |', '|---|---:|---:|']
    for label, count in m['counts'].items():
        lines.append(f'| {label} | {count} | {count / m["total"]:.1%} |')
    actuals = {'correct_rate': f"{m['correct_rate']:.1f}% ({m['counts']['Correct']}/{m['total']})",
               'unsupported_rate': f"{m['unsupported_rate']:.1f}% ({m['counts']['Unsupported']}/{m['total']})",
               'critical_failures': str(m['critical_failures']), 'coverage': f"{m['coverage']:.1f}% ({m['evaluated']}/{m['total']})"}
    lines += ['', '## Proposed acceptance gates', '', 'Targets are proposed project requirements. At 30 cases, Correct must be at least 27 and Unsupported at most 1. Decisions use exact counts, not rounded percentages.', '',
              '| Metric | Actual | Target | Result |', '|---|---:|---|---|']
    for key, gate in m['gates'].items():
        lines.append(f"| {key.replace('_', ' ').title()} | {actuals[key]} | {gate['target']} | {'PASS' if gate['passed'] else 'FAIL'} |")
    lines += ['', '## Category results', '', '| Category | Cases | Correct | Partial | Incorrect | Unsupported | Correct % | Critical |', '|---|---:|---:|---:|---:|---:|---:|---:|']
    for category, values in m['categories'].items():
        counts = values['counts']
        lines.append(f"| {CATEGORY_NAMES[category]} | {values['total']} | {counts['Correct']} | {counts['Partially correct']} | {counts['Incorrect']} | {counts['Unsupported']} | {values['correct_rate']:.1f}% | {values['critical_failures']} |")
    lines += ['', '## Case-level simulated review audit', '', '| Case | Classification | Critical | Policy references | Rationale |', '|---|---|---|---|---|']
    escape = lambda value: str(value).replace('|', '\\|').replace('\n', ' ')
    for row in dataset.evaluations:
        lines.append('| ' + ' | '.join(escape(v) for v in [row['test_id'], row['classification'], 'Yes' if row['critical_failure'] else 'No', row['policy_references'] or 'Handbook scope / information absent', row['evaluation_rationale']]) + ' |')
    lines += ['', '## Required actions before a real pilot', '',
              '1. Remediate credential-sharing, purchase-splitting, and supplier-bank-change failure scenarios; recheck every critical case.',
              '2. Add grounding checks, missing-information handling, and a clear approval checklist; retest omissions and unsupported benefits.',
              '3. Evaluate actual versioned model outputs on a broader holdout dataset with independent reviewers, adjudication, and privacy review.',
              '4. Obtain fictional-role-equivalent business, security, and QA sign-off against all gates before considering a limited deployment.', '',
              '## Limits and provenance', '',
              'Thirty intentionally selected fixtures are not a representative sample of employee traffic. Labels and references were authored within this demonstration; no independent agreement statistic or model-accuracy confidence interval is claimed. A critical failure blocks release regardless of aggregate score. Structural validation cannot prove semantic correctness. Label Studio runtime status is documented in `label-studio/setup-guide.md`.', '',
              'SHA-256 input fingerprints are stored in `metrics.json`. Regenerate this report after any input change.']
    return '\n'.join(lines) + '\n'


def html_dashboard(dataset, m, real_summary=None):
    e = html.escape
    from scripts.real_model_report import dashboard_section
    real_section = dashboard_section(real_summary)
    gate_summary = ('Demonstration fixtures meet the proposed gates; independent model validation is still required.'
                    if all(g['passed'] for g in m['gates'].values())
                    else 'Demonstration fixtures fail the proposed gates.')
    cards = ''.join(f'<article class="card"><p>{title}</p><strong>{value}</strong><small>{detail}</small></article>' for title, value, detail in [
        ('Correct', f"{m['correct_rate']:.1f}%", f"{m['counts']['Correct']} of {m['total']} · target ≥90%"),
        ('Unsupported', f"{m['unsupported_rate']:.1f}%", f"{m['counts']['Unsupported']} of {m['total']} · target ≤5%"),
        ('Critical failures', str(m['critical_failures']), 'Target: zero'),
        ('Review coverage', f"{m['coverage']:.0f}%", f"{m['evaluated']} of {m['total']} · target 100%")])
    gates = ''.join(f'<li class="{"pass" if g["passed"] else "fail"}"><b>{"PASS" if g["passed"] else "FAIL"}</b> {e(k.replace("_", " ").title())}<span>{e(g["target"])}</span></li>' for k, g in m['gates'].items())
    category_rows = ''
    for category, values in m['categories'].items():
        counts = values['counts']
        category_rows += '<tr><th scope="row">' + e(CATEGORY_NAMES[category]) + '</th>' + ''.join(f'<td>{v}</td>' for v in [values['total'], counts['Correct'], counts['Partially correct'], counts['Incorrect'], counts['Unsupported'], f"{values['correct_rate']:.1f}%", values['critical_failures']]) + '</tr>'
    classifications = ''.join(f'<li><span>{e(label)}</span><b>{count}</b><meter min="0" max="{m["total"]}" value="{count}" aria-label="{e(label)}: {count} of {m["total"]}">{count}</meter></li>' for label, count in m['counts'].items())
    cases = {c['test_id']: c for c in dataset.cases}
    responses = {r['test_id']: r for r in dataset.responses}
    audit = ''
    for row in dataset.evaluations:
        tid = row['test_id']; case = cases[tid]
        fields = [('Question', case['employee_question']), ('Policy context', case['policy_context']),
                  ('Reference answer', case['reference_answer']), ('Expected behavior', case['expected_behavior']),
                  ('Acceptance criteria', case['acceptance_criteria']), ('Candidate response', responses[tid]['candidate_response']),
                  ('Review rationale', row['evaluation_rationale']), ('Policy references', row['policy_references'] or 'Handbook scope; answer absent')]
        audit += f'<details><summary><b>{e(tid)}</b> · {e(row["classification"])}{" · CRITICAL" if row["critical_failure"] else ""}<span>{e(CATEGORY_NAMES[case["category"]])}</span></summary><dl>' + ''.join(f'<dt>{e(k)}</dt><dd>{e(v)}</dd>' for k, v in fields) + '</dl></details>'
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AI Response Quality Evaluation Pilot — Synthetic Baseline</title>
<style>
:root{{--ink:#152a3a;--muted:#526474;--paper:#f2f5f7;--red:#a51c30;--green:#12613f;--line:#d3dde4}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--paper);color:var(--ink);font:16px/1.6 system-ui,sans-serif}}main{{max-width:1180px;margin:auto;padding:42px 24px 64px}}header{{border-top:5px solid #166a72;padding:24px 0}}.eyebrow{{font-size:12px;letter-spacing:.13em;text-transform:uppercase;font-weight:750;color:#16616a}}h1{{font-size:clamp(28px,4vw,44px);line-height:1.15;max-width:850px;margin:14px 0}}h2{{font-size:22px;margin-top:0}}p{{max-width:85ch}}.muted,small{{color:var(--muted)}}.notice{{background:#fff6df;border:1px solid #d4ad4d;padding:16px 20px;border-radius:8px}}.decision{{border-left:5px solid var(--red);background:#fff0f2;padding:16px 20px;margin:24px 0}}.decision strong{{color:var(--red)}}.cards{{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin:28px 0}}.card,section{{background:white;border:1px solid var(--line);border-radius:10px;padding:22px}}.card p{{margin:0;font-weight:650}}.card strong{{display:block;font-size:36px;line-height:1.6}}small{{display:block}}section{{margin-top:22px}}.two{{display:grid;grid-template-columns:1fr 1fr;gap:22px}}ul{{list-style:none;padding:0;margin:0}}li{{margin:12px 0}}.gates li{{padding:12px;border-radius:5px}}.gates b{{margin-right:12px}}.gates span{{display:block;margin-left:54px;font-size:14px}}.fail{{background:#fff0f2;color:var(--red)}}.pass{{background:#eaf8f0;color:var(--green)}}.distribution li{{display:grid;grid-template-columns:1fr 30px;gap:5px}}meter{{grid-column:1/-1;width:100%;height:15px}}.table-scroll{{overflow-x:auto}}table{{border-collapse:collapse;width:100%;text-align:left;font-size:14px}}th,td{{padding:13px 10px;border-bottom:1px solid var(--line)}}thead{{background:#f2f6f8}}tbody th{{font-weight:600;min-width:190px}}td{{text-align:right}}details{{border-top:1px solid var(--line);padding:14px 0}}summary{{cursor:pointer;line-height:1.8}}summary span{{display:block;color:var(--muted);font-size:13px;margin-left:18px}}dt{{font-weight:700;margin-top:13px}}dd{{margin:3px 0;white-space:pre-wrap}}footer{{font-size:13px;color:var(--muted);margin-top:30px}}a{{color:#09606a}}a:focus-visible,summary:focus-visible{{outline:3px solid #be8100;outline-offset:4px}}@media(max-width:800px){{.cards{{grid-template-columns:repeat(2,1fr)}}.two{{grid-template-columns:1fr}}main{{padding:20px 14px}}}}@media(max-width:420px){{.cards{{grid-template-columns:1fr}}}}@media print{{body{{background:white}}main{{padding:0}}.card,section{{break-inside:avoid}}details{{break-inside:avoid}}}}
</style></head><body><main>
<header><div class="eyebrow">Dmitry Petrushin · Independent portfolio simulation</div>
<h1>AI Response Quality Evaluation Pilot</h1><p class="muted">A release decision grounded in policy evidence, explicit quality gates, and an auditable review process.</p></header>
{real_section}
<div class="notice"><b>SYNTHETIC DATA · SIMULATED REVIEW</b><br>{e(m['disclosure'])} Northstar Business Services is fictional.</div>
<h2 id="synthetic-baseline">Synthetic Evaluation Baseline</h2>
<div class="decision"><strong>{e(m['decision'])}</strong><br>{e(gate_summary)} This synthetic baseline uses authored answers; no business deployment occurred.</div>
<div class="cards">{cards}</div>
<div class="two"><section><h2>Proposed acceptance gates</h2><ul class="gates">{gates}</ul><p class="muted">For 30 cases: at least 27 Correct, at most 1 Unsupported, and no critical failures. Exact counts determine the decision.</p></section>
<section><h2>Classification distribution</h2><ul class="distribution">{classifications}</ul><p class="muted">Precedence: contradiction → Incorrect; otherwise unsupported material claim → Unsupported; otherwise omission → Partially correct; otherwise Correct.</p></section></div>
<section><h2>Results by question category</h2><div class="table-scroll"><table><caption>Thirty synthetic cases, grouped by question category</caption><thead><tr><th scope="col">Category</th><th scope="col">Cases</th><th scope="col">Correct</th><th scope="col">Partial</th><th scope="col">Incorrect</th><th scope="col">Unsupported</th><th scope="col">Correct %</th><th scope="col">Critical</th></tr></thead><tbody>{category_rows}</tbody></table></div></section>
<section><h2>Case-level evidence</h2><p class="muted">Expand any case to inspect its question, policy evidence, candidate response, and simulated review rationale.</p>{audit}</section>
<section><h2>Decision and next steps</h2><p>Address credential sharing, approval bypasses, and supplier payment controls first. Improve grounding and completeness, then evaluate versioned real-model outputs with independent reviewers and a broader holdout set. Business, security, and QA approval are required before a controlled pilot can be considered.</p><p class="muted">This intentionally selected sample demonstrates the process; it cannot estimate production accuracy, user adoption, or financial return. Label Studio integration status is documented in the repository setup guide.</p></section>
<footer>Offline report · No remote fonts, scripts, or services · Sources: data/*.json, data/evaluation-results.csv, data/company-policies.md<br>Reproduce: <code>python3 scripts/generate_report.py</code> · <a href="quality-report.md">Markdown quality report</a> · <a href="metrics.json">Metrics and input fingerprints</a></footer>
</main></body></html>'''


def generate_reports(root=ROOT, output_dir=None):
    root = Path(root)
    dataset = load_dataset(root)
    metrics = calculate_metrics(dataset)
    from scripts.real_model_report import real_summary
    actual_summary = real_summary(root)
    metrics['input_sha256'] = {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in INPUTS}
    output = Path(output_dir) if output_dir is not None else root / 'reports'
    output.mkdir(parents=True, exist_ok=True)
    (output / 'quality-report.md').write_text(markdown_report(dataset, metrics), encoding='utf-8')
    (output / 'dashboard.html').write_text(html_dashboard(dataset, metrics, actual_summary), encoding='utf-8')
    (output / 'metrics.json').write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return metrics


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--output-dir', type=Path)
    args = parser.parse_args()
    try:
        m = generate_reports(args.root, args.output_dir)
    except (DatasetValidationError, OSError) as exc:
        print(f'Report generation failed: {exc}', file=sys.stderr)
        return 1
    print(f"Generated Markdown, HTML, JSON: Correct {m['correct_rate']:.1f}%; "
          f"Unsupported {m['unsupported_rate']:.1f}%; critical {m['critical_failures']}; coverage {m['coverage']:.1f}%")
    print(m['decision'])
    return 0


if __name__ == '__main__':
    sys.exit(main())
