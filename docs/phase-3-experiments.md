# Phase 3: reproduce and review the experiments

Phase 3 uses actual local Ollama inference and **provisional agent-assisted quality reviews**. The default application recipe is frozen in `experiments/phase-3/selection.json` after validation. Deployment remains **NO-GO** pending independent human validation and resolution of observed quality failures. The [comparison report](../reports/phase-3-comparison.md) is generated from sealed response/review files.

## Environment and startup

The core application, runner, reports and unit tests use Python's standard library. The measured environment is Linux, Python 3.12.3, an Intel Core i5-13420H with 12 logical CPUs, about 15.34 GiB RAM and CPU-only inference. Four inference threads were configured. These times do not predict performance on another computer. `reports/phase-3-evidence/preflight.json` records initial available memory/disk and historical checksums.

Ollama 0.40.16 is provided by the pinned Docker image in `config/ollama-image.txt`. Cached weights and optional Label Studio state are ignored local runtime data, not Git deliverables. No paid API, model training, embedding service or external knowledge source is used.

```bash
python3 scripts/start_assistant.py --setup-model --open
```

This starts/checks the loopback Ollama service and downloads only an explicitly permitted small model if absent. It serves the selected profile at `http://127.0.0.1:8000`. Use `--model-only` to prepare the service without serving the app. Cached installation:

```bash
python3 scripts/start_assistant.py --open
```

The explicit rollback starts the original model, prompt and settings:

```bash
python3 scripts/start_assistant.py --config config/assistant-baseline.json --open
```

Stop an already running app before starting another on port 8000. The old batch CLI intentionally defaults to the baseline regardless of the selected app profile. Pass a new output path to preserve historical evidence:

```bash
python3 scripts/evaluate_real_model.py --output data/phase-3/my-baseline-replay.json
```

## Frozen inputs and actual model identity

The expanded dataset is `data/phase-3/dataset/`: 40 development, 30 validation and 30 held-out cases, 100 total. The original 30 cases are unchanged development copies. Every added case has a policy reference or an explicit absence scenario, expected behavior, reference answer, acceptance criteria, category, difficulty and risk severity. All new references require independent human validation. The handbook itself is a fictional authored authority, not a source of employment-law advice.

`manifest.json` fingerprints the unchanged handbook, original cases, all splits and five prompt files. Normalized questions and scenario groups are disjoint between splits; this is a check against accidental duplicates, not proof of independence between policy concepts. The same agent authored the data and reviewed outputs. Held-out questions were authored after prompts froze, then withheld from experiment execution until selection; this is a question holdout, not an independently blind third-party benchmark. No prompts were retuned using validation or held-out answers.

The three comparable model identifiers are `qwen2.5:3b`, `qwen3:4b-instruct-2507-q4_K_M` and `llama3.2:3b`, all Q4_K_M. Two upstream families are represented (Qwen and Llama). Exact digests, artifact sizes, native/configured contexts and runtime metadata are retained in actual responses. Tags can move; reproduce the recorded digest rather than assuming a tag is immutable. Ollama `/api/show` identified the Qwen3 instruct weights as Apache 2.0 and Llama as the Llama 3.2 Community License. See [attribution](../THIRD_PARTY_NOTICES.md).

