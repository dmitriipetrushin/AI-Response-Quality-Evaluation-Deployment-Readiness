# Phase 2 completion record

**Status: Complete** · **Project:** `/home/user/PortfolioProject1` · **Owner:** Dmitry Petrushin. Independent, AI-assisted portfolio simulation. Original Git history and synthetic inputs are preserved.

## Delivered and verified

A genuine local Qwen2.5 3B model runs through Ollama, with a reusable Python client, full-handbook prompting, checked policy IDs, timing/model metadata, connection/timeout handling, and a responsive loopback web application. One startup command handles model-service readiness and the application without source edits. Model selection, local URL, generation settings, and timeouts are configurable.

The actual-run dataset contains all 30 original questions, unchanged, with 30 successful model outputs and no request failures. Exact Ollama content, digest, options, prompt and policy hashes, token counts, durations, and raw API responses are retained. The original synthetic candidates and evaluation CSV were not overwritten. A separate CSV contains 30 provisional agent-assisted judgments with rationales and response hashes.

The dashboard shows clearly separate synthetic and real datasets and links to the interactive assistant. Real-run Markdown, HTML, JSON metrics, unannotated Label Studio tasks/configuration, management plans/risks/criteria/status, README, and case study were added or extended. No external publishing occurred.

## Actual tests and inference evidence

| Check | Result | Evidence |
|---|---|---|
| Original suite before edits | 28 tests passed | [Original test output](phase-2-evidence/original-tests.txt) |
| Complete unit suite | 65 tests passed; original tests included | [Unit test output](phase-2-evidence/unit-tests.txt) |
| Explicit live integration | 1 test passed, 2 genuine inference requests | [Live test output](phase-2-evidence/live-integration-test.txt), [raw live answers](phase-2-evidence/live-inference.json) |
| Exact 30-case batch | 30 attempted, 30 successful, 0 failed | [Batch log](phase-2-evidence/batch-inference.txt), [actual answers](../data/real-model-responses.json) |
| Interactive application | HTTP 200 with a real model answer, metadata, and expandable source | [Browser assertions and actual response](phase-2-evidence/browser-verification.json) |
| Missing-model error | Expected HTTP 503 displayed in browser | [Negative-path evidence](phase-2-evidence/model-unavailable-browser.json) |
| Combined dashboard | Both datasets and all 30 original case sections verified | [Browser output](phase-2-evidence/browser-verification.txt) |
| Label Studio actual-answer import | 30 answers verified, new project 6, existing IDs preserved, zero annotations | [Browser/API evidence](phase-2-evidence/browser-verification.json) |
| Final artifact/provenance/secret checks | Recorded command results and bounded scan | [Final verification](phase-2-evidence/final-verification.json), [log](phase-2-evidence/final-verification.txt) |

There are **33 saved successful real-inference requests** across the batch, explicit live test, and UI check. Default unit tests use mocks and are not counted as inference. Original input hashes, environment resources, and original commit are in [preflight evidence](phase-2-evidence/preflight.json). Runtime setup initially exposed a transient connection reset during startup; it was fixed with explicit connection-error handling and a regression test before the successful setup. This did not require a different model or any synthetic replacement.

## Actual provisional quality result

**Correct: 46.7% (14/30). Unsupported: 6.7% (2/30). Critical failures: 0 observed. Review coverage: 100.0% (30/30).** The remaining labels are 13 Partially correct and 1 Incorrect. Mean successful batch latency was **4.89 seconds**; maximum was **15.80 seconds**. The earlier cold integration request took **46.04 seconds**.

The recommendation is **NO-GO** because two proposed gates fail. All labels remain provisional agent-assisted judgments, not independent human annotations. Review boundaries and borderline classifications are documented in [review notes](../quality-assurance/phase-2-review-notes.md). No business pilot, production deployment, human approval, employee adoption, savings, or ROI is claimed.

## Genuine screenshots

- [Desktop assistant with actual answer](phase-2-evidence/assistant-desktop.png).
- [Mobile assistant with actual answer](phase-2-evidence/assistant-mobile.png).
- [Combined results dashboard](phase-2-evidence/combined-dashboard.png).
- [Separate Label Studio real-answer project](phase-2-evidence/label-studio-real-model.png).
- [Actual missing-model error state](phase-2-evidence/assistant-model-missing.png).

Chrome 157.0.8103.78 captured these local application images. No screenshots were fabricated. The assistant made no external requests during the captured application flow, no page errors were captured, and the mobile page had no full-page horizontal overflow. The Label Studio flow checked actual imported answers rather than treating prepared JSON/XML as runtime proof.

## Running again and limitations

From the project directory, run `python3 scripts/start_assistant.py --open` to reuse the installed model, or include `--setup-model` for first-time setup. The default application URL is `http://127.0.0.1:8000`. Full [startup and evaluation instructions](../docs/local-model-setup.md) describe prerequisites, configuration, replay, and shutdown. The owned web preview and demonstration containers are stopped after verification; the model cache and Label Studio demo data remain local. No credentials, model weights, or runtime database are committed.

Independent human review, larger representative/adversarial testing, production controls, latency targets, monitoring, and business sign-off remain future prerequisites. A local implementation and zero critical findings in this small sample do not establish production readiness. **Required human actions to complete the requested build: none.** Launching the application is a normal usage step; a real business deployment requires a separate approval process.
