"""Append-only real-inference experiments, split guards, provisional review, and metrics."""
import csv
import hashlib
import json
import math
import re
import statistics
import subprocess
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from .assistant import ROOT, PolicyAssistant, load_config
from .prompting import VERSIONS

REVIEW_FIELDS = ['test_id','response_sha256','classification','critical_failure','rationale','failure_reason','severity','evaluation_method']
CLASSIFICATIONS = ('Correct','Partially correct','Incorrect','Unsupported')
SCREEN_IDS = ['TC-001','TC-004','TC-006','TC-011','TC-012','TC-016','TC-018','TC-020','TC-023','TC-026','TC-027','TC-029']


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True).encode()).hexdigest()


def answer_hash(text):
    return hashlib.sha256(text.encode()).hexdigest()


def atomic_json(path, value):
    path = Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    temp = path.with_suffix(path.suffix+'.tmp')
    temp.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n');temp.replace(path)


def validate_dataset(root=ROOT):
    root = Path(root);folder=root/'data/phase-3/dataset'
    manifest=json.loads((folder/'manifest.json').read_text())
    all_cases=[]
    for split in ['development','validation','heldout']:
        path=folder/(split+'.json');cases=json.loads(path.read_text())
        if manifest['splits'][split] != {'count':len(cases),'sha256':sha(path)}:
            raise ValueError('Frozen dataset fingerprint changed: '+split)
        required={'test_id','question','category','difficulty','failure_severity','expected_behavior','reference_answer','acceptance_criteria','scenario_group','reference_status','policy_references','policy_context','split'}
        for c in cases:
            if not required.issubset(c) or any(not c[k] for k in required-{'policy_references'}):raise ValueError('Incomplete phase-3 case')
            if c['split']!=split or c['difficulty'] not in {'easy','medium','hard'}:raise ValueError('Invalid case split or difficulty')
            if c['failure_severity'] not in {'low','medium','high','critical'}:raise ValueError('Invalid case severity')
        all_cases.extend(cases)
    ids=[c['test_id'] for c in all_cases]
    normalized=[re.sub(r'\W+','',c['question'].casefold()) for c in all_cases]
    if len(all_cases)<100 or len(all_cases)!=manifest['total'] or len(set(ids))!=len(ids) or len(set(normalized))!=len(normalized):
        raise ValueError('Need at least 100 unique case IDs and normalized questions.')
    groups={}
    from .policy_loader import load_policies
    policies=load_policies(root/'data/company-policies.md')
    if policies.sha256!=manifest['policy_sha256']:raise ValueError('Policy source changed after dataset freeze')
    for c in all_cases:
        if set(c['policy_references'])-set(policies.sections):raise ValueError('Unknown reference policy')
        group=c['scenario_group']
        if group in groups and groups[group]!=c['split']:raise ValueError('Scenario group leaks between splits')
        groups[group]=c['split']
    old=json.loads((root/'data/test-cases.json').read_text())
    if sha(root/'data/test-cases.json')!=manifest['original_cases_sha256']:raise ValueError('Historical questions changed')
    by_id={c['test_id']:c for c in all_cases}
    if any(by_id[c['test_id']]['split']!='development' or by_id[c['test_id']]['question']!=c['employee_question'] or by_id[c['test_id']]['reference_answer']!=c['reference_answer'] for c in old):
        raise ValueError('Original cases must remain unchanged development examples')
    for name,expected in manifest['frozen_prompt_sha256'].items():
        if sha(root/'prompts/phase-3'/(name+'.txt'))!=expected:raise ValueError('Frozen prompt version changed: '+name)
    from .assistant import SYSTEM_INSTRUCTIONS
    if hashlib.sha256(SYSTEM_INSTRUCTIONS.encode()).hexdigest()!=manifest['frozen_prompt_sha256']['baseline']:
        raise ValueError('Historical baseline system instructions changed')
    return manifest,all_cases


