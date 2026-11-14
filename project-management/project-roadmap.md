# Proposed four-week delivery roadmap

This is a **proposed delivery schedule** for a hypothetical small-business pilot, not the actual duration of the portfolio build. Fictional roles describe needed responsibilities, not people who participated. Effort is an assumption in person-hours; elapsed weeks include review waits. Total proposed effort is 112 hours, consistent with the budget.

| Week | Focus | Proposed work and exit evidence | PM / Engineer / QA hours |
|---|---|---|---|
| 1 | Discovery and planning | Confirm policy boundaries, stakeholders, information risks, success gates, charter, risk register, and case taxonomy. Exit: approved requirements and policy-owner review. | 16 / 4 / 4 |
| 2 | Development | Implement validation and reports, prepare the 30-case baseline, configure Label Studio, and connect an actual assistant only in a future separately scoped phase. Exit: traceable dataset and working offline pipeline. | 8 / 24 / 4 |
| 3 | Testing and review | Validate data, run regression tests, review all cases, independently annotate actual model outputs if available, adjudicate disagreement, and retest critical issues. Exit: reproducible quality evidence and defect triage. | 8 / 20 / 8 |
| 4 | Decision and handover | Compile decision pack and cost/risk update, review proposed operating controls, and decide no-go or authorize a bounded pilot subject to all gates and sign-offs. Exit: recorded decision and next-action owners. | 8 / 0 / 8 |

Dependencies: approved policy content precedes reference answers; rubric precedes review; labels must freeze before decision reporting. Real-model testing depends on a separately available model and approved data-handling route. Label Studio availability is optional for the offline process and must never block report generation.

The current portfolio implements the offline artifacts and simulated evaluation. It has not completed the hypothetical stakeholder approvals, independent annotation, real-model testing, or deployment. A missed critical gate moves the deployment decision to no-go and schedules remediation; it does not trigger silent scope expansion or relaxed targets.
