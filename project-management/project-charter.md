# Project charter

**Project:** AI Response Quality Evaluation Pilot<br>
**Portfolio owner:** Dmitry Petrushin<br>
**Context:** Independent portfolio simulation for an AI Project Manager / AI Implementation Manager role. Northstar Business Services and all stakeholder roles are fictional. No client engagement, employment, team management, or deployment is claimed.

## Business problem

Management needs a defensible way to judge whether an internal-policy assistant could enter a controlled pilot. Fluent answers can still invent benefits, miss approvals, expose private information, or suggest unsafe financial actions. A single aggregate accuracy score hides these risks.

## Objectives

Translate the decision into explicit requirements: a policy source, balanced risk scenarios, mutually exclusive labels, separate criticality, complete review coverage, and exact acceptance gates. Deliver a credential-free offline evaluation workflow and a prepared HumanSignal Label Studio review interface. Communicate evidence and remaining uncertainty so a future sponsor can distinguish process readiness from assistant readiness.

## Scope and deliverables

Seven fictional policy sections; exactly 30 cases in five specified categories; one synthetic candidate and simulated review per case; Python validation, reporting, and automated tests; offline HTML and Markdown results; Label Studio configuration and tasks; charter, roadmap, backlog, risks, stakeholder plan, budget, QA plan, executive report, lessons, and portfolio materials. Every claim must distinguish actual build work from proposed business implementation.

Out of scope: creating or training a model, collecting real employee data, connecting enterprise systems, deploying to production, running stakeholder workshops, producing independent human annotations, measuring adoption or business ROI, and publishing the repository. Label Studio runtime setup is optional; unavailable runtime does not block the offline deliverables.

## Success and approval criteria

Portfolio completion requires all records and deliverables, valid relationships and policy references, passing automated tests, regenerated reports matching inputs, a locally opening dashboard, and honest optional-integration status. These delivery criteria are separate from the proposed assistant release criteria: at least 90% Correct, at most 5% Unsupported, zero critical failures, and 100% evaluation coverage. For 30 cases this means at least 27 Correct and at most 1 Unsupported. Never alter a label merely to pass.

A hypothetical sponsor approves scope and costs; a policy owner approves content; security and Finance approve sensitive controls; QA approves review evidence. A real pilot would require all gates and those approvals on actual model evidence. No such business approvals occurred in this simulation. The documented no-go recommendation is a completed deliverable, not a failed portfolio build.

## Stakeholder roles

| Fictional role | Proposed responsibility |
|---|---|
| Business sponsor / Operations Director | Accountable for business decision and hypothetical funding |
| AI Project Manager | Requirements, scope, dependencies, risks, progress, and decision pack |
| People Operations policy owner | Entitlements, policy interpretation, reference-answer review |
| Information Security lead | Privacy, credentials, access, and criticality review |
| Finance approver | Expense controls, bank-change controls, cost assumptions |
| Implementation engineer | Pipeline and future assistant integration |
| QA reviewer | Independent annotation and regression evidence in a future pilot |
| Employee representatives | Future usability and adoption feedback |

These are proposed responsibilities, not a real staffed team.

## Constraints and assumptions

Mandatory functionality uses Python's standard library, requires no keys or paid services, and must run offline. No private files, real company data, global settings changes, large model downloads, or external publishing are needed. The handbook is internally authoritative for the simulation. A hypothetical future business can provide approved policies and independent reviewers. Installation of optional Label Studio is timeboxed to roughly 20 minutes of troubleshooting, with a documented fallback.

## Change control and closure

Record requirement changes in the backlog, assess policy and metric effects, and update linked evidence. Baseline synthetic results stay immutable unless correcting a documented authoring error. Closure is supported by reports/completion-report.md and executable verification. The four-week roadmap and budget are planning artifacts; they do not describe actual elapsed portfolio-build duration or expenditure.