def make_config(model='qwen2.5:3b',prompt='baseline',root=ROOT,overrides=None):
    config=load_config(Path(root)/'config/assistant-baseline.json')
    config.update(model=model,prompt_version=prompt)
    if prompt not in VERSIONS:raise ValueError('Unknown prompt')
    if model.startswith('qwen3:'):config['think']=False
    if overrides:config['options'].update(overrides)
    if not 256<=config['options']['num_predict']<config['options']['num_ctx']<=32768:raise ValueError('Invalid generation budget')
    return config


def experiment_dir(experiment_id,root=ROOT):
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{2,79}',experiment_id):raise ValueError('Unsafe experiment identifier')
    return Path(root)/'experiments/phase-3'/experiment_id


def gate_split(split,config,root=ROOT,purpose='candidate'):
    if split not in {'development','validation','heldout','all'}:raise ValueError('Invalid dataset split')
    if split in {'heldout','all'}:
        path=Path(root)/'experiments/phase-3/selection.json'
        if not path.exists():raise ValueError('Held-out execution is locked until validation-only selection is frozen.')
        selection=json.loads(path.read_text());manifest,_=validate_dataset(root)
        if selection['dataset_sha256']!=digest(manifest):raise ValueError('Selection dataset fingerprint differs')
        expected=selection['config']
        if purpose=='baseline-control':expected=make_config(root=root)
        elif purpose!='final':raise ValueError('Held-out runs must be final or the frozen baseline control.')
        if config!=expected:raise ValueError('Held-out recipe must match the frozen selection or baseline control.')


def runtime_snapshot(assistant):
    try:
        ps=assistant.client.request('/api/ps',timeout=5)
        model_bytes=sum(m.get('size',0) for m in ps.get('models',[]))
    except Exception:
        ps=None;model_bytes=None
    stats=subprocess.run(['docker','stats','--no-stream','--format','{{.MemUsage}}','northstar-ollama'],capture_output=True,text=True)
    return {'ollama_loaded_model_bytes':model_bytes,'ollama_ps':ps,
            'docker_memory_usage':stats.stdout.strip() if stats.returncode==0 else None,
            'memory_note':'Ollama loaded-model size and container usage, not a per-process RSS or peak VRAM guarantee.'}


