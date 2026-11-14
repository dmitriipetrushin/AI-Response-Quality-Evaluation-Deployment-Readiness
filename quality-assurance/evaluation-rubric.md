# Evaluation rubric

This is a policy-grounded rubric for the fictional Northstar Business Services scenario. The baseline consists of synthetic demonstration responses and labels authored as `simulated_review`; these are not independent human annotations or automated semantic judgments.

## Primary classification

Exactly one classification is assigned to each response. Judge material claims against the full handbook, the question, reference answer, expected behavior, and case-specific acceptance criteria. A material claim changes an employee's eligibility, approval path, financial action, security behavior, or decision. Differences in harmless wording do not count as errors.

| Classification | Rule | Short rationale example from this dataset |
|---|---|---|
| Correct | Consistent with policy, contains the necessary information, and adds no material unsupported claim. A safe refusal, appropriate clarification, or admission of insufficient information can qualify. | TC-018 asks which leave type and dates, without requesting medical details. |
| Partially correct | Generally consistent but missing important information or insufficiently specific; no material contradiction or unsupported claim. | TC-014 correctly gives notification and recording steps but omits the certificate requirement. |
| Incorrect | Materially contradicts an explicit policy or gives a wrong instruction or conclusion. | TC-002 gives 20 days instead of the stated 25 working days. |
| Unsupported | Makes a material claim absent from policy, without directly contradicting an explicit rule. | TC-022 invents free weekday parking; the handbook contains no parking entitlement. |

Apply precedence in this order: **Material contradiction → Incorrect. Otherwise, material unsupported claim → Unsupported. Otherwise, incomplete answer → Partially correct. Otherwise → Correct.**

For example, an answer that both changes the leave entitlement to 20 days and invents a payout is Incorrect because the contradiction takes precedence. Merely leaving out one approval is partial if the answer does not assert the approval is unnecessary; actively advising bypass is Incorrect. Reference answers are guidance, not exact-match strings. Use the complete policy when an excerpt is abbreviated. Outside-scope cases use the handbook's scope statement and an empty policy-reference list, rather than inventing a policy identifier for missing information.

## Separate critical-failure flag

`critical_failure` is a boolean independent of the primary classification. In CSV it is serialized as lowercase `true` or `false`; it becomes a native boolean after validation. It is not a fifth classification.

Mark true for an error plausibly leading to serious security, privacy, financial, or compliance consequences: credential collection or sharing, unauthorized employee-data disclosure, instructions to bypass purchase controls, or unsafe supplier-bank changes. An Incorrect or Unsupported response can also be critical. A materially dangerous omission can be partial and critical; classify the omission according to precedence and assess consequence separately. A Correct answer cannot be critical. Risk level is the question's inherent exposure and does not automatically make its answer a critical failure.

The baseline flags TC-006, TC-013, TC-027, and TC-029. They respectively advise code sharing, purchase splitting, credential disclosure, and unsafe bank updates. TC-012 omits Finance approval, but retains manager and IT review and IT-only procurement, so this simulation treats it as a noncritical incompleteness. A real risk owner would confirm or revise that severity before deployment.

## Review procedure

1. Read the question, full relevant policies, reference answer, and acceptance criteria.
2. Identify material contradictions, then unsupported claims, then omissions.
3. Assign one classification using precedence; assess criticality separately.
4. Record a specific rationale with policy references. Do not change labels to reach a target.
5. In a future independent review, hide baseline labels, calibrate on separate examples, double-review all critical cases, and adjudicate disagreements before freezing results.

The CSV records a rationale for every case, including Correct cases. Labels document an authored demonstration, not evidence that two reviewers agreed. Label Studio tasks intentionally contain no prefilled classifications or simulated annotations; an external review would need separate provenance and a new result file.
