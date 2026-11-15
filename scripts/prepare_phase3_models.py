#!/usr/bin/env python3
"""Prepare the three small CPU comparison models; never pull an unbounded model list."""
import json,sys,urllib.request
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.start_assistant import ensure_model
from src.experiments import make_config
from src.assistant import PolicyAssistant

MODELS=['qwen2.5:3b','qwen3:4b-instruct-2507-q4_K_M','llama3.2:3b']
if __name__=='__main__':
 config=make_config();ensure_model(config,setup=True)
 client=PolicyAssistant(config).client
 installed={m['name'] for m in client.request('/api/tags')['models']}
 for model in MODELS:
  if model not in installed:
   request=urllib.request.Request(config['service_url']+'/api/pull',data=json.dumps({'model':model,'stream':True}).encode(),headers={'Content-Type':'application/json'})
   print('Downloading',model,flush=True)
   with urllib.request.urlopen(request,timeout=600) as stream:
    last=None
    for line in stream:
     row=json.loads(line)
     if row.get('error'):raise RuntimeError(row['error'])
     if row.get('total',0)>3_000_000_000:raise RuntimeError('A model layer exceeds the 3 GB automatic-download limit.')
     if row.get('status')!=last:print(row.get('status'),flush=True);last=row.get('status')
   if last!='success':raise RuntimeError('Model download did not complete')
  print(json.dumps(PolicyAssistant(make_config(model)).model_metadata(),indent=2))