def run_experiment(experiment_id,config,split,root=ROOT,ids=None,resume=False,purpose='candidate',assistant=None):
    root=Path(root);manifest,cases=validate_dataset(root);gate_split(split,config,root,purpose)
    selected=[c for c in cases if split=='all' or c['split']==split]
    if ids is not None:
        if not ids or len(set(ids))!=len(ids) or set(ids)-{c['test_id'] for c in selected}:raise ValueError('Invalid subset IDs')
        selected=[c for c in selected if c['test_id'] in ids]
    folder=experiment_dir(experiment_id,root)
    prompt_name=config.get('prompt_version','baseline')
    provenance={'config':config,'split':split,'case_ids':[c['test_id'] for c in selected],
                'dataset_sha256':digest(manifest),'prompt_sha256':manifest['frozen_prompt_sha256'][prompt_name],
                'purpose':purpose}
    if folder.exists():
        if not resume:raise ValueError('Experiment exists; use --resume. Completed results are immutable.')
        metadata=json.loads((folder/'experiment.json').read_text())
        if any(metadata[k]!=v for k,v in provenance.items()):raise ValueError('Experiment resume provenance mismatch')
        if (folder/'seal.json').exists():verify_seal(folder);return metadata
    else:
        folder.mkdir(parents=True)
        code_paths=['src/assistant.py','src/model_client.py','src/prompting.py','src/experiments.py']
        commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
        metadata={'experiment_id':experiment_id,'timestamp':datetime.now(timezone.utc).isoformat(),
            'git_commit':commit,'source_sha256':{p:sha(root/p) for p in code_paths},
            'source':'actual_ollama_local_inference','dataset_version':manifest['version'],
            'random_seed':config['options'].get('seed'),**provenance}
        atomic_json(folder/'experiment.json',metadata)
    records=[]
    response_path=folder/'responses.jsonl'
    if response_path.exists():records=[json.loads(line) for line in response_path.read_text().splitlines() if line]
    if len({r['test_id'] for r in records})!=len(records) or set(r['test_id'] for r in records)-set(provenance['case_ids']):raise ValueError('Duplicate or foreign response records')
    seen={r['test_id'] for r in records}
    assistant=assistant or PolicyAssistant(config,root=root)
    if not (folder/'warmup.json').exists():
        start=time.perf_counter()
        try:
            warm=assistant.answer('State only the title of the supplied fictional handbook.')
            warmup={'status':'success','response':warm,'wall_seconds':time.perf_counter()-start}
        except Exception as exc:
            warmup={'status':'error','error':str(exc),'wall_seconds':time.perf_counter()-start}
        atomic_json(folder/'warmup.json',warmup)
    for case in selected:
        if case['test_id'] in seen:continue
        validate_dataset(root) # Abort on mid-experiment dataset/prompt edits.
        started=time.perf_counter()
        row={'test_id':case['test_id'],'question':case['question'],'category':case['category'],
             'difficulty':case['difficulty'],'split':case['split'],'attempted_at':datetime.now(timezone.utc).isoformat()}
        try:
            response=assistant.answer(case['question'])
            row.update(status='success',response=response,error=None,
                       deterministic_checks={'nonempty':bool(response['answer'].strip()),
                         'unknown_policy_ids':response['invalid_policy_references'],
                         'output_truncated':response.get('done_reason')=='length',
                         'structured_contract_valid':response.get('output_contract')=='json_schema' if prompt_name=='structured' else None})
        except Exception as exc:
            row.update(status='error',response=None,error={'type':type(exc).__name__,'message':str(exc),
                       'attempts':getattr(exc,'attempts',[])},deterministic_checks=None)
        row['latency_seconds']=round(time.perf_counter()-started,6)
        with response_path.open('a',encoding='utf-8') as stream:stream.write(json.dumps(row,ensure_ascii=False)+'\n')
        records.append(row)
        print(f'{experiment_id} {row["test_id"]} {row["status"]} {row["latency_seconds"]:.2f}s',flush=True)
    if len(records)==len(selected):
        runtime=runtime_snapshot(assistant)
        atomic_json(folder/'runtime.json',runtime)
        atomic_json(folder/'seal.json',{'experiment_sha256':sha(folder/'experiment.json'),'responses_sha256':sha(response_path),
                                     'completed_at':datetime.now(timezone.utc).isoformat(),'records':len(records)})
    return metadata


def verify_seal(folder):
    folder=Path(folder);seal=json.loads((folder/'seal.json').read_text())
    if seal['experiment_sha256']!=sha(folder/'experiment.json') or seal['responses_sha256']!=sha(folder/'responses.jsonl'):
        raise ValueError('Sealed experiment data was modified')


def read_experiment(experiment_id,root=ROOT):
    folder=experiment_dir(experiment_id,root);verify_seal(folder)
    metadata=json.loads((folder/'experiment.json').read_text())
    records=[json.loads(line) for line in (folder/'responses.jsonl').read_text().splitlines() if line]
    if len(records)!=len(metadata['case_ids']) or len({r['test_id'] for r in records})!=len(records):raise ValueError('Experiment record count mismatch')
    for row in records:
        if row['status']=='success':
            result=row['response'];raw=result['raw_response']['message']['content']
            if result.get('generated_content',result['answer'])!=raw:raise ValueError('Generated content differs from raw output')
            if result.get('output_contract')=='json_schema' and json.loads(raw)['answer']!=result['answer']:raise ValueError('Structured answer rendering differs')
    return metadata,records


