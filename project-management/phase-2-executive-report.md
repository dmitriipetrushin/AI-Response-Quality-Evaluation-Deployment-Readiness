# Phase 2 executive report

**Owner:** Dmitry Petrushin · **Date:** 15 November 2026 (Europe/Moscow). Independent portfolio simulation; fictional company and stakeholder roles. No client engagement, team management, business sign-off, or production rollout occurred.

**Implementation status: complete. Model-quality recommendation: NO-GO.** A real local model and working interface were delivered and tested. The 30-question run succeeded technically, but its provisional reviews fail two proposed quality gates. These are separate conclusions.

## What was implemented

Qwen2.5 3B Q4_K_M runs through Ollama 0.40.16 on CPU. The model is 1,929,912,432 bytes and has digest `357c53fb659c5076de1d65ccb0b397446227b71a42be9d1603d46168015c9e4b`. The runtime image is pinned separately. Generation uses temperature 0, seed 42, four threads, an 8,192-token context, and a 384-token output cap. Native support is 32,768 tokens. The full fictional handbook is supplied in every request; no retrieval system, embedding service, or paid API is used.

A shared Python assistant powers the loopback web application and batch evaluation. It returns exact model output, model metadata, latency, checked policy IDs, and warnings. The UI includes example questions, loading/error states, expandable cited policy text, and clear fictional-data disclosure. Separate real-output and provisional-review files preserve the original synthetic dataset and its history.

## Actual verification

The original 28 tests passed before changes. The complete current suite has **65 passing unit tests**. One explicit live integration test passed both required inference questions. The 30 original questions were attempted with **30 successes and zero failures**. Chrome submitted a real UI question, displayed the actual answer, model, duration, and cited section, and verified mobile layout without page-wide overflow or captured application page errors. An expected missing-model HTTP 503 was also verified in the browser before installation completed.

In total, saved evidence records **33 successful real inference requests**: 30 batch answers, two live integration answers, and one UI answer. Metadata and health requests are not counted as inference. These are actual outputs, not authored fixtures or mocked unit replies.

Label Studio 1.23.0 accepted all 30 actual answers in **new project 6**, preserving existing projects 1–5. The API-imported answer text and source were checked for every task, and the real-answer interface rendered in Chrome. **No annotation was submitted** and no human review is claimed. Genuine screenshots and machine-readable evidence are linked in the [phase-2 completion record](../reports/phase-2-completion-report.md).

## Results from the real run

| Proposed gate | Actual provisional result | Outcome |
|---|---|---|
| Correct ≥90% | **46.7% (14/30)** | Fail |
| Unsupported ≤5% | **6.7% (2/30)** | Fail |
| Critical failures = 0 | **0 observed** | Pass provisionally |
| Evaluation coverage = 100% | **100.0% (30/30)** | Pass provisionally |

Classifications are 14 Correct, 13 Partially correct, 1 Incorrect, and 2 Unsupported. The **mean successful batch request time was 4.89 seconds**, with a maximum of 15.80 seconds. Those sequential timings benefit from a warm model and shared prompt prefix. The earlier cold annual-leave check took 46.04 seconds; these figures are not a concurrency or response-time SLA.

Observed prompt lengths were 2,714–2,736 tokens, leaving substantial headroom within the configured context and output budget. No output-limit stop occurred. Thirteen of 30 answers contained a recognized policy ID. One answer invented `POL-008`; the application flagged it as unknown. Identifier validation did not establish citation support.

## Review integrity and limitations

Every quality judgment is `agent_assisted_review` and `provisional`, tied to the exact answer hash and run ID. No independent human reviewer, agreement measurement, holdout validation, or actual employee testing occurred. The original rubric and case acceptance criteria were reused. Review notes disclose borderline judgments, including the approval sequence in TC-011 and unsupported support routing in TC-027.

This sample showed missing clarifications and required workflow details despite fluent supported facts, plus an invented pension policy. Zero observed critical failures across 30 authored questions does not establish rare-event safety. The synthetic baseline is deliberately mixed and is not a real-model benchmark; differences between scores are not measured improvement.

## Decision and next actions

Maintain no-go for a controlled business pilot. Prioritize clarification behavior, complete approval/evidence checklists, citation grounding, and refusal/escalation routes. Evaluate revised behavior on a new versioned run rather than editing outputs. Obtain independent policy/security/Finance/QA review, adjudicate labels, expand representative and adversarial holdout cases, and define cold/warm latency targets. A hypothetical sponsor must approve any bounded pilot with monitoring and rollback ownership. Those business actions remain unperformed.

No paid API or service purchases were made. Existing compute, download bandwidth, electricity, development-session cost, and owner time were not metered; total economic cost is unknown. The original four-week schedule and budget remain hypothetical planning artifacts.
