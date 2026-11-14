# Case study: a defensible pre-pilot AI quality decision

**Dmitry Petrushin · AI Project Manager / AI Implementation Manager portfolio**<br>
**Independent simulation:** Northstar Business Services and all stakeholder roles are fictional. This is not paid employment, a client engagement, management of a real team, or a production deployment.

## The decision to support

A fictional small business is considering an assistant for employee-policy questions. The important management question is whether the available quality evidence supports a controlled pilot, given the possibility of invented benefits, missed approvals, credential exposure, and unsafe financial instructions.

I framed the deliverable as a reproducible decision process: requirements, an authoritative fictional knowledge base, risk-based test coverage, explicit review rules, measurable gates, and a decision pack. A working reporting tool and a no-go recommendation can both be successful delivery outcomes.

## Scope and planning

The charter separates the portfolio's completion criteria from the assistant's proposed release gates. The management pack includes a proposed four-week roadmap, a 21-item backlog with dependencies and acceptance criteria, 14 risks with fictional owner roles, and a hypothetical USD 9,120 budget ceiling. The budget assumes 112 person-hours, infrastructure and future inference allowances, and 20% contingency. It is not actual expenditure, a price quote, or elapsed portfolio duration.

The offline core was prioritized so neither model availability nor optional annotation tooling could prevent completion. No real company data, API credentials, model downloads, or external publishing were required. The foundation is a prepared integration with HumanSignal Label Studio, with actual runtime status disclosed in its setup guide.

## Evaluation design

The 2,019-word fictional handbook defines seven policies covering remote work, leave, expenses, equipment, security, travel, and approvals. Exactly 30 cases cover 10 factual questions and five each of multi-step, ambiguous, outside-scope, and sensitive questions. Every case includes context, policy IDs where applicable, a reference answer, expected behavior, risk, and acceptance criteria.

Synthetic answers intentionally include realistic failures. All responses are marked `synthetic_fixture`; all baseline labels are `simulated_review`. A four-label rubric prioritizes material contradiction, then unsupported claims, then omissions. Safe refusal, uncertainty, and clarification qualify as Correct when appropriate. Criticality is assessed separately from the label and the question's inherent risk.

For example, TC-012 omits a Finance approval while preserving IT procurement, so its authored label is Partially correct. TC-013 expressly advises purchase splitting to bypass review, so it is Incorrect and critical. TC-022 invents free parking without contradicting an explicit alternative entitlement, so it is Unsupported. These distinctions make the quality process reviewable.

## Implementation and verification

Standard-library Python validates required fields, category counts, unique IDs, record coverage, policy references, verbatim context, boolean values, labels, and provenance. It then calculates exact gate comparisons, category performance, and critical counts. The reports expose every rationale and record input fingerprints for repeatability.

The 28-test unittest suite checks failure paths as well as the expected dataset. A test exposed a fixed failure sentence in the dashboard's hypothetical passing scenario; the implementation now derives that wording from current gate outcomes. The actual baseline labels were preserved. XML and JSON checks verify annotation-task structure; browser and optional-runtime checks are recorded separately in the completion report.

## Result and decision

| Metric | Actual synthetic result | Proposed target |
|---|---|---|
| Correct | **56.7% (17/30)** | At least 90% |
| Unsupported | **13.3% (4/30)** | No more than 5% |
| Critical failures | **4** | Zero |
| Coverage | **100.0% (30/30)** | 100% |

The remaining primary labels are 4 Partially correct and 5 Incorrect. Three proposed release gates fail, so the recommendation is **NO-GO**. Critical cases concern login codes, purchase splitting, password/recovery-code collection, and supplier-bank-change verification. The decision follows the evidence instead of changing labels to pass. It is not a measured model benchmark: no actual model was evaluated.

## Next steps for a real organization

First, remediate credential and financial-control failure patterns and retain authorization controls outside the model. Then evaluate versioned real-model responses against a broader representative holdout set, assign independent reviewers, adjudicate disagreements, and repeat critical and full regression tests. Any controlled pilot needs policy-owner, sponsor, security, Finance, and QA approval, with monitoring and rollback ownership. Those approvals and business activities did not occur here.

## Competencies demonstrated

This project makes requirements, scope, dependencies, cost assumptions, evaluation methodology, risk ownership, status reporting, and a release recommendation concrete. The strongest lesson is that process readiness and assistant readiness need separate evidence. Thirty authored fixtures demonstrate the framework; they cannot prove production accuracy, safety, adoption, savings, or return on investment.

Evidence: [README](../README.md), [generated report](../reports/quality-report.md), [dashboard](../reports/dashboard.html), [charter](../project-management/project-charter.md), [risk register](../project-management/risk-register.csv), and [actual verification record](../reports/completion-report.md).
