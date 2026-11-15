# Hypothetical budget estimate

All amounts, rates, hours, and usage below are **planning assumptions**, expressed in USD for the proposed four-week small-business project. They are not market quotations, invoices, actual spending, or a claim of business return. Roles are hypothetical allocations; no real team was paid or managed in this build.

| Cost category | Assumed calculation | Estimate |
|---|---|---:|
| Proposed labor: AI Project Manager | 40 hours × USD 65 | USD 2,600 |
| Proposed labor: implementation engineer | 48 hours × USD 75 | USD 3,600 |
| Quality assurance: independent review and retesting | 24 hours × USD 50 | USD 1,200 |
| Infrastructure | Four-week private test hosting, storage, and basic logging allowance | USD 80 |
| AI inference | Future model evaluation allowance: 1,000 responses × USD 0.12 blended assumption | USD 120 |
| Subtotal | 2,600 + 3,600 + 1,200 + 80 + 120 | **USD 7,600** |
| Contingency | 20% × USD 7,600 | USD 1,520 |
| Proposed authorization ceiling | Subtotal + contingency | **USD 9,120** |

Labor excluding the separately shown QA allocation is USD 6,200. Total proposed staffing effort is 112 person-hours. The QA allowance is included once, not added again to labor. Open-source Label Studio has no assumed license charge; optional managed hosting, enterprise licensing, procurement tax, legal review, model development, and ongoing production operation are excluded. These exclusions would need review before a real authorization.

At USD 0.24 per response, the same assumed 1,000-response evaluation would cost USD 240, increasing the pre-contingency total by USD 120. If review time doubles from 24 to 48 hours, the additional QA labor is USD 1,200; this consumes most contingency and requires sponsor review. The PM should seek revised assumptions when scope, data volume, or model choice changes.

## Actual portfolio-build costs

During the original Phase 1 build, no paid services, AI inference APIs, subscriptions, or model downloads were ordered. Phase 2 added free local runtime and model downloads; it still used no paid inference API or service purchase. No monetary purchases were made as part of the build. Existing compute, network access, electricity, AI-assisted development session cost, and the owner's time were not metered, so total actual economic cost is **unknown**, not claimed to be zero. The mandatory pipeline runs with the existing Python installation and no third-party Python dependencies.

Future hosting or inference procurement would be a separate human decision after privacy review and scope approval. This estimate does not authorize any purchase.
