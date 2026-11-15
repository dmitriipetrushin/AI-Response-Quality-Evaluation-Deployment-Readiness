#!/usr/bin/env python3
"""Prepare unannotated final real-model tasks with experiment/case provenance."""
import hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.assistant import ROOT
from src.experiments import validate_dataset,read_experiment,read_reviews
from src.policy_loader import load_policies


def prepare(root=ROOT):
 root=Path(root);selection=json.loads((root/'experiments/phase-3/selection.json').read_text())
 finals=[]
 for folder in (root/'experiments/phase-3').iterdir():
  if folder.is_dir() and (folder/'seal.json').exists():
   meta,rows=read_experiment(folder.name,root)
   if meta['experiment_id']=='final-selected' and meta['purpose']=='final' and meta['split']=='all':finals.append((meta,rows))
 if len(finals)!=1:raise ValueError('Exactly one sealed final 100-case run is required.')
 metadata,records=finals[0];_,cases=validate_dataset(root);by_id={c['test_id']:c for c in cases};policies=load_policies(root/'data/company-policies.md')
 tasks=[]
 for index,row in enumerate(records,1):
  if row['status']!='success':continue
  case=by_id[row['test_id']];response=row['response']
  context='\n\n'.join(policies.sections[p]['text'] for p in case['policy_references']) if case['policy_references'] else policies.text
  tasks.append({'id':index,'data':{'test_id':row['test_id'],'experiment_id':metadata['experiment_id'],
   'model':metadata['config']['model'],'model_digest':response['model_metadata']['digest'],'prompt_version':metadata['config'].get('prompt_version','baseline'),
   'question':row['question'],'policy_context':context,'reference_answer':case['reference_answer'],'acceptance_criteria':case['acceptance_criteria'],
   'expected_behavior':case['expected_behavior'],'difficulty':case['difficulty'],'split':case['split'],
   'candidate_response':response['answer'],'response_source':'actual_ollama_local_inference',
   'response_sha256':hashlib.sha256(response['answer'].encode()).hexdigest(),
   'provisional_review_artifact':'experiments/phase-3/'+metadata['experiment_id']+'/reviews.csv',
   'review_status':'unannotated; independent human review pending'}})
 path=root/'label-studio/phase-3-import-tasks.json';path.write_text(json.dumps(tasks,ensure_ascii=False,indent=2)+'\n')
 xml='''<View>
 <Header value="Phase 3 — Actual local-model answers; independent human review pending"/>
 <Text name="case_id" value="$test_id"/><Text name="experiment" value="$experiment_id"/>
 <Text name="model" value="$model"/><Text name="prompt" value="$prompt_version"/>
 <Header value="Question"/><Text name="question" value="$question"/>
 <Header value="Policy evidence"/><Text name="context" value="$policy_context"/>
 <Header value="Reference answer — policy-check required"/><Text name="reference" value="$reference_answer"/>
 <Header value="Acceptance criteria"/><Text name="criteria" value="$acceptance_criteria"/>
 <Header value="Actual model answer"/><Text name="candidate" value="$candidate_response"/>
 <Choices name="classification" toName="candidate" choice="single-radio" required="true">
  <Choice value="Correct"/><Choice value="Partially correct"/><Choice value="Incorrect"/><Choice value="Unsupported"/>
 </Choices>
 <Header value="Critical failure"/>
 <Choices name="critical_failure" toName="candidate" choice="single-radio" required="true"><Choice value="Yes"/><Choice value="No"/></Choices>
 <Header value="Failure reasons — choose None for no failure"/>
 <Choices name="failure_reasons" toName="candidate" choice="multiple" required="true">
  <Choice value="None"/><Choice value="Factual error"/><Choice value="Hallucination or unsupported claim"/><Choice value="Incomplete response"/>
  <Choice value="Question interpretation"/><Choice value="Workflow reasoning"/><Choice value="Instruction following"/>
  <Choice value="Formatting or truncation"/><Choice value="Unnecessary refusal"/><Choice value="Uncertainty handling"/><Choice value="Citation support"/>
 </Choices>
 <Header value="Response failure severity"/>
 <Choices name="severity" toName="candidate" choice="single-radio" required="true">
  <Choice value="Low"/><Choice value="Medium"/><Choice value="High"/><Choice value="Critical"/>
 </Choices>
 <TextArea name="reviewer_comments" toName="candidate" rows="4" required="true" placeholder="Explain the decision using the handbook. No independent-human status is inferred merely from an export."/>
</View>'''
 (root/'label-studio/phase-3-labeling-config.xml').write_text(xml+'\n')
 return tasks

if __name__=='__main__':print('Prepared',len(prepare()),'unannotated final tasks.')
