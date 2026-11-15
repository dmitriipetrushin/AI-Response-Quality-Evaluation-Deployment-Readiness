# Phase 2 implementation plan — real local-model integration

**Owner:** Dmitry Petrushin. Independent, AI-assisted portfolio simulation. Northstar and all business stakeholder roles are fictional; no client engagement or staffed project team is claimed.

## Why extend the original pilot?

The original 30 synthetic answers established a QA process and demonstrated failure handling. They could not establish whether a real assistant could answer the policies. Phase 2 adds actual local-model inference, an interactive application, a versioned batch run of the unchanged questions, and explicitly provisional review. It preserves the synthetic responses, evaluation labels, and Git history.

## Objectives and approach

Use Qwen2.5 3B through the official Ollama runtime, on CPU, with a model download below approximately 3 GB. The application and evaluation share one `PolicyAssistant`. Every request includes the complete fictional handbook in a grounded system prompt and the employee question as a separate user message. Reference answers, acceptance labels, and synthetic candidate answers are never sent to the model. This is full-context prompting, not RAG: no retrieval or embedding system is implemented.

Configuration is in `config/assistant.json`. Defaults use temperature 0, seed 42, 8,192 context tokens, a 384-token output cap, four inference threads, and a 180-second model-request timeout. Before inference, `/api/show` must establish that the configured window is within the selected model's native limit. Actual prompt-token counts and output-limit stop reasons are retained for review. Seed and temperature improve repeatability but cannot guarantee byte-identical regeneration across runtime or hardware changes.

The loopback web application accepts a question, calls the model, and displays the exact answer, checked policy IDs, model identifier, and inference time. Cited sections are available for inspection. Identifier validity is checked mechanically; whether the text supports each statement remains a substantive review task. Unknown identifiers remain visible in the exact answer and are flagged separately. The interface runs on `127.0.0.1` by default, has bounded input and concurrency, and does not execute commands from questions.

## Dependencies and milestones

| Milestone | Dependency | Evidence required |
|---|---|---|
| M1: preserve and inspect | Existing checkout | Clean initial Git state, original test log, original input fingerprints, hardware inventory |
| M2: establish inference | Docker or installed Ollama, disk/RAM, initial internet download | Model digest and configuration, two required nonempty actual responses, native context metadata |
| M3: shared assistant and UI | Approved fictional handbook and M2 | Prompt/client tests, live API answer, actual browser interaction and screenshot |
| M4: batch evaluation | Same assistant path and original case set | 30 attempted requests, raw outputs or explicit failures, timings and hashes, atomic checkpoints |
| M5: provisional review and reports | Frozen batch outputs | Case-by-case agent-assisted labels and rationales, separate CSV and report, original gates without relaxed thresholds |
| M6: review preparation and handover | M5 | Separate Label Studio tasks/project where feasible, phase-2 management pack, startup instructions, final tests, local commit |

Roles such as QA reviewer, policy owner, security lead, Finance approver, and sponsor describe responsibilities for a future business project; they did not participate here. The four-week roadmap in Phase 1 remains a hypothetical schedule, not the duration of this build.

## Success and release decisions

Implementation completion requires genuine inference, a working local UI, at least two required live checks, all 30 questions attempted, preserved raw outputs, accurate reports, passing tests, and updated documentation. A request failure is recorded without any synthetic replacement. Assistant readiness uses the original gates (Correct ≥90%, Unsupported ≤5%, zero critical failures, full review coverage). Provisional labels cannot establish production readiness, even if all gates pass. Any unmet implementation criterion must be disclosed as incomplete; any critical quality failure leads to no-go.
