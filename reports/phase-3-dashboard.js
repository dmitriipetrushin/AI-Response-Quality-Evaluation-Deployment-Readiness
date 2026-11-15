'use strict';
const data=JSON.parse(document.getElementById('experiment-data').textContent);
const get=id=>document.getElementById(id);
const fmt=value=>value===null||value===undefined?'Unreviewed':Number(value).toFixed(1);
for(const [id,key] of [['model-filter','model'],['prompt-filter','prompt'],['split-filter','split']]){
 for(const value of [...new Set(data.experiments.map(e=>e[key]))].sort()){
  const option=document.createElement('option');option.value=value;option.textContent=value;get(id).append(option);
 }
 get(id).addEventListener('change',render);
}
for(const item of data.experiments){const option=document.createElement('option');option.value=item.experiment_id;option.textContent=item.experiment_id;get('experiment-select').append(option);}
if(data.final)get('experiment-select').value=data.final.experiment_id;
get('experiment-select').addEventListener('change',renderGroups);
function row(parent,values){const tr=document.createElement('tr');for(const value of values){const td=document.createElement('td');td.textContent=String(value);tr.append(td);}parent.append(tr);}
function render(){
 const items=data.experiments.filter(e=>(!get('model-filter').value||e.model===get('model-filter').value)&&(!get('prompt-filter').value||e.prompt===get('prompt-filter').value)&&(!get('split-filter').value||e.split===get('split-filter').value));
 const previous=get('experiment-select').value;get('experiment-select').replaceChildren();
 for(const e of items){const option=document.createElement('option');option.value=e.experiment_id;option.textContent=e.experiment_id;get('experiment-select').append(option);}
 if(items.some(e=>e.experiment_id===previous))get('experiment-select').value=previous;
 get('experiment-rows').replaceChildren();
 for(const e of items)row(get('experiment-rows'),[e.experiment_id,`${e.model} / ${e.prompt}`,`${e.split} / ${e.total}`,`${fmt(e.correct_rate)}%`,`${fmt(e.unsupported_rate)}%`,e.critical_failures??'Unknown',`${fmt(e.mean_latency)} / ${fmt(e.median_latency)} / ${fmt(e.p95_latency)}`,`${e.reviewed}/${e.total}`]);
 renderGroups();
}
function renderGroups(){
 const e=data.experiments.find(e=>e.experiment_id===get('experiment-select').value);if(!e){get('category-rows').replaceChildren();get('difficulty-rows').replaceChildren();get('resource-summary').textContent='No experiments match these filters.';return;}
 for(const [id,key] of [['category-rows','by_category'],['difficulty-rows','by_difficulty']]){get(id).replaceChildren();for(const [name,s] of Object.entries(e[key]))row(get(id),[name,`${s.correct}/${s.total}`,fmt(s.correct_rate)]);}
 get('resource-summary').replaceChildren();
 for(const text of [`Model: ${e.model}`,`Digest: ${e.model_metadata.digest??'Unreported'}`,`Quantization: ${e.model_metadata.details?.quantization_level??'Unreported'}; runtime: Ollama ${e.model_metadata.ollama_version??'Unreported'}`,`Settings: ${JSON.stringify(e.config.options)}; prompt: ${e.prompt}`,`Loaded model bytes: ${e.runtime.ollama_loaded_model_bytes??'Unreported'}; container memory: ${e.runtime.docker_memory_usage??'Unreported'}`]){const p=document.createElement('p');p.textContent=text;get('resource-summary').append(p);}
}
for(const [title,e] of [['Selected configuration',data.heldout],['Original baseline on identical held-out cases',data.baseline_heldout]]){
 if(!e)continue;const p=document.createElement('p');p.textContent=`${title}: ${fmt(e.correct_rate)}% Correct, ${fmt(e.unsupported_rate)}% Unsupported, ${e.critical_failures} critical, n=${e.total}, mean ${fmt(e.mean_latency)} s; nominal Wilson 95% ${e.nominal_wilson_95?.map(fmt).join('–')}%.`;get('heldout-summary').append(p);
}
render();
