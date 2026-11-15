#!/usr/bin/env python3
"""Run, inspect, compare, and freeze split-controlled local-model experiments."""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.experiments import make_config,run_experiment,summarize,freeze_selection,validate_dataset,SCREEN_IDS


def main():
 p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
 run=sub.add_parser('run');run.add_argument('--id',required=True);run.add_argument('--model',default='qwen2.5:3b');run.add_argument('--prompt',default='baseline');run.add_argument('--split',choices=['development','validation','heldout','all'],default='development');run.add_argument('--screen',action='store_true');run.add_argument('--resume',action='store_true');run.add_argument('--purpose',default='candidate',choices=['candidate','final','baseline-control']);run.add_argument('--context',type=int,default=8192);run.add_argument('--output-tokens',type=int,default=384);run.add_argument('--temperature',type=float,default=0)
 compare=sub.add_parser('compare');compare.add_argument('ids',nargs='+')
 select=sub.add_parser('select');select.add_argument('ids',nargs='+')
 sub.add_parser('validate-dataset')
 a=p.parse_args()
 try:
  if a.command=='run':
   c=make_config(a.model,a.prompt,overrides={'num_ctx':a.context,'num_predict':a.output_tokens,'temperature':a.temperature})
   result=run_experiment(a.id,c,a.split,ids=SCREEN_IDS if a.screen else None,resume=a.resume,purpose=a.purpose)
  elif a.command=='compare':result=[summarize(i) for i in a.ids]
  elif a.command=='select':result=freeze_selection(a.ids)
  else:
   m,cases=validate_dataset();result={'version':m['version'],'total':len(cases),'splits':m['splits']}
  print(json.dumps(result,ensure_ascii=False,indent=2));return 0
 except (ValueError,OSError,KeyError) as exc:print(str(exc),file=sys.stderr);return 1

if __name__=='__main__':sys.exit(main())
