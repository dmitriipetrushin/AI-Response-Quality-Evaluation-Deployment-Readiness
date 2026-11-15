"""Phase-3 unit tests: temporary mocked inference is never benchmark evidence."""
import copy,json,shutil,tempfile,unittest
from pathlib import Path
from unittest.mock import Mock,patch
from src.assistant import ROOT,PolicyAssistant,load_config
from src.model_client import ModelClient,ModelProtocolError
from src.prompting import load_prompt,parse_structured,response_schema,VERSIONS
from src.experiments import (sha,digest,validate_dataset,make_config,gate_split,run_experiment,
 read_experiment,write_reviews,summarize,freeze_selection,experiment_dir,wilson)


class PromptContractTests(unittest.TestCase):
 def test_known_versions_and_baseline_backward_compatibility(self):
  from src.assistant import SYSTEM_INSTRUCTIONS
  self.assertEqual(load_prompt('baseline',SYSTEM_INSTRUCTIONS,ROOT),SYSTEM_INSTRUCTIONS)
  self.assertEqual(len(VERSIONS),5)
  with self.assertRaises(ValueError):load_prompt('../../secret','baseline',ROOT)

 def test_valid_structured_response(self):
  value={'answer':'Ask your manager.','response_type':'answer','policy_references':['POL-001']}
  self.assertEqual(parse_structured(json.dumps(value),{'POL-001'}),value)
  self.assertEqual(response_schema({'POL-002'})['properties']['policy_references']['items']['enum'],['POL-002'])

 def test_malformed_structured_responses(self):
  values=['not json','[]',json.dumps({'answer':'','response_type':'answer','policy_references':[]}),
   json.dumps({'answer':'x','response_type':{},'policy_references':[]}),
   json.dumps({'answer':'x','response_type':'answer','policy_references':['POL-999']}),
   json.dumps({'answer':'x','response_type':'answer','policy_references':['POL-001','POL-001']})]
  for value in values:
   with self.subTest(value=value):
    with self.assertRaises(ModelProtocolError):parse_structured(value,{'POL-001'})

 def assistant(self,contents):
  c=make_config(prompt='structured');client=Mock()
  client.inspect_model.return_value={'digest':'unit-test'}
  client.chat.side_effect=[{'answer':text,'response_time_seconds':.5,'model':'qwen2.5:3b',
   'token_usage':{'prompt_eval_count':3000,'eval_count':30},'done_reason':'stop',
   'raw_response':{'message':{'content':text},'done':True}} for text in contents]
  return PolicyAssistant(c,client=client),client

 def test_one_controlled_format_retry_and_natural_rendering(self):
  valid=json.dumps({'answer':'Please clarify the location.','response_type':'clarify','policy_references':['POL-001']})
  assistant,client=self.assistant(['bad-json',valid]);r=assistant.answer('Can I work away?')
  self.assertEqual(client.chat.call_count,2);self.assertEqual(r['answer'],'Please clarify the location.')
  self.assertEqual(r['generated_content'],valid);self.assertEqual(r['response_time_seconds'],1)
  self.assertEqual(len(r['generation_attempts']),2);self.assertIn('validation_error',r['generation_attempts'][0])

 def test_retry_limit_exhausted_is_a_technical_error(self):
  assistant,client=self.assistant(['bad','still bad'])
  with self.assertRaises(ModelProtocolError) as caught:assistant.answer('Question')
  self.assertEqual(client.chat.call_count,2);self.assertEqual(len(caught.exception.attempts),2)

 def test_plain_answers_are_not_retried_for_quality(self):
  config=make_config();client=Mock();client.inspect_model.return_value={}
  client.chat.return_value={'answer':'See POL-999.','response_time_seconds':.1,'model':'qwen2.5:3b','raw_response':{'message':{'content':'See POL-999.'}},'token_usage':{},'done_reason':'stop'}
  r=PolicyAssistant(config,client=client).answer('Question')
  self.assertEqual(client.chat.call_count,1);self.assertEqual(r['invalid_policy_references'],['POL-999'])

 def test_model_format_and_thinking_payload(self):
  client=ModelClient('http://127.0.0.1:11434','qwen3:4b',{'num_ctx':8192})
  client.request=Mock(return_value={'model':'qwen3:4b','done':True,'message':{'content':'{}'}})
  client.chat([],response_format={'type':'object'},think=False)
  body=client.request.call_args.args[1]
  self.assertIs(body['think'],False);self.assertEqual(body['format'],{'type':'object'})


class ExperimentTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
  for folder in ['data/phase-3/dataset','prompts/phase-3','config','src','experiments/phase-3']:(self.root/folder).mkdir(parents=True,exist_ok=True)
  for name in ['data/company-policies.md','data/test-cases.json','config/assistant-baseline.json','src/assistant.py','src/model_client.py','src/prompting.py','src/experiments.py']:
   shutil.copy(ROOT/name,self.root/name)
  for folder in ['data/phase-3/dataset','prompts/phase-3']:
   for path in (ROOT/folder).iterdir():shutil.copy(path,self.root/folder/path.name)
  self.config=make_config(root=self.root);self.fake=Mock()
  self.fake.answer.side_effect=lambda q:{'answer':'Unit test response.','generated_content':'Unit test response.',
   'raw_response':{'message':{'content':'Unit test response.'},'done':True},'output_contract':'plain_text',
   'invalid_policy_references':[],'done_reason':'stop','generation_attempts':[]}
  self.patch1=patch('src.experiments.runtime_snapshot',return_value={'ollama_loaded_model_bytes':1,'docker_memory_usage':'unit-test'})
  self.patch2=patch('src.experiments.subprocess.check_output',return_value='unit-test-commit\n')
  self.patch1.start();self.patch2.start();self.addCleanup(self.patch1.stop);self.addCleanup(self.patch2.stop)

 def run_mock(self,eid='test-run',split='development',ids=None,config=None):
  return run_experiment(eid,config or self.config,split,root=self.root,ids=ids,assistant=self.fake)

 def review(self,eid,labels=None):
  _,rows=read_experiment(eid,self.root)
  judgments=[(r['test_id'],labels.get(r['test_id'],'Correct') if labels else 'Correct',False,'Unit-test judgment only.','none','low') for r in rows if r['status']=='success']
  write_reviews(eid,judgments,self.root)

 def test_dataset_integrity_and_historical_cases(self):
  m,cases=validate_dataset(self.root)
  self.assertEqual(len(cases),100);self.assertEqual([m['splits'][s]['count'] for s in ['development','validation','heldout']],[40,30,30])
  self.assertEqual(sum(c['historical_id'] is not None for c in cases),30)

 def test_frozen_dataset_edit_is_rejected(self):
  p=self.root/'data/phase-3/dataset/heldout.json';p.write_text('[]')
  with self.assertRaisesRegex(ValueError,'fingerprint'):validate_dataset(self.root)

 def test_cross_split_scenario_leak_is_rejected(self):
  path=self.root/'data/phase-3/dataset/validation.json';rows=json.loads(path.read_text())
  rows[0]['scenario_group']='historical-TC-001';path.write_text(json.dumps(rows))
  p=self.root/'data/phase-3/dataset/manifest.json';m=json.loads(p.read_text());m['splits']['validation']['sha256']=sha(path);p.write_text(json.dumps(m))
  with self.assertRaisesRegex(ValueError,'leaks'):validate_dataset(self.root)

 def test_heldout_locked_before_selection(self):
  with self.assertRaisesRegex(ValueError,'locked'):gate_split('heldout',self.config,self.root,'final')
  with self.assertRaisesRegex(ValueError,'locked'):gate_split('all',self.config,self.root,'final')

 def test_run_is_immutable_and_review_is_separate(self):
  self.run_mock(ids=['TC-001','TC-002']);s=summarize('test-run',self.root)
  self.assertIsNone(s['correct_rate']);self.assertEqual(s['reviewed'],0)
  with self.assertRaisesRegex(ValueError,'exists'):self.run_mock(ids=['TC-001','TC-002'])
  self.review('test-run',{'TC-002':'Partially correct'});s=summarize('test-run',self.root)
  self.assertEqual(s['correct_rate'],50);self.assertEqual(s['unsupported_rate'],0)
  self.assertTrue(s['complete_review']);self.assertEqual(s['critical_failures'],0)
  with self.assertRaisesRegex(ValueError,'already exist'):self.review('test-run')

 def test_response_seal_detects_tampering(self):
  self.run_mock(ids=['TC-001']);folder=experiment_dir('test-run',self.root)
  with (folder/'responses.jsonl').open('a') as f:f.write('{}\n')
  with self.assertRaisesRegex(ValueError,'modified'):read_experiment('test-run',self.root)

 def test_review_seal_detects_tampering(self):
  self.run_mock(ids=['TC-001']);self.review('test-run')
  p=experiment_dir('test-run',self.root)/'reviews.csv';p.write_text(p.read_text().replace('Correct','Incorrect'))
  with self.assertRaisesRegex(ValueError,'changed'):summarize('test-run',self.root)

 def test_resource_and_warmup_evidence_are_sealed(self):
  for name in ['runtime.json','warmup.json']:
   eid='tamper-'+name.split('.')[0];self.run_mock(eid,ids=['TC-001'])
   (experiment_dir(eid,self.root)/name).write_text('{}')
   with self.assertRaisesRegex(ValueError,'resource evidence'):read_experiment(eid,self.root)

 def test_failure_is_preserved_without_synthetic_substitution(self):
  self.fake.answer.side_effect=ModelProtocolError('unit-test invalid response')
  self.run_mock(ids=['TC-001']);_,rows=read_experiment('test-run',self.root)
  self.assertEqual(rows[0]['status'],'error');self.assertIsNone(rows[0]['response'])
  self.assertEqual(summarize('test-run',self.root)['failed'],1)

 def test_prompt_change_after_freeze_rejected(self):
  path=self.root/'prompts/phase-3/policy-workflow.txt';path.write_text('Changed after freeze')
  with self.assertRaisesRegex(ValueError,'Frozen prompt'):validate_dataset(self.root)

 def test_validation_only_selection_and_final_recipe_guard(self):
  self.run_mock('val-base','validation');self.review('val-base')
  self.run_mock('dev-base','development',ids=['TC-001']);self.review('dev-base')
  with self.assertRaisesRegex(ValueError,'validation'):freeze_selection(['dev-base'],self.root)
  selected=freeze_selection(['val-base'],self.root)
  gate_split('heldout',selected['config'],self.root,'final')
  altered=copy.deepcopy(selected['config']);altered['options']['temperature']=.9
  with self.assertRaisesRegex(ValueError,'recipe'):gate_split('heldout',altered,self.root,'final')
  with self.assertRaisesRegex(ValueError,'already frozen'):freeze_selection(['val-base'],self.root)

 def test_latency_quantiles_and_wilson(self):
  interval=wilson(27,30);self.assertLess(interval[0],90);self.assertGreater(interval[1],90)
  self.assertIsNone(wilson(0,0))
  self.run_mock(ids=['TC-001','TC-002']);self.review('test-run');s=summarize('test-run',self.root)
  self.assertGreaterEqual(s['p95_latency'],s['median_latency']);self.assertIn('factual',s['by_category'])

 def test_small_validation_gain_retains_baseline(self):
  cases=json.loads((self.root/'data/phase-3/dataset/validation.json').read_text())
  ids=[c['test_id'] for c in cases]
  self.run_mock('val-base','validation');self.review('val-base',{ids[0]:'Partially correct'})
  self.run_mock('val-alternative','validation',config=make_config(prompt='uncertainty-aware',root=self.root))
  self.review('val-alternative')
  selected=freeze_selection(['val-base','val-alternative'],self.root)
  self.assertEqual(selected['selected_experiment'],'val-base')
  self.assertIn('two additional',selected['baseline_retention_reason'])

 def test_safe_experiment_id(self):
  with self.assertRaises(ValueError):experiment_dir('../overwrite',self.root)

 def test_report_generation_is_offline_and_deterministic(self):
  from scripts.phase3_reports import generate
  self.run_mock(ids=['TC-001']);self.review('test-run')
  (self.root/'reports').mkdir();(self.root/'app').mkdir()
  shutil.copy(ROOT/'reports/real-model-metrics.json',self.root/'reports/real-model-metrics.json')
  shutil.copy(ROOT/'app/phase3-dashboard.js',self.root/'app/phase3-dashboard.js')
  payload=generate(self.root)
  self.assertEqual(payload['experiments'][0]['correct_rate'],100)
  page=(self.root/'reports/phase-3-dashboard.html').read_text()
  self.assertIn('model-filter',page);self.assertIn('difficulty-rows',page)
  self.assertNotIn('P3-T-',page)
  before=(self.root/'reports/phase-3-metrics.json').read_bytes();generate(self.root)
  self.assertEqual(before,(self.root/'reports/phase-3-metrics.json').read_bytes())

 def test_dashboard_json_escapes_script_termination(self):
  from scripts.phase3_reports import generate
  from html.parser import HTMLParser
  malicious='</script><script>alert(1)</script>'
  config=copy.deepcopy(self.config);config['model']=malicious
  self.run_mock(config=config,ids=['TC-001']);self.review('test-run')
  (self.root/'reports').mkdir();(self.root/'app').mkdir()
  shutil.copy(ROOT/'reports/real-model-metrics.json',self.root/'reports/real-model-metrics.json')
  shutil.copy(ROOT/'app/phase3-dashboard.js',self.root/'app/phase3-dashboard.js')
  generate(self.root);page=(self.root/'reports/phase-3-dashboard.html').read_text()
  self.assertNotIn(malicious,page)
  payload=page.split('id="experiment-data">',1)[1].split('</script>',1)[0]
  self.assertEqual(json.loads(payload)['experiments'][0]['model'],malicious)


if __name__=='__main__':unittest.main()
