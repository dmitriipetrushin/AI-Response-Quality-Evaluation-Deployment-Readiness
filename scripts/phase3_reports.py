#!/usr/bin/env python3
"""Export reproducible experiment comparisons and an offline interactive dashboard."""
import csv,html,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.assistant import ROOT
from src.experiments import summarize,read_experiment,read_reviews,experiment_dir,validate_dataset,digest


def collect(root=ROOT):
 root=Path(root);manifest,_=validate_dataset(root);items=[]
 for path in sorted((root/'experiments/phase-3').iterdir()):
  if path.is_dir() and (path/'seal.json').exists():items.append(summarize(path.name,root))
 selection=json.loads((root/'experiments/phase-3/selection.json').read_text()) if (root/'experiments/phase-3/selection.json').exists() else None
 # Replays get new IDs; they must not silently replace the canonical final evidence.
 final=next((s for s in items if s['experiment_id']=='final-selected' and s['purpose']=='final' and s['split']=='all'),None)
 control=next((s for s in items if s['experiment_id']=='final-baseline-heldout' and s['purpose']=='baseline-control' and s['split']=='heldout'),None)
 held=summarize(final['experiment_id'],root,only_split='heldout') if final else None
 historical_subset=None;critical_examples=[]
 if final:
  metadata,rows=read_experiment(final['experiment_id'],root);reviews=read_reviews(final['experiment_id'],rows,root)
  old_ids={c['test_id'] for c in json.loads((root/'data/test-cases.json').read_text())}
  subset=[r for r in reviews if r['test_id'] in old_ids]
  by_id={r['test_id']:r for r in rows}
  for review in reviews:
   if review['critical_failure']=='true':
    row=by_id[review['test_id']]
    critical_examples.append({'test_id':row['test_id'],'split':row['split'],'question':row['question'],
     'answer':row['response']['answer'],'classification':review['classification'],'rationale':review['rationale']})
  historical_subset={'total':30,'reviewed':len(subset),'correct':sum(r['classification']=='Correct' for r in subset),
   'correct_rate':100*sum(r['classification']=='Correct' for r in subset)/30,
   'unsupported':sum(r['classification']=='Unsupported' for r in subset),'critical':sum(r['critical_failure']=='true' for r in subset),
   'caveat':'These original cases were exposed development cases, not a held-out generalization benchmark.'}
 return {'dataset_version':manifest['version'],'dataset_sha256':digest(manifest),'case_count':manifest['total'],
         'experiments':items,'selection':selection,'final':final,'heldout':held,'baseline_heldout':control,
         'original_30_selected':historical_subset,'critical_examples':critical_examples,'judgment_disclosure':'All classifications are provisional agent-assisted reviews. No independent human annotations.',
         'historical_phase2':json.loads((root/'reports/real-model-metrics.json').read_text())}


def paired_examples(payload,root=ROOT):
 if not payload['final']:return []
 eid=payload['final']['experiment_id'];_,rows=read_experiment(eid,root)
 reviews={r['test_id']:r for r in read_reviews(eid,rows,root)}
 old=json.loads((Path(root)/'data/real-model-responses.json').read_text())
 old_answers={r['test_id']:r for r in old['responses']}
 old_reviews={r['test_id']:r for r in csv.DictReader((Path(root)/'data/real-model-evaluation.csv').open())}
 rank={'Correct':3,'Partially correct':2,'Unsupported':0,'Incorrect':0}
 examples=[]
 for row in rows:
  tid=row['test_id']
  if tid not in old_answers or tid not in reviews:continue
  before=old_reviews[tid]['classification'];after=reviews[tid]['classification']
  if before==after:continue
  examples.append({'test_id':tid,'question':row['question'],'before_classification':before,'after_classification':after,
   'change':'improvement' if rank[after]>rank[before] else 'regression' if rank[after]<rank[before] else 'changed failure type',
   'baseline_answer':old_answers[tid]['response']['answer'],'selected_answer':row['response']['answer'] if row['response'] else 'INFERENCE FAILED',
   'rationale':reviews[tid]['rationale'],'dataset_status':'exposed original development case'})
 return examples


