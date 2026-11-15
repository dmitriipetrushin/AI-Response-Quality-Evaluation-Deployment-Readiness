# Phase 3 completion report

**Status: Complete — engineering/evaluation deliverables. Quality targets not met.**

Project: `/home/user/PortfolioProject1`. Selected application recipe: **`qwen2.5:3b`, Q4_K_M, original baseline prompt**, temperature 0, seed 42, context 8,192, output cap 384, four threads. All quality labels are **provisional agent-assisted reviews**, without independent human validation. **Deployment recommendation: NO-GO.** No optimization gain is claimed.

## Measured result

| Metric | Historical Phase 2 | Phase 3 selected profile |
|---|---:|---:|
| Correct | 46.7% (14/30) | 48.0% (48/100) |
| Unsupported | 6.7% (2/30) | 3.0% (3/100) |
| Critical failures | 0 observed | 3 provisional findings |
| Mean latency | 4.89 s | 5.40 s |
| Cases | 30 | 100 |

**Different case sets:** the pooled 100 includes development and validation examples exposed during experimentation. These columns do not measure optimization improvement. All original 30 selected-profile answers remain byte-identical to historical outputs; their 14 Correct, two Unsupported and zero-critical labels are unchanged. The initial reproduction also matched all 30 answers, with a cold-inclusive 6.11-second mean that is not a matched warm-speed comparison.

| Matched held-out comparison | Correct | Unsupported | Critical | Mean / median / P95 seconds |
|---|---:|---:|---:|---|
| Selected retained baseline, 30 cases | 12/30 (40.0%) | 0/30 | 1 | 4.63 / 4.10 / 7.86 |
| Separate original-baseline control, same 30 cases | 12/30 (40.0%) | 0/30 | 1 | 4.67 / 3.95 / 8.09 |

All 30 held-out outputs match between those two actual runs. The small timing difference is normal runtime variation, not a claimed speed gain. The nominal Wilson 95% Correct interval is **24.6–57.7%**, conditional on provisional labels and independent Bernoulli assumptions. Authored, nonrandom, shared-policy questions do not justify population-accuracy or rare-event-safety guarantees.

The final 100 labels are **48 Correct, 36 Partially correct, 13 Incorrect, three Unsupported**, with mean/median/P95 **5.40/4.26/12.62 seconds**, no failed transport requests and one flagged output-limit stop. No ambiguous case was fully Correct (0/19); omissions and interpretation remain major weaknesses. Category/difficulty results appear in the [comparison](phase-3-comparison.md) and [dashboard](phase-3-dashboard.html).

| Phase-3 engineering target | Result | Outcome |
|---|---|---|
| Correct ≥85% | 48.0% | Fail |
| Unsupported ≤3% | 3.0% | Pass provisionally |
| Zero critical failures | 3 | Fail |
| Mean latency ≤10 s | 5.40 s | Pass |
| At least 100 cases | 100 attempted, generated and reviewed | Pass |

The new benchmark exposes critical generated advice in **P3-D-004** (tax ignored and Finance approval explicitly bypassed), **P3-V-018** (weaker external-sharing authorization) and **P3-T-010** (equipment route replaced without mandatory IT approval). These are judgments about potential exposure from answers, not actual purchases, disclosures or harm. Their exact outputs/rationales are available in the comparison and sealed [final reviews](../experiments/phase-3/final-selected/reviews.csv).

## Experiments and selection

Fourteen sealed experiments preserve **364 real case attempts**, plus separately recorded warm-ups. The initial 30-case reproduction and one generic-Qwen3 compatibility probe are separate evidence, not added to those experiment denominators. Five prompts were compared on a 12-case development screen; context 4,096 and temperature 0.3 were tested as single-setting ablations. The full same-30 validation comparison includes:

| Configuration | Correct / 30 | Unsupported | Critical | Mean s |
|---|---:|---:|---:|---:|
| qwen2.5:3b / baseline | 20 | 0 | 1 | 7.74 |
| qwen2.5:3b / policy-workflow | 14 | 3 | 1 | 11.04 |
| qwen2.5:3b / uncertainty-aware | 19 | 0 | 1 | 6.39 |
| qwen3:4b-instruct-2507-q4_K_M / policy-workflow | 23 | 3 | 0 | 26.20 |
| llama3.2:3b / policy-workflow | 14 | 1 | 0 | 9.15 |

