'use strict';
const byId = id => document.getElementById(id);
async function checkService() {
  try {
    const response = await fetch('/api/health');
    const data = await response.json();
    byId('service-status').textContent = data.status === 'ready' ? `● Local model ready · ${data.model}` : `Local model unavailable · ${data.error || 'Run the startup command to install the model.'}`;
  } catch (_) { byId('service-status').textContent = 'Local service unavailable. Open this app through the Python startup command.'; }
}
for (const example of document.querySelectorAll('[data-question]')) {
  example.addEventListener('click', () => { byId('question').value = example.dataset.question; byId('question').focus(); });
}
byId('question').addEventListener('keydown', event => {
  if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); if (!byId('ask-button').disabled) byId('question-form').requestSubmit(); }
});
byId('question-form').addEventListener('submit', async event => {
  event.preventDefault();
  const question = byId('question').value.trim();
  if (!question) return;
  byId('ask-button').disabled = true;
  byId('question').disabled = true;
  document.querySelectorAll('[data-question]').forEach(button => { button.disabled = true; });
  byId('progress').hidden = false;
  byId('error').hidden = true;
  byId('answer-panel').hidden = true;
  const controller = new AbortController();
  const deadline = setTimeout(() => controller.abort(), 605000);
  try {
    const response = await fetch('/api/ask', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({question}), signal: controller.signal});
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || `Request failed (HTTP ${response.status}).`);
    byId('answer').textContent = data.answer;
    byId('answer-meta').replaceChildren();
    for (const value of [`Model: ${data.model}`, `Profile: ${data.prompt_version || 'baseline'}`, `Response time: ${data.response_time_seconds.toFixed(2)} s`, `Prompt tokens: ${data.token_usage.prompt_eval_count ?? 'unreported'}`]) {
      const item = document.createElement('span'); item.textContent = value; byId('answer-meta').append(item);
    }
    byId('answer-warnings').textContent = data.warnings.join(' ');
    byId('answer-warnings').hidden = data.warnings.length === 0;
    byId('citations').replaceChildren();
    if (!data.policy_references.length) byId('citations').textContent = 'The model did not cite a recognized policy identifier. Check the handbook before relying on this answer.';
    for (const reference of data.policy_references) {
      const detail = document.createElement('details');
      const summary = document.createElement('summary'); summary.textContent = reference;
      const text = document.createElement('pre'); text.textContent = 'Loading the cited policy…';
      detail.append(summary, text); byId('citations').append(detail);
      fetch(`/api/policies/${encodeURIComponent(reference)}`).then(r => { if (!r.ok) throw new Error(); return r.json(); }).then(policy => { summary.textContent = `${reference} · ${policy.title}`; text.textContent = policy.text; }).catch(() => { text.textContent = 'Unable to load policy text. Consult data/company-policies.md.'; });
    }
    byId('answer-panel').hidden = false;
  } catch (error) {
    byId('error').textContent = error.name === 'AbortError' ? 'The request exceeded the browser time limit. Check the local model service and retry.' : error.message;
    byId('error').hidden = false;
  } finally {
    clearTimeout(deadline); byId('ask-button').disabled = false; byId('question').disabled = false;
    document.querySelectorAll('[data-question]').forEach(button => { button.disabled = false; });
    byId('progress').hidden = true;
  }
});
checkService();
