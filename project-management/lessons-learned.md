# Lessons learned

**Historical Phase 1 record:** the statements below describe the original synthetic-only build at commit `931e1ac`. Phase 2 adds actual inference; see [the phase-2 record](phase-2-executive-report.md).

This is a retrospective on an independent portfolio build, not a client delivery or production incident review.

## What worked

Defining the four primary classifications and their precedence before reporting avoided overlap between wrong instructions and invented claims. Separate criticality exposed dangerous financial and credential advice even though review coverage was complete. A single authoritative CSV, exact count comparisons, and fingerprints made the reports reproducible. Policy IDs and per-case context made judgments inspectable. Standard-library Python kept the mandatory pipeline independent of hosting, model downloads, and annotation-server availability.

## What was difficult

The main semantic difficulty was distinguishing omissions from contradictions. TC-012 omits Finance approval but retains IT procurement; TC-013 explicitly advises splitting a purchase to bypass review. They deserve different primary labels and severity judgments. Unsupported claims also required attention to the handbook's scope: absence of a contractor entitlement is not a statement of a different entitlement. These decisions are documented in the rubric and case rationales.

A regression test exposed a dashboard sentence that would still say the gates failed after a hypothetical all-Correct input. The reporting code now derives that sentence from the current gates; the dataset itself was not relabeled. This demonstrates why testing the passing boundary matters even when the intended demonstration baseline fails.

## Verification limits

Structural validation does not prove that a human interpretation is correct. References, candidates, and labels were authored within the same simulation. No independent human annotation, agreement measurement, deployed model, production integration, employee adoption test, or real stakeholder sign-off occurred. See the Label Studio setup guide for the exact optional-runtime status and the completion report for executed checks; prepared XML and JSON alone are not a runtime verification claim.

## Before a real deployment

Use an approved real policy corpus with owners and change dates, expand the cases to representative employee questions, and evaluate separately versioned real-model outputs. Assign independent reviewers, calibrate outside the holdout set, adjudicate disagreements, and preserve original decisions. Implement access controls and security escalation outside the model, then verify refusal and prompt-injection behavior across variants. Require all release gates, named approvals, monitoring, rollback ownership, and bounded pilot scope. Measure usefulness and adoption only after those prerequisites; no productivity or ROI improvement can be inferred from this synthetic baseline.