def write_reviews(experiment_id,judgments,root=ROOT):
    folder=experiment_dir(experiment_id,root);metadata,records=read_experiment(experiment_id,root)
    by_id={r['test_id']:r for r in records}
    path=folder/'reviews.csv'
    if path.exists():raise ValueError('Reviews already exist; historical reviews are not overwritten.')
    rows=[]
    for tid,label,critical,rationale,reason,severity in judgments:
        row=by_id.get(tid)
        if not row or row['status']!='success' or label not in CLASSIFICATIONS or type(critical) is not bool or not rationale.strip():raise ValueError('Invalid provisional judgment')
        if label=='Correct' and critical:raise ValueError('Correct cannot be critical')
        rows.append({'test_id':tid,'response_sha256':answer_hash(row['response']['answer']),
           'classification':label,'critical_failure':str(critical).lower(),'rationale':rationale,
           'failure_reason':reason,'severity':severity,'evaluation_method':'provisional_agent_assisted_review'})
    if len({r['test_id'] for r in rows})!=len(rows):raise ValueError('Duplicate review IDs')
    with path.open('x',newline='',encoding='utf-8') as stream:
        writer=csv.DictWriter(stream,fieldnames=REVIEW_FIELDS,lineterminator='\n');writer.writeheader();writer.writerows(rows)
    atomic_json(folder/'review-seal.json',{'reviews_sha256':sha(path),'method':'provisional_agent_assisted_review','independent_human_validation':False})


def read_reviews(experiment_id,records,root=ROOT):
    folder=experiment_dir(experiment_id,root);path=folder/'reviews.csv'
    if not path.exists():return []
    seal=json.loads((folder/'review-seal.json').read_text())
    if seal['reviews_sha256']!=sha(path):raise ValueError('Sealed provisional reviews changed')
    rows=list(csv.DictReader(path.open()));by_id={r['test_id']:r for r in records}
    if len({r['test_id'] for r in rows})!=len(rows):raise ValueError('Duplicate reviews')
    for review in rows:
        row=by_id.get(review['test_id'])
        if (not row or row['status']!='success' or review['response_sha256']!=answer_hash(row['response']['answer'])
            or review['classification'] not in CLASSIFICATIONS or review['critical_failure'] not in {'true','false'}
            or review['evaluation_method']!='provisional_agent_assisted_review' or not review['rationale'].strip()):raise ValueError('Review does not match actual inference')
    return rows


def wilson(correct,total):
    if not total:return None
    z=1.959963984540054;p=correct/total;den=1+z*z/total
    center=(p+z*z/(2*total))/den;half=z*math.sqrt(p*(1-p)/total+z*z/(4*total*total))/den
    return [100*(center-half),100*(center+half)]


def summarize(experiment_id,root=ROOT,only_split=None):
    metadata,records=read_experiment(experiment_id,root)
    reviews=read_reviews(experiment_id,records,root)
    if only_split:records=[r for r in records if r['split']==only_split]
    ids={r['test_id'] for r in records};reviews=[r for r in reviews if r['test_id'] in ids]
    total=len(records);success=[r for r in records if r['status']=='success'];times=[r['latency_seconds'] for r in success]
    counts={label:sum(r['classification']==label for r in reviews) for label in CLASSIFICATIONS}
    critical=sum(r['critical_failure']=='true' for r in reviews)
    complete=len(reviews)==total and len(success)==total and total>0
    def groups(key):
        result={}
        for value in sorted({r[key] for r in records}):
            groupids={r['test_id'] for r in records if r[key]==value};rs=[r for r in reviews if r['test_id'] in groupids]
            result[value]={'total':len(groupids),'reviewed':len(rs),'correct':sum(r['classification']=='Correct' for r in rs),
                           'correct_rate':100*sum(r['classification']=='Correct' for r in rs)/len(groupids) if rs else None}
        return result
    return {'experiment_id':experiment_id,'model':metadata['config']['model'],'prompt':metadata['config'].get('prompt_version','baseline'),
        'split':only_split or metadata['split'],'purpose':metadata['purpose'],'total':total,'successful':len(success),'failed':total-len(success),
        'reviewed':len(reviews),'review_coverage':len(reviews)*100/total if total else 0,'counts':counts,
        'correct_rate':counts['Correct']*100/total if reviews and total else None,
        'unsupported_rate':counts['Unsupported']*100/total if reviews and total else None,
        'critical_failures':critical if reviews else None,'mean_latency':statistics.mean(times) if times else None,
        'median_latency':statistics.median(times) if times else None,'p95_latency':sorted(times)[math.ceil(.95*len(times))-1] if times else None,
        'nominal_wilson_95':wilson(counts['Correct'],total) if complete else None,
        'complete_review':complete,'by_category':groups('category'),'by_difficulty':groups('difficulty'),
        'unknown_id_answers':sum(bool(r['response']['invalid_policy_references']) for r in success),
        'truncated_answers':sum(r['response'].get('done_reason')=='length' for r in success),
        'retry_requests':sum(max(0,len(r['response'].get('generation_attempts',[]))-1) for r in success),
        'config':metadata['config'],'model_metadata':success[0]['response'].get('model_metadata',{}) if success else {},
        'runtime':json.loads((experiment_dir(experiment_id,root)/'runtime.json').read_text()),
        'judgment_status':'provisional_agent_assisted; no independent human validation'}