def validation_examples(payload,root=ROOT):
 """Matched same-prompt examples from candidates, never claimed as selected/held-out gains."""
 ids={s['experiment_id'] for s in payload['experiments']}
 if not {'val-workflow','val-qwen3-instruct'}<=ids:return []
 _,before_rows=read_experiment('val-workflow',root);_,after_rows=read_experiment('val-qwen3-instruct',root)
 before_reviews={r['test_id']:r for r in read_reviews('val-workflow',before_rows,root)}
 after_reviews={r['test_id']:r for r in read_reviews('val-qwen3-instruct',after_rows,root)}
 old={r['test_id']:r for r in before_rows};rank={'Correct':3,'Partially correct':2,'Incorrect':0,'Unsupported':0}
 result=[];counts={'improvement':0,'regression':0}
 for row in after_rows:
  tid=row['test_id']
  if tid not in before_reviews or tid not in after_reviews:continue
  a=before_reviews[tid]['classification'];b=after_reviews[tid]['classification']
  if rank[a]==rank[b]:continue
  change='improvement' if rank[b]>rank[a] else 'regression'
  if counts[change]>=2:continue
  counts[change]+=1
  result.append({'test_id':tid,'question':row['question'],'before_classification':a,'after_classification':b,
   'change':change,'baseline_answer':old[tid]['response']['answer'],'selected_answer':row['response']['answer'],
   'before_source':'Validation: Qwen2.5 3B / policy-workflow','after_source':'Validation: Qwen3 Instruct 4B / policy-workflow (not selected)',
   'rationale':after_reviews[tid]['rationale'],'dataset_status':'Matched validation question used for selection; not a selected-profile or held-out improvement.'})
 return result


