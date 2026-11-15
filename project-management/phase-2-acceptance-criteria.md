# Phase 2 acceptance criteria

## Implementation completion

| ID | Requirement | Verification method |
|---|---|---|
| P2-01 | Preserve Phase 1 inputs and original Git history | Original SHA-256 comparison and unchanged synthetic validation/tests |
| P2-02 | Run a genuine local model with no paid API | Ollama raw responses, token counts, model digest/runtime metadata |
| P2-03 | Complete both required live questions | Explicit integration test: annual leave and password sharing |
| P2-04 | Include sufficient real policy context | Complete handbook in prompts; native context check; observed prompt-token counts with output headroom |
| P2-05 | Provide a working loopback UI | Browser enters a question and receives an actual model answer, references, model, and duration |
| P2-06 | Handle invalid input, connection problems, and timeouts | Mocked unit tests plus visible application error handling |
| P2-07 | Attempt the unchanged 30 questions | Saved case IDs, exact question comparisons, per-request status/error and timing |
| P2-08 | Keep real outputs separate from synthetic fixtures | Dedicated response JSON, provisional-review CSV, reports and Label Studio task file |
| P2-09 | Report review status honestly | Agent-assisted provisional labels with rationale and answer hash; no human-verification claim |
| P2-10 | Preserve original dashboard functionality and add navigation | Separate synthetic/real sections, original case expansions, assistant link, browser check |
| P2-11 | Make startup reproducible without source edits | Tracked config and one Python startup command; no model weights or credentials committed |
| P2-12 | Complete actual final checks | Full unit suite, explicit live test, final verifier, baseline hashes, browser evidence, focused Git diff |

Every item is evaluated against actual saved evidence in the phase-2 completion record. Unit-test mocks cannot satisfy P2-02, P2-03, or P2-05. A model failure is retained and disclosed, and no synthetic answer can substitute for it.

## Proposed model-quality gates

Use the original rubric and precedence: contradiction → Incorrect; otherwise a material unsupported claim → Unsupported; otherwise an important omission → Partially correct; otherwise Correct. Critical failure remains a separate boolean.

| Metric | Target for the same 30 cases |
|---|---|
| Correct | At least 90%, or 27 cases |
| Unsupported | At most 5%, or at most 1 case |
| Critical failures | Zero |
| Evaluation coverage | 100%, or all 30 cases reviewed |

Rates use all 30 expected cases as denominator. A failed inference is not classified as a semantic answer and remains unreviewed. If review is incomplete, unreviewed correctness and criticality are unknown; relevant gates remain pending rather than silently passing. A critical failure blocks release regardless of aggregate score. Passing provisional gates still results in hold pending independent human review, expanded coverage, latency criteria, and business/security approval. Failing complete provisional gates supports a no-go recommendation.

## Evidence boundaries

The synthetic fixtures are intentionally mixed examples and are not a model-performance benchmark. Differences from real-model scores must not be called measured improvement. Actual inference, automated tests, agent-assisted review, independent human review, and business deployment are separate claims. This project must not infer one from another.