Matched comparison models are **`qwen2.5:3b`**, **`qwen3:4b-instruct-2507-q4_K_M`** and **`llama3.2:3b`**, all Q4_K_M, representing Qwen and Llama upstream families. Generic **`qwen3:4b`** was compatibility-probed only: current thinking-only behavior did not provide the intended matched mode. Model digests, quantization, settings and resource snapshots are retained in every run. Official tag/capability references and licenses are linked in the [guide](../docs/phase-3-experiments.md) and [attribution](../THIRD_PARTY_NOTICES.md).

Selection was frozen using validation only, before held-out inference. The predeclared replacement gate requires two additional Correct cases without more critical or Unsupported outcomes. It is a hard gate after ranking, not a statistical-significance test. It retained baseline even though Qwen3 had zero sampled critical failures: Qwen3 introduced three Unsupported answers and averaged 26.2 seconds. Retention is not an endorsement of baseline safety. The structured-output profile, reduced context and temperature change were not adopted as defaults. The report shows same-prompt Qwen2.5/Qwen3 validation examples of both improvement and regression, explicitly distinguished from selected-profile gains.

The dataset contains **40 development / 30 validation / 30 held-out cases** with stable IDs, policy evidence, authored references/criteria, category, difficulty and risk severity. The original 30 are unchanged development copies. Prompts and splits are fingerprinted; held-out execution was locked until selection, and no prompts/settings were retuned after it. The same agent authored new references and reviewed outputs. This is a question holdout within a fictional handbook, not an independently blind benchmark.

## Delivered implementation

- [Frozen 100-case manifest](../data/phase-3/dataset/manifest.json), [machine-readable baseline failure analysis](phase-3-failure-analysis.json) and [readable analysis](phase-3-failure-analysis.md).
- Five versioned prompts, controlled ablations, three comparable model configurations, [protocol](../experiments/phase-3/protocol.json) and [immutable selection](../experiments/phase-3/selection.json).
- Reproducible CLI, exact raw outputs/attempts, source and answer hashes, separate provisional reviews, response/review/resource seals, checkpoint/resume guards and explicit error records.
- Strict optional JSON contract and at most one technical format-repair retry. Plain answers are not retried for semantic quality. Structured output was rejected as the default after its measured failures.
- Existing assistant UI with active profile display, maintained startup/rollback, inspectable actual citations, understandable runtime errors and a separate offline comparison view.
- [JSON metrics](phase-3-metrics.json), [CSV comparison](phase-3-comparison.csv), category/difficulty breakdowns, model resources, critical examples and candidate improvements/regressions. Original synthetic and Phase-2 evidence remains accessible.
- A separate Label Studio project and [review guide](../label-studio/phase-3-review-guide.md), [review notes](../quality-assurance/phase-3-review-notes.md), updated README/portfolio and [detailed case study](../portfolio/phase-3-case-study.md).

The full 2,019-word handbook fits in context. Retrieval infrastructure was not added without a demonstrated need; no unmeasured RAG performance claim is made. The inference code does not branch on benchmark IDs, retrieve reference answers or substitute canned model replies.

## Executed verification

| Check | Actual outcome | Evidence |
|---|---|---|
| Complete unit suite | **88 passed** | [Log](phase-3-evidence/unit-tests.txt) |
| Site packages disabled | **88 passed** with `python3 -S` | [Log](phase-3-evidence/unit-tests-stdlib-only.txt) |
| Explicit real Ollama integration | **2 tests passed**, four actual questions, original and selected profiles | [Log](phase-3-evidence/live-integration-tests.txt) |
| Real selected-model records | Actual raw outputs/token counts retained | [Selected live evidence](phase-3-evidence/selected-live-inference.json) |
| Actual browser application | Passed real inference, model/profile/time, policy expansion, input error, desktop/mobile | [Browser evidence](phase-3-evidence/browser-verification.json) |
| Comparison dashboard | Passed file/HTTP execution, filters, empty filter state, category/difficulty and mobile overflow checks | [Browser log](phase-3-evidence/browser-check-log.txt) |
| Actual stopped-model browser path | **HTTP 503**, visible guidance, controls reenabled, no fabricated answer | [Error-path evidence](phase-3-evidence/unavailable-browser-verification.json) |
| Historical artifacts | **13 original files byte-preserved**, 30 identical reproduction answers | [Artifact verification](phase-3-evidence/artifact-verification.json) |
| Legacy project and Phase-2 checks | Passed after documentation completed | [Project log](phase-3-evidence/legacy-project-verification.txt), [Phase-2 log](phase-3-evidence/legacy-phase2-verification.txt) |
| Frozen inputs, seals, final task bindings, derived report consistency | Passed | [Artifact check](phase-3-evidence/artifact-check-log.txt) |
| Common credential patterns | No matches in tracked/unignored text | [Scan](phase-3-evidence/credential-pattern-scan.json) |
| Owned services | Stopped; ports 8000/8087/11434 closed | [Teardown](phase-3-evidence/teardown.json) |

