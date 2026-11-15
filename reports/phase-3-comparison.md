# Phase 3 comparative evaluation

All classifications are provisional agent-assisted reviews. No independent human annotations.

The original synthetic baseline is an authored illustration, not a model benchmark. The historical Phase-2 score is a 30-case exposed baseline. Compare matched cases and split-specific results; do not call cross-dataset differences measured improvement.

Dataset: northstar-policy-eval-v3.1 · 100 cases · 40 development / 30 validation / 30 held out.

## Experiment comparison

| Experiment | Model | Prompt | Split / n | Correct % | Unsupported % | Critical | Mean / median / P95 seconds | Review coverage |
|---|---|---|---|---:|---:|---:|---|---|
| dev-baseline | qwen2.5:3b | baseline | development / 12 | 16.7 | 16.7 | 0 | 8.0 / 5.9 / 22.9 | 12/12 |
| dev-context-4096 | qwen2.5:3b | policy-workflow | development / 12 | 50.0 | 0.0 | 0 | 11.9 / 9.4 / 44.4 | 12/12 |
| dev-instruction-focused | qwen2.5:3b | instruction-focused | development / 12 | 41.7 | 16.7 | 0 | 9.4 / 7.4 / 23.0 | 12/12 |
| dev-policy-workflow | qwen2.5:3b | policy-workflow | development / 12 | 50.0 | 0.0 | 0 | 11.7 / 8.3 / 40.8 | 12/12 |
| dev-structured | qwen2.5:3b | structured | development / 12 | 0.0 | 8.3 | 1 | 8.4 / 6.7 / 21.0 | 12/12 |
| dev-temperature-03 | qwen2.5:3b | policy-workflow | development / 12 | 33.3 | 8.3 | 0 | 11.4 / 7.5 / 38.0 | 12/12 |
| dev-uncertainty-aware | qwen2.5:3b | uncertainty-aware | development / 12 | 41.7 | 8.3 | 0 | 8.1 / 5.9 / 26.2 | 12/12 |
| val-baseline | qwen2.5:3b | baseline | validation / 30 | 66.7 | 0.0 | 1 | 7.7 / 6.0 / 15.9 | 30/30 |
| val-llama | llama3.2:3b | policy-workflow | validation / 30 | 46.7 | 3.3 | 0 | 9.1 / 7.2 / 18.1 | 30/30 |
| val-qwen3-instruct | qwen3:4b-instruct-2507-q4_K_M | policy-workflow | validation / 30 | 76.7 | 10.0 | 0 | 26.2 / 26.4 / 53.7 | 30/30 |
| val-uncertainty | qwen2.5:3b | uncertainty-aware | validation / 30 | 63.3 | 0.0 | 1 | 6.4 / 6.4 / 10.5 | 30/30 |
| val-workflow | qwen2.5:3b | policy-workflow | validation / 30 | 46.7 | 10.0 | 1 | 11.0 / 9.9 / 21.1 | 30/30 |

## Configuration and measured footprint