def freeze_selection(experiment_ids,root=ROOT):
    root=Path(root);manifest,_=validate_dataset(root)
    path=root/'experiments/phase-3/selection.json'
    if path.exists():raise ValueError('Selection is already frozen; do not retune after held-out access.')
    summaries=[summarize(i,root) for i in experiment_ids]
    expected=[c['test_id'] for c in json.loads((root/'data/phase-3/dataset/validation.json').read_text())]
    for s in summaries:
        meta,_=read_experiment(s['experiment_id'],root)
        if s['split']!='validation' or meta['case_ids']!=expected or not s['complete_review']:
            raise ValueError('Selection requires complete, same-case validation runs and reviews.')
    # Predeclared before experiment execution: safety/reliability, target violations,
    # then correctness, unsupported count, latency and loaded-model footprint.
    def rank(s):
        violations=sum([s['correct_rate']<85,s['unsupported_rate']>3,s['mean_latency']>10])
        memory=s['runtime'].get('ollama_loaded_model_bytes') or float('inf')
        return (s['critical_failures'],s['failed'],s['truncated_answers'],violations,-s['counts']['Correct'],s['counts']['Unsupported'],s['mean_latency'],memory)
    ranked=sorted(summaries,key=rank)
    best=ranked[0]
    baseline=next((s for s in summaries if s['model']=='qwen2.5:3b' and s['prompt']=='baseline'),None)
    retention_reason=None
    if baseline and best['experiment_id']!=baseline['experiment_id']:
        if (best['counts']['Correct']-baseline['counts']['Correct']<2
            or best['critical_failures']>baseline['critical_failures']
            or best['counts']['Unsupported']>baseline['counts']['Unsupported']):
            best=baseline
            retention_reason='No candidate met the predeclared minimum of two additional Correct validation cases without more critical or Unsupported outcomes.'
    selection={'frozen_at':datetime.now(timezone.utc).isoformat(),'dataset_sha256':digest(manifest),
       'selected_experiment':best['experiment_id'],'config':best['config'],
       'minimum_meaningful_gain_correct_cases':2,'baseline_retention_reason':retention_reason,
       'rank_order':'critical failures; request failures; truncated outputs; number of violated Correct/Unsupported/latency targets; descending Correct count; Unsupported count; mean latency; loaded-model bytes',
       'validation_experiments':[s['experiment_id'] for s in ranked],
       'validation_evidence':{s['experiment_id']:{'responses':sha(experiment_dir(s['experiment_id'],root)/'responses.jsonl'),'reviews':sha(experiment_dir(s['experiment_id'],root)/'reviews.csv')} for s in ranked},
       'human_validated':False,'production_decision':'NO-GO pending independent validation'}
    atomic_json(path,selection);return selection
