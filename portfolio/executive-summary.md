# Executive summary

**AI Response Quality Evaluation Pilot · Dmitry Petrushin**<br>
Independent portfolio simulation for an AI Project Manager / AI Implementation Manager role. Northstar Business Services and stakeholders are fictional; no client, staffed team, or production deployment is claimed.

**Decision: NO-GO for the demonstration baseline.** A complete evaluation process was delivered, but the intentionally mixed synthetic answers fail three proposed release gates.

| Proposed gate | Actual synthetic result | Outcome |
|---|---|---|
| Correct ≥90% | **56.7% (17/30)** | Fail |
| Unsupported ≤5% | **13.3% (4/30)** | Fail |
| Critical failures = 0 | **4** | Fail |
| Review coverage = 100% | **100.0% (30/30)** | Pass |

The baseline contains 17 Correct, 4 Partially correct, 5 Incorrect, and 4 Unsupported answers. Every response is a `synthetic_fixture`, and every label is a `simulated_review`. These are not independently validated annotations or production-model accuracy results.

The delivered package includes seven fictional policy sections, 30 balanced cases, policy-linked review rationales, offline Python validation and reporting, a 28-test suite, an offline dashboard with expandable case evidence, and Label Studio tasks and configuration. The project-management pack adds a charter, proposed four-week roadmap, 21-item backlog, 14-risk register, stakeholder plan, assumed budget, QA plan, executive status, and lessons. Label Studio 1.23.0 was installed and its task-import and annotation-interface flow verified locally; no annotation was submitted.

Critical examples involve credential handling and financial-control bypasses. Before any real pilot, remediate those patterns, evaluate actual model outputs independently on broader data, rerun all gates, and require policy, sponsor, security, Finance, and QA approvals. No such business activities occurred in this simulation.

The hypothetical plan assumes 112 person-hours and a USD 9,120 ceiling including contingency; these are not actual costs or elapsed duration. The project made no paid-service purchases, while existing compute and development-session costs were not metered.

Read the [case study](case-study.md), [dashboard](../reports/dashboard.html), or [verification record](../reports/completion-report.md). The mandatory workflow needs only Python's standard library and no credentials or internet connection.

## Phase 2 update — actual model implementation

The original summary above describes Phase 1. Phase 2 added a functioning local **qwen2.5:3b** assistant, a responsive web interface, and the same 30 questions run through actual Ollama inference. All 30 batch requests succeeded. Two explicit live-check answers and a browser-submitted answer bring the saved inference evidence to 33 successful requests. The complete unit suite has 65 passing tests; the separate live integration test also passed.

Provisional agent-assisted review found **46.7% Correct (14/30)**, **6.7% Unsupported (2/30)**, **0 critical failures observed**, and **100.0% review coverage (30/30)**. Mean successful sequential batch time was **4.89 seconds**. Recommendation: **NO-GO**, because two original quality gates fail. No independent human validation or production approval is claimed, and synthetic-to-real score differences are not measured improvement.

Label Studio 1.23.0 imported all actual answers into a new project without altering existing projects or submitting annotations. The [phase-2 executive report](../project-management/phase-2-executive-report.md), [actual run report](../reports/real-model-evaluation.md), and [completion evidence](../reports/phase-2-completion-report.md) provide the decision trail. Start the app with `python3 scripts/start_assistant.py --open`; first-time setup adds `--setup-model`.