The final test suite has no failures. Two initial browser-harness failures were resolved: Label Studio limits project titles to 50 characters, and severity controls use alphabetic shortcut labels. Their original [title error](phase-3-evidence/browser-initial-title-failure.txt) and [selector error](phase-3-evidence/browser-initial-selector-failure.txt) logs remain available. Neither changed benchmark data or quality labels. An optional Node CLI syntax probe was unavailable because Node is not installed; actual JavaScript execution/filter behavior passed in Chrome 157.0.8103.78. No Node dependency was added.

Genuine screenshots: [assistant desktop](phase-3-evidence/app-desktop.png), [assistant mobile](phase-3-evidence/app-mobile.png), [comparison desktop](phase-3-evidence/comparison-desktop.png), [comparison mobile](phase-3-evidence/comparison-mobile.png), [Label Studio](phase-3-evidence/label-studio-phase3.png), [model unavailable](phase-3-evidence/app-model-unavailable.png). Screenshots come from the actual browser; no generated mockups are used.

## Label Studio and preservation

Label Studio **1.23.0**, separate **project 7**, contains **100 actual final answers**, verified against source response hashes and experiment/case/model identity. There are **zero submitted annotations and zero tasks with annotations**. Classification, criticality, failure-reason, severity and comment controls render. Project IDs 1–6 remain present, with matching fingerprints of project title/description/config and exported task IDs/data/annotations/predictions before and after successful verification. Dynamic timestamps are excluded from those content fingerprints. Successful reruns reuse the new project to avoid duplicate imports.

The 100 final reviews comprise **60 exact-question/exact-answer reuses** of existing provisional judgments and **40 new substantive provisional judgments**; the held-out control reuses the same 30 reviewed answers only after exact equality checks. [Final review provenance](phase-3-evidence/final-selected-review-provenance.json) and [control provenance](phase-3-evidence/final-control-review-provenance.json) distinguish this from independent reviewer agreement. Imported tasks do not contain these labels as annotations or predictions. Independent policy/reference validation, answer review and adjudication remain future work.

## Hardware, reproducibility and handover

Measured environment: Intel Core i5-13420H, 12 logical CPUs, approximately 15.34 GiB RAM, CPU inference, four configured threads, Python 3.12.3 and Ollama 0.40.16. The selected disk artifact is approximately 1.93 GB; its recorded loaded-model footprint is about 2.25 GiB and final container usage about 2.35 GiB. These are snapshots, not peak RSS/VRAM or minimum system requirements. Alternative artifacts are under 3 GB each. No GPU allocation, paid API or new mandatory Python dependency is required.

Canonical final benchmark inference source commit: `c1006636312a78d39603ec55f9be4b63d88b767c`; inference source hashes are also recorded in each experiment. The final delivery commit is the repository HEAD after the completion commit and is reported in the handover message; it is not embedded self-referentially in this file. Completed changes are committed locally. **No remote push or public deployment occurred.**

Start using the cached local model:

```bash
cd /home/user/PortfolioProject1
python3 scripts/start_assistant.py --open
```

First-time setup adds `--setup-model`. Explicit historical rollback:

```bash
python3 scripts/start_assistant.py --config config/assistant-baseline.json --open
```

Read the [reproduction guide](../docs/phase-3-experiments.md) for fresh downloads, immutable replay IDs, comparison/report commands and all verification commands. The app and containers `northstar-ollama` / `northstar-quality-pilot` are stopped; model cache, container and annotation database persist for restart.

## Remaining limits and decision

The application and evaluation workflow function, but model quality is inadequate. All labels/references share authorship and need independent validation; there is no human agreement measurement, representative employee-traffic sample, production assessment or stakeholder approval. Dataset concepts overlap within the same fictional handbook despite split/duplicate checks. Quality intervals do not remove those biases. Current findings do not support adoption, cost-saving, safety or business-impact claims.

Continue with independent reference/answer review and adjudication, representative adversarial cases, better clarification/workflow behavior and controls outside the model. **NO-GO for deployment.** Technical delivery is complete; the attempted optimization did not produce a qualifying improvement.