def generate(root=ROOT):
 root=Path(root);payload=collect(root);examples=paired_examples(payload,root)+validation_examples(payload,root)
 report=root/'reports';report.mkdir(exist_ok=True)
 (report/'phase-3-metrics.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
 fields=['experiment_id','model','prompt','split','total','successful','reviewed','correct_rate','unsupported_rate','critical_failures','mean_latency','median_latency','p95_latency','unknown_id_answers','truncated_answers','retry_requests']
 with (report/'phase-3-comparison.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n',extrasaction='ignore');w.writeheader();w.writerows(payload['experiments'])
 fmt=lambda x:'Unreviewed' if x is None else f'{x:.1f}'
 lines=['# Phase 3 comparative evaluation','',payload['judgment_disclosure'],'',
 'The original synthetic baseline is an authored illustration, not a model benchmark. The historical Phase-2 score is a 30-case exposed baseline. Compare matched cases and split-specific results; do not call cross-dataset differences measured improvement.','',
 f"Dataset: {payload['dataset_version']} · {payload['case_count']} cases · 40 development / 30 validation / 30 held out.",'',
 '## Experiment comparison','', '| Experiment | Model | Prompt | Split / n | Correct % | Unsupported % | Critical | Mean / median / P95 seconds | Review coverage |', '|---|---|---|---|---:|---:|---:|---|---|']
 for s in payload['experiments']:
  lines.append(f"| {s['experiment_id']} | {s['model']} | {s['prompt']} | {s['split']} / {s['total']} | {fmt(s['correct_rate'])} | {fmt(s['unsupported_rate'])} | {s['critical_failures']} | {fmt(s['mean_latency'])} / {fmt(s['median_latency'])} / {fmt(s['p95_latency'])} | {s['reviewed']}/{s['total']} |")
 lines += ['', '## Configuration and measured footprint', '', '| Experiment | Digest | Quantization | Temperature | Context / output tokens | Think option | Loaded-model GiB | Container memory |', '|---|---|---|---:|---|---|---:|---|']
 for s in payload['experiments']:
  model=s['model_metadata'];opts=s['config']['options'];mem=s['runtime'].get('ollama_loaded_model_bytes')
  lines.append(f"| {s['experiment_id']} | {model.get('digest','Unreported')} | {model.get('details',{}).get('quantization_level','Unreported')} | {opts.get('temperature')} | {opts['num_ctx']} / {opts['num_predict']} | {s['config'].get('think','default')} | {f'{mem/1024**3:.2f}' if mem else 'Unreported'} | {s['runtime'].get('docker_memory_usage','Unreported')} |")
 lines+=['','Development screens intentionally emphasize historical failures and are not comparable to the complete Phase-2 average. Early screens overlapped a model download; model latency comparisons use the later validation/final runs without downloads. Each experiment has a separate actual-output seal, source commit/hash, prompt/configuration, warm-up record, model identity, and memory snapshot.','',
 '## Selection and final evidence','']
 if payload['selection']:
  selection=payload['selection'];lines += [f"Selected validation experiment: **{selection['selected_experiment']}**.",f"Recipe: `{json.dumps(selection['config'],sort_keys=True)}`.",f"Frozen at {selection['frozen_at']}. Selection order: {selection['rank_order']}.",str(selection.get('baseline_retention_reason') or 'A candidate met the predeclared practical validation-improvement rule.'),'']
 else:lines+=['Selection has not been frozen; no held-out performance is claimed.','']
 if payload['final']:
  final=payload['final'];held=payload['heldout'];base=payload['baseline_heldout']
  lines += [f"Selected aggregate: **{fmt(final['correct_rate'])}% Correct**, **{fmt(final['unsupported_rate'])}% Unsupported**, **{final['critical_failures']} critical**, {final['reviewed']}/{final['total']} provisionally reviewed; mean {final['mean_latency']:.2f} s.",
   'This pooled 100-case result includes development and validation questions used during optimization/selection. The held-out result below is the final question-holdout comparison.','',
   '| Matched held-out test | n | Correct % | Unsupported % | Critical | Mean / median / P95 s | Nominal Wilson 95% interval for Correct |','|---|---:|---:|---:|---:|---|---|']
  for title,s in [('Selected',held),('Original baseline, newly run on the same held-out cases',base)]:
   if s:lines.append(f"| {title} | {s['total']} | {fmt(s['correct_rate'])} | {fmt(s['unsupported_rate'])} | {s['critical_failures']} | {s['mean_latency']:.2f} / {s['median_latency']:.2f} / {s['p95_latency']:.2f} | {s['nominal_wilson_95']} |")
  old=payload['original_30_selected'];lines += ['',f"On the same original 30 development cases, the selected profile is {old['correct_rate']:.1f}% Correct ({old['correct']}/30), compared with the historical/reproduced 46.7% (14/30). This is an exposed-case comparison and does not establish held-out generalization.",'']
  for key,title in [('by_category','Category'),('by_difficulty','Difficulty')]:
   lines += [f'### Selected configuration by {title.lower()}', '', f'| {title} | Cases | Correct | Correct % |', '|---|---:|---:|---:|']
   lines += [f"| {name} | {s['total']} | {s['correct']} | {fmt(s['correct_rate'])} |" for name,s in final[key].items()]
   lines += ['']
 if payload['critical_examples']:
  lines+=['## Critical findings in the final 100 (provisional)','','These are judgments about generated advice, not claims that a real purchase, disclosure or loss occurred.','']
  for issue in payload['critical_examples']:
   lines += [f"### {issue['test_id']} / {issue['split']}",'',issue['question'],'','Actual answer:',issue['answer'],'','Provisional rationale: '+issue['rationale'],'']
 lines += ['## Engineering targets and uncertainty','',
 'Phase-3 engineering targets are Correct ≥85%, Unsupported ≤3%, zero critical failures, mean latency ≤10 seconds, and at least 100 cases. The original Phase-1/2 business-quality target was 90% Correct; the historical reports keep that threshold. Meeting either target set provisionally does not authorize deployment.','',
 'Nominal Wilson intervals assume independent Bernoulli observations and condition on the provisional labels. The questions are a nonrandom agent-authored set within the same fictional handbook; the intervals are illustrative uncertainty summaries, not validated population-accuracy guarantees. The same agent authored references and reviewed outputs. No independent human validation or reviewer agreement is claimed.','',
 'Loaded-model bytes come from Ollama /api/ps, while container memory is separately sampled with docker stats. Neither is a guaranteed process-RSS/VRAM peak. CPU execution, four inference threads, seed 42, nominal temperature 0 and Q4_K_M quantization are documented in the individual records. Context/temperature ablations are explicitly identified; models have different tokenizers and the same token cap does not mean the same word budget. Warm-up/cold loading is recorded separately and excluded from timed case means.','',
 'The full handbook fits the context window. Retrieval was not added: the observed failures primarily involve interpretation, instruction following and omitted workflow details, and section retrieval could omit cross-policy requirements. This is a feasibility-based scope decision, not an unmeasured claim that retrieval would perform worse.','',
 '**Deployment recommendation: NO-GO pending adequate independent human review, broader representative/adversarial coverage, operational controls and approval.** Continue development according to the observed improvement/regression evidence; no production rollout or real employee outcome is claimed.','',
 '## Improvement and regression examples on matched questions','','Markdown presentation trims line-ending whitespace; sealed raw records retain every generated character. HTML preserves answer whitespace through character references.','']
 for ex in examples:
  lines += [f"### {ex['test_id']} · {ex['change']} ({ex['before_classification']} → {ex['after_classification']})",'',ex['dataset_status'],'',ex['question'],'',ex.get('before_source','Phase-2 baseline')+':',ex['baseline_answer'],'',ex.get('after_source','Selected profile')+':',ex['selected_answer'],'','Provisional rationale: '+ex['rationale'],'']
 (report/'phase-3-comparison.md').write_text('\n'.join(line.rstrip() for line in '\n'.join(lines).split('\n'))+'\n')
 e=html.escape
 render_answer=lambda value:e(value).replace('\n','&#10;')
 cases_html=''
 critical_html=''
 if payload['critical_examples']:
  critical_html='<section><h2>Critical findings in the final 100</h2><p>Provisional judgments about generated advice; no actual purchase, disclosure or loss occurred.</p>'
  for issue in payload['critical_examples']:
   critical_html+=f'<details><summary>{e(issue["test_id"])} / {e(issue["split"])}</summary><p>{e(issue["question"])}</p><p class="answer">{render_answer(issue["answer"])}</p><p>{e(issue["rationale"])}</p></details>'
  critical_html+='</section>'
 for ex in examples:
  cases_html+=f'<details><summary>{e(ex["test_id"])} · {e(ex["change"])} · {e(ex["before_classification"])} → {e(ex["after_classification"])}</summary><p>{e(ex["question"])}</p><h3>{e(ex.get("before_source","Phase-2 actual answer"))}</h3><p class="answer">{render_answer(ex["baseline_answer"])}</p><h3>{e(ex.get("after_source","Selected actual answer"))}</h3><p class="answer">{render_answer(ex["selected_answer"])}</p><p>{e(ex["rationale"])}</p><small>{e(ex["dataset_status"])} Provisional review.</small></details>'
 final_text='Final results are not available until validation-only selection and final evaluation complete.'
 if payload['final']:
  s=payload['final'];h=payload['heldout'];final_text=f"Selected: {s['model']} / {s['prompt']}. Pooled {s['total']} cases: {fmt(s['correct_rate'])}% Correct, {fmt(s['unsupported_rate'])}% Unsupported, {s['critical_failures']} critical, mean {s['mean_latency']:.2f} s. Held-out {h['total']} cases: {fmt(h['correct_rate'])}% Correct."
 data=json.dumps(payload,ensure_ascii=False).replace('<',chr(92)+'u003c')
 html_doc=f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Phase 3 · LLM experiments</title><script src="phase-3-dashboard.js" defer></script><style>body{{margin:0;background:#f2f5f7;color:#152a3a;font:16px/1.6 system-ui,sans-serif}}main{{max-width:1280px;margin:auto;padding:32px 24px}}h1{{line-height:1.15}}a,summary{{color:#12646b}}section,details{{background:white;border:1px solid #d3dde4;border-radius:10px;padding:22px;margin:20px 0}}.notice{{background:#fff6df;border:1px solid #d4ad4d;padding:16px}}.decision{{background:#fff0f2;border-left:5px solid #a51c30;padding:18px}}.filters{{display:flex;gap:18px;flex-wrap:wrap}}label{{display:flex;flex-direction:column;font-size:14px}}select{{font:inherit;padding:8px;max-width:100%}}.scroll{{overflow-x:auto}}table{{border-collapse:collapse;width:100%;font-size:14px}}th,td{{padding:11px;border-bottom:1px solid #d3dde4;text-align:left}}th{{background:#f3f7f8}}p,td,summary{{overflow-wrap:anywhere}}small{{color:#526474}}summary{{font-weight:650;cursor:pointer}}.answer{{white-space:pre-wrap}}a:focus-visible,select:focus-visible,summary:focus-visible{{outline:3px solid #be8100;outline-offset:3px}}.groups{{display:grid;grid-template-columns:1fr 1fr;gap:20px}}@media(max-width:700px){{main{{padding:18px 12px}}.groups{{grid-template-columns:1fr}}section{{padding:16px}}}}</style></head><body><main><nav><a href="dashboard.html">All phases</a> · <a href="http://127.0.0.1:8000/">Interactive assistant</a> · <a href="phase-3-comparison.md">Full evidence report</a></nav><p>Dmitry Petrushin · Independent fictional-company portfolio</p><h1>Phase 3: LLM optimization and comparison</h1><p class="notice">Actual local-model inference. All quality labels are provisional agent-assisted judgments. No independent human validation. Synthetic fixtures are not a real-model performance benchmark.</p><p class="decision"><b>NO-GO for deployment pending adequate human validation.</b><br>{e(final_text)}</p>{critical_html}<section><h2>Experiment comparison</h2><p>Filter results by model, prompt and split. Compare identical validation/held-out cases. Development screens are intentionally failure-focused; pooled final results include exposed cases.</p><div class="filters"><label>Model<select id="model-filter"><option value="">All models</option></select></label><label>Prompt<select id="prompt-filter"><option value="">All prompts</option></select></label><label>Split<select id="split-filter"><option value="">All splits</option></select></label><label>Breakdown experiment<select id="experiment-select"></select></label></div><div class="scroll"><table><thead><tr><th>Experiment</th><th>Model / prompt</th><th>Split / n</th><th>Correct</th><th>Unsupported</th><th>Critical</th><th>Mean / median / P95 s</th><th>Review coverage</th></tr></thead><tbody id="experiment-rows"></tbody></table></div></section><div class="groups"><section><h2>By category</h2><div class="scroll"><table><thead><tr><th>Category</th><th>Correct / cases</th><th>Correct %</th></tr></thead><tbody id="category-rows"></tbody></table></div></section><section><h2>By difficulty</h2><div class="scroll"><table><thead><tr><th>Difficulty</th><th>Correct / cases</th><th>Correct %</th></tr></thead><tbody id="difficulty-rows"></tbody></table></div></section></div><section><h2>Matched final held-out comparison</h2><div id="heldout-summary"></div><p>Nominal intervals condition on provisional labels and independent-case assumptions. This authored question set is not a random employee-traffic sample.</p></section><section><h2>Model identity and resource evidence</h2><div id="resource-summary"></div><p>Runtime versions, digests, quantization and settings are recorded for each actual run. Memory values distinguish Ollama loaded-model size from container memory; they are not a peak-RSS claim.</p></section><section><h2>Observed improvements and regressions</h2><p>Original-case examples use exposed development questions. Validation examples compare Qwen2.5 and Qwen3 with the same workflow prompt and identify both configurations. They are not selected-profile or held-out gains.</p>{cases_html or '<p>No original-case classification changes were observed.</p>'}</section><footer><a href="phase-3-metrics.json">JSON metrics</a> · <a href="phase-3-comparison.csv">CSV comparison</a> · Synthetic baseline and Phase-2 results remain available on the all-phases dashboard.</footer><script type="application/json" id="experiment-data">{data}</script></main></body></html>'''
 (report/'phase-3-dashboard.html').write_text(html_doc)
 (report/'phase-3-dashboard.js').write_bytes((root/'app/phase3-dashboard.js').read_bytes())
 return payload

if __name__=='__main__':
 payload=generate();print(json.dumps({'experiments':len(payload['experiments']),'selected':payload['selection']['selected_experiment'] if payload['selection'] else None,'final_cases':payload['final']['total'] if payload['final'] else 0}))
