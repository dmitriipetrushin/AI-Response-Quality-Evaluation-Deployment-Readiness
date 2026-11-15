# Running the real local assistant

This phase extends the existing portfolio; the original dependency-free synthetic evaluation still runs without a model. The real assistant uses Python's standard library and Ollama's loopback HTTP API. No paid inference API or private credentials are required.

## Prerequisites

Python 3.10+ (tested here with 3.12.3), Docker for automatic local runtime setup or an already running native Ollama service, initial internet access for downloads, and sufficient free RAM and disk. The chosen Qwen2.5 3B Q4_K_M model is approximately 1.93 GB. The separately downloaded official Ollama Docker runtime image is approximately 3.40 GB compressed; unpacking and cache storage need additional disk. Budget at least 12 GB free disk and approximately 6 GB available RAM for this small-model CPU demonstration. These are planning allowances, not measured minimum system requirements. No NVIDIA GPU was detected here; four CPU inference threads are configured.

The existing `.venv-label-studio` and Playwright are optional browser-verification tools, not application dependencies. No `pip install` is needed to run the assistant or its normal unit suite. Do not expose this demonstration publicly.

## One command to start

From the repository root:

```bash
python3 scripts/start_assistant.py --setup-model --open
```

This connects to an existing service at the configured loopback origin, or creates/starts the dedicated `northstar-ollama` container at the default `http://127.0.0.1:11434`. It downloads the selected model only if missing, checks the model's native context capacity, starts the application at `http://127.0.0.1:8000`, and asks the default browser to open it. If automatic browser opening is unavailable, use the printed URL. On later runs, `python3 scripts/start_assistant.py --open` reuses the cached model; no new weights are downloaded.

The Docker image is pinned in `config/ollama-image.txt`. Model storage stays under ignored `.runtime/ollama` in the project. Cloud features are disabled in this container with `OLLAMA_NO_CLOUD=1`; no account or cloud API is used. Host port publication is restricted to loopback. No global service, installer script, GPU driver, or system configuration change is performed.

To prepare or check only the service, without launching the UI:

```bash
python3 scripts/start_assistant.py --setup-model --model-only
```

Stop the application with Ctrl+C. Stop the dedicated model container with `docker stop northstar-ollama`; the ignored cache remains. Restart through the same startup command. Do not remove the cache if you want to avoid another model download. The container name is specific to this project; no unrelated services are stopped.

## Configuration

Edit `config/assistant.json`, not Python source, to select the model, service URL, timeouts, generation options, or application port. A separate file can be selected with `--config path/to/config.json`. The service URL and application host must remain loopback. A native Ollama install is supported if its configured endpoint is reachable. Automatic downloading is restricted to `qwen2.5:3b` and `qwen2.5:1.5b`; other compatible models must already be installed. The default model is the only one downloaded by this build.

Current defaults:

| Setting | Value |
|---|---|
| Model | `qwen2.5:3b` |
| Policy strategy | Complete handbook in every prompt; no retrieval system |
| Context window | 8,192 tokens, verified against `/api/show` metadata |
| Maximum output | 384 tokens; length stops are retained and warned about |
| Temperature / seed | 0 / 42 |
| CPU inference threads | 4 |
| Model request timeout | 180 seconds |
| UI concurrency | One inference at a time; additional requests receive HTTP 429 |
| Input limit | 2,000 characters per question; 16 KiB HTTP body limit |

The selected artifact reports a native 32,768-token context window; the application configures 8,192 tokens. Actual prompt-token counts and observed headroom are recorded in the run report. Fixed sampling does not guarantee identical outputs after a model/runtime/hardware change. Record a new run when changing generation settings or policies; the resume command rejects mismatched provenance. Model digests and exact raw responses are preserved, not inferred from tag names.

## Evaluation and reporting

```bash
python3 scripts/evaluate_real_model.py
python3 scripts/generate_real_model_report.py
```

The first command uses the exact original 30 questions, in order, through the same `PolicyAssistant` as the UI. Existing output is protected: use `--resume` to continue an interrupted run with identical configuration, or `--output data/another-real-run.json` to create a new artifact. Failed requests are retained as errors and are never replaced with authored responses. A resumed run skips already attempted records, including errors; a rerun should use a new output path. The default dashboard uses the canonical `data/real-model-responses.json` run and its matching review CSV.

`data/real-model-evaluation.csv` contains case-by-case **provisional agent-assisted review** tied to answer hashes. Labels are not created automatically by the inference pipeline and are not human-verified. On a new run, review the actual saved answers against the existing rubric and write a separate matching review CSV before treating quality metrics as assessed. A stale CSV causes report validation to fail rather than silently reuse old labels. Without a CSV, reports show unreviewed status and pending gates. The committed review represents this build's saved run only.

Report outputs are `reports/real-model-evaluation.md`, `reports/real-model-dashboard.html`, and `reports/real-model-metrics.json`. The original combined dashboard retains the synthetic baseline and adds a clearly separate real-run section. No score difference is described as measured model improvement.

## Verification

```bash
python3 -m unittest discover -s tests -v
python3 -m unittest discover -s tests -p integration_real_model.py -v
python3 scripts/verify_project.py
python3 scripts/verify_phase2.py
```

The default unit suite uses mocks for model responses and needs no running LLM. The explicit integration test needs Ollama and runs the two required real questions, preserving raw replies in `reports/phase-2-evidence/live-inference.json`. It proves inference, not semantic correctness. The phase-2 verifier checks the saved original input hashes, the exact question set, actual-output provenance, model metadata and token evidence, prompt consistency, provisional review hashes, report freshness, and task bindings.

With the optional project-local Playwright installation and existing Chrome:

```bash
.venv-label-studio/bin/python scripts/verify_phase2_browser.py --label-studio
```

Start the app and the optional `northstar-quality-pilot` Label Studio container first. The browser harness makes a real application inference request and creates a **separate** unannotated Label Studio project with real answers. It preserves existing project IDs and verifies all imported answer strings. It does not submit human annotations. See the [phase-2 executive report](../project-management/phase-2-executive-report.md) for the actual outcomes, rather than inferring success from these instructions.

## Source and license references

Official references: [Ollama Docker runtime](https://docs.ollama.com/docker), [chat API](https://docs.ollama.com/api/chat), [local-only configuration and context options](https://docs.ollama.com/faq), and [Qwen2.5 3B model artifact](https://ollama.com/library/qwen2.5:3b). The 3B artifact uses the upstream Qwen research license; it is not relicensed under this repository's MIT license. Model weights and runtime binaries are not committed. See [third-party notices](../THIRD_PARTY_NOTICES.md).