The generic `qwen3:4b` tag was separately downloaded and compatibility-probed. Its current metadata exposed thinking-only operation, and a real cold probe took 116.6 seconds despite requesting `think:false`. It was excluded from the matched benchmark; its single-question probe is not model-comparison accuracy. The explicit instruct variant resolved that compatibility problem. Current official references: [Qwen3 tags](https://ollama.com/library/qwen3/tags), [Llama 3.2 3B](https://ollama.com/library/llama3.2:3b), [structured outputs](https://docs.ollama.com/capabilities/structured-outputs), [thinking controls](https://docs.ollama.com/capabilities/thinking).

To prepare comparison weights on a fresh machine, first prepare Ollama, then run:

```bash
python3 scripts/prepare_phase3_models.py
```

This permits the three named small artifacts and rejects a layer over 3 GB. No GPU allocation or peak-VRAM measurement is claimed.

## Experiment commands

```bash
python3 scripts/phase3_experiments.py validate-dataset
python3 scripts/phase3_experiments.py run --id my-dev-screen --prompt instruction-focused --screen
python3 scripts/phase3_experiments.py run --id my-validation --model llama3.2:3b --prompt policy-workflow --split validation
python3 scripts/phase3_experiments.py compare val-baseline val-workflow val-uncertainty val-qwen3-instruct val-llama
```

Optional flags include `--context`, `--temperature`, `--output-tokens` and `--resume`. Each ID is an immutable experiment namespace. A sealed run cannot be appended to or replaced. An interrupted run can resume only with identical data, prompt, configuration and inference source; it skips saved responses. Use a new ID for a different recipe. Errors are saved as errors, without substituted answers. Prompts, reference answers and review labels are never looked up as benchmark-specific answer templates.

Baseline options are temperature 0, seed 42, context 8,192, output cap 384 and four threads. The context ablation used 4,096; the temperature ablation used 0.3. The Qwen3 instruct comparison requests non-thinking operation. Five prompts cover original instructions, instruction emphasis, uncertainty handling, workflow completeness and JSON-schema output. The structured variant renders its natural-language `answer` in the app and stores the exact generated JSON separately. One format-repair retry is permitted for an invalid contract; ordinary semantic mistakes and unknown citations do not trigger retries. Empty answers, malformed transport and incomplete runtime responses fail explicitly; output-limit stops remain visible with a warning.

`protocol.json` predeclares the 12-case failure-focused development screen, same-30-case validation comparison and selection rule. Two amendments were recorded before validation started: a minimum gain of two Correct validation cases with no increase in critical/Unsupported outcomes, and output reliability ahead of semantic count. Selection ranks critical failures, request failures, truncated outputs, number of violated quality/latency targets, Correct count, Unsupported count, latency and loaded-model bytes. The minimum-gain fallback retains baseline if an alternative does not qualify; this is a practical rule, not statistical significance.

Only after every validation response has a sealed provisional review can selection freeze:

```bash
python3 scripts/phase3_experiments.py select val-baseline val-workflow val-uncertainty val-qwen3-instruct val-llama
```

The committed selection already exists: this command deliberately refuses to overwrite it. Rebuilding the whole study with new prompts/data requires a new versioned study directory or isolated copy and fresh protocol, not editing these historical artifacts. Held-out and all-case runs require the exact frozen selected recipe with `--purpose final`, or the fixed original recipe with `--purpose baseline-control`. Use new IDs for replays; the report deliberately designates `final-selected` and `final-baseline-heldout` as canonical final evidence so a replay cannot silently replace them.

## Review and metrics

The output cap was monitored rather than increased indiscriminately. The original 30 baseline outputs stopped normally; incompleteness was not caused by reaching the cap. The workflow prompt later produced repeated/checklist text and a cap stop. Allowing still more tokens would not directly address that observed instruction-following problem and would increase the latency budget. No unmeasured claim about a larger cap improving quality is made. Top-p stayed at the artifact/runtime default; the explicitly changed settings and the captured model defaults are in the evidence.

Every experiment stores `experiment.json` (timestamp, Git commit, source hashes, dataset/prompt/configuration), a separate real warm-up, append-only `responses.jsonl`, runtime snapshot and SHA-256 seal. Response records include exact raw content, token counts, stop reason, attempts and measured wall time. Reviews are separately sealed CSVs bound to the exact natural answer hash. `write_reviews` rejects unsupported labels, duplicate case IDs, invalid criticality and overwrites. No hidden semantic judge, keyword pass-rate or independent reviewer is implied.

The rubric precedence is contradiction → Incorrect; otherwise material unsupported claim → Unsupported; otherwise material omission → Partially correct; otherwise Correct. Criticality is a separate flag for a serious weakened security/privacy/financial control. A case's potential risk severity does not mean every imperfect answer is a critical incident. Minor formatting and irrelevant citations can be recorded alongside semantic correctness; truncation is separately measured and penalized in selection. Borderline cases need human adjudication. The [review guide](../label-studio/phase-3-review-guide.md) explains the independent workflow.

Correct/Unsupported percentages use every attempted case as denominator, and review coverage is explicit. Error records cannot become Correct. Mean, median and nearest-rank P95 are measured case wall times; model warm-up is excluded and stored separately. The original reproduction included a cold first request, so its timing is not a matched warm-latency estimate. Early development screens overlapped downloads; later validation/final runs did not. The host is a shared desktop, not a controlled performance laboratory; ordinary host activity and caching can affect timing. Only one timed inference stream ran at once; the app and Label Studio checks ran after benchmarks.

Loaded-model bytes come from `/api/ps`; container memory comes from `docker stats`. They are snapshots, not peak process RSS or peak VRAM. All models receive the same handbook and cap/settings, but tokenizers and model templates differ. Nominal Wilson 95% Correct intervals condition on provisional labels and independent Bernoulli observations. A nonrandom authored sample with shared-policy scenarios does not support population-accuracy guarantees. The pooled 100 includes exposed development/validation cases; compare the same 30 held-out questions separately, and compare the original 30 only as exposed development evidence.

## Reports, tests and annotation tasks

```bash
python3 scripts/phase3_reports.py
python3 scripts/generate_report.py
python3 scripts/phase3_label_studio.py
python3 -m unittest discover -s tests -v
python3 -S -m unittest discover -s tests -v
python3 -m unittest tests.integration_real_model tests.integration_phase3 -v
python3 scripts/verify_project.py
python3 scripts/verify_phase2.py
python3 scripts/verify_phase3.py
```

The two explicit integration tests require running Ollama and generate new Phase-3 evidence, preserving Phase-2 evidence. Reports are deterministic given the sealed artifacts. Open `reports/dashboard.html` for all phases or `reports/phase-3-dashboard.html` for model/prompt/split filters, category/difficulty tables, resources and paired examples. The comparison HTML works directly from disk and through the assistant server.

Label Studio is optional. Start the existing container with `docker start northstar-quality-pilot`; on a fresh installation follow the [existing setup guide](../label-studio/setup-guide.md). The Phase-3 generator creates 100 unannotated tasks containing actual final answers, source text, references and case/experiment/model/hash provenance. Provisional labels remain outside the annotation UI. With the optional Playwright environment and installed Chrome:

```bash
.venv-label-studio/bin/python scripts/verify_phase3_browser.py --label-studio
```

This verifies real browser inference, response metadata, citations, mobile layout, offline/HTTP filters and annotation controls. It creates or reuses a separate Phase-3 project, verifies all response bindings and compares exports of historical projects before/after. It submits no annotation. Evidence goes only under `reports/phase-3-evidence/`.

Stop the application with Ctrl+C and stop only the owned test containers after verification:

```bash
docker stop northstar-ollama northstar-quality-pilot
```

After stopping Ollama while the app is still running, the optional real error-path check is `.venv-label-studio/bin/python scripts/verify_phase3_browser.py --unavailable`. It checks the visible 503 error and reenabled controls without fabricating a successful answer. Then stop the app with Ctrl+C.

The caches and annotation database persist. No remote push or public deployment is part of this study.