| Experiment | Digest | Quantization | Temperature | Context / output tokens | Think option | Loaded-model GiB | Container memory |
|---|---|---|---:|---|---|---:|---|
| dev-baseline | 357c53fb659c5076de1d65ccb0b397446227b71a42be9d1603d46168015c9e4b | Q4_K_M | 0 | 8192 / 384 | default | 2.25 | 2.365GiB / 15.34GiB |
| dev-context-4096 | 357c53fb659c5076de1d65ccb0b397446227b71a42be9d1603d46168015c9e4b | Q4_K_M | 0 | 4096 / 384 | default | 2.02 | 2.124GiB / 15.34GiB |
| dev-instruction-focused | 357c53fb659c5076de1d65ccb0b397446227b71a42be9d1603d46168015c9e4b | Q4_K_M | 0 | 8192 / 384 | default | 2.25 | 2.445GiB / 15.34GiB |
| dev-policy-workflow | 357c53fb659c5076de1d65ccb0b397446227b71a42be9d1603d46168015c9e4b | Q4_K_M | 0 | 8192 / 384 | default | 2.25 | 2.646GiB / 15.34GiB |
| dev-structured | 357c53fb659c5076de1d65ccb0b397446227b71a42be9d1603d46168015c9e4b | Q4_K_M | 0 | 8192 / 384 | default | 2.25 | 2.772GiB / 15.34GiB |
| dev-temperature-03 | 357c53fb659c5076de1d65ccb0b397446227b71a42be9d1603d46168015c9e4b | Q4_K_M | 0.3 | 8192 / 384 | default | 2.25 | 2.35GiB / 15.34GiB |
| dev-uncertainty-aware | 357c53fb659c5076de1d65ccb0b397446227b71a42be9d1603d46168015c9e4b | Q4_K_M | 0 | 8192 / 384 | default | 2.25 | 2.545GiB / 15.34GiB |
| val-baseline | 357c53fb659c5076de1d65ccb0b397446227b71a42be9d1603d46168015c9e4b | Q4_K_M | 0 | 8192 / 384 | default | 2.25 | 2.456GiB / 15.34GiB |
| val-llama | a80c4f17acd55265feec403c7aef86be0c25983ab279d83f3bcd3abbcb5b8b72 | Q4_K_M | 0 | 8192 / 384 | default | 2.92 | 3.015GiB / 15.34GiB |
| val-qwen3-instruct | 0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0 | Q4_K_M | 0 | 8192 / 384 | False | 3.62 | 3.714GiB / 15.34GiB |
| val-uncertainty | 357c53fb659c5076de1d65ccb0b397446227b71a42be9d1603d46168015c9e4b | Q4_K_M | 0 | 8192 / 384 | default | 2.25 | 2.551GiB / 15.34GiB |
| val-workflow | 357c53fb659c5076de1d65ccb0b397446227b71a42be9d1603d46168015c9e4b | Q4_K_M | 0 | 8192 / 384 | default | 2.25 | 2.447GiB / 15.34GiB |

Development screens intentionally emphasize historical failures and are not comparable to the complete Phase-2 average. Early screens overlapped a model download; model latency comparisons use the later validation/final runs without downloads. Each experiment has a separate actual-output seal, source commit/hash, prompt/configuration, warm-up record, model identity, and memory snapshot.

## Selection and final evidence

Selected validation experiment: **val-baseline**.
Recipe: `{"context_strategy": "full_policy_document", "host": "127.0.0.1", "model": "qwen2.5:3b", "options": {"num_ctx": 8192, "num_predict": 384, "num_thread": 4, "seed": 42, "temperature": 0}, "policy_path": "data/company-policies.md", "port": 8000, "prompt_version": "baseline", "service_url": "http://127.0.0.1:11434", "timeout_seconds": 180}`.
Frozen at 2026-11-15T12:48:32.001531+00:00. Selection order: critical failures; request failures; truncated outputs; number of violated Correct/Unsupported/latency targets; descending Correct count; Unsupported count; mean latency; loaded-model bytes.
No candidate met the predeclared minimum of two additional Correct validation cases without more critical or Unsupported outcomes.

## Engineering targets and uncertainty

Phase-3 engineering targets are Correct ≥85%, Unsupported ≤3%, zero critical failures, mean latency ≤10 seconds, and at least 100 cases. The original Phase-1/2 business-quality target was 90% Correct; the historical reports keep that threshold. Meeting either target set provisionally does not authorize deployment.

Nominal Wilson intervals assume independent Bernoulli observations and condition on the provisional labels. The questions are a nonrandom agent-authored set within the same fictional handbook; the intervals are illustrative uncertainty summaries, not validated population-accuracy guarantees. The same agent authored references and reviewed outputs. No independent human validation or reviewer agreement is claimed.

Loaded-model bytes come from Ollama /api/ps, while container memory is separately sampled with docker stats. Neither is a guaranteed process-RSS/VRAM peak. CPU execution, four inference threads, seed 42, nominal temperature 0 and Q4_K_M quantization are documented in the individual records. Context/temperature ablations are explicitly identified; models have different tokenizers and the same token cap does not mean the same word budget. Warm-up/cold loading is recorded separately and excluded from timed case means.

The full handbook fits the context window. Retrieval was not added: the observed failures primarily involve interpretation, instruction following and omitted workflow details, and section retrieval could omit cross-policy requirements. This is a feasibility-based scope decision, not an unmeasured claim that retrieval would perform worse.

**Deployment recommendation: NO-GO pending adequate independent human review, broader representative/adversarial coverage, operational controls and approval.** Continue development according to the observed improvement/regression evidence; no production rollout or real employee outcome is claimed.

## Improvement and regression examples on the original exposed cases

