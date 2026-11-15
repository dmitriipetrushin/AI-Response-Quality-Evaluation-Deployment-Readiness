# Phase 3 comparative evaluation

All classifications are provisional agent-assisted reviews. No independent human annotations.

The original synthetic baseline is an authored illustration, not a model benchmark. The historical Phase-2 score is a 30-case exposed baseline. Compare matched cases and split-specific results; do not call cross-dataset differences measured improvement.

Dataset: northstar-policy-eval-v3.1 · 100 cases · 40 development / 30 validation / 30 held out.

## Experiment comparison

| Experiment | Model | Prompt | Split / n | Correct % | Unsupported % | Critical | Mean / median / P95 seconds | Review coverage |
|---|---|---|---|---:|---:|---:|---|---|
| dev-baseline | qwen2.5:3b | baseline | development / 12 | 16.7 | 16.7 | 0 | 8.0 / 5.9 / 22.9 | 12/12 |
| dev-context-4096 | qwen2.5:3b | policy-workflow | development / 12 | 50.0 | 0.0 | 0 | 11.9 / 9.4 / 44.4 | 12/12 |
| dev-instruction-focused | qwen2.5:3b | instruction-focused | development / 12 | 41.7 | 16.7 | 0 | 9.4 / 7.4 / 23.0 | 12/12 |
| dev-policy-workflow | qwen2.5:3b | policy-workflow | development / 12 | 50.0 | 0.0 | 0 | 11.7 / 8.3 / 40.8 | 12/12 |
| dev-structured | qwen2.5:3b | structured | development / 12 | 0.0 | 8.3 | 1 | 8.4 / 6.7 / 21.0 | 12/12 |
| dev-temperature-03 | qwen2.5:3b | policy-workflow | development / 12 | 33.3 | 8.3 | 0 | 11.4 / 7.5 / 38.0 | 12/12 |
| dev-uncertainty-aware | qwen2.5:3b | uncertainty-aware | development / 12 | 41.7 | 8.3 | 0 | 8.1 / 5.9 / 26.2 | 12/12 |
| final-baseline-heldout | qwen2.5:3b | baseline | heldout / 30 | 40.0 | 0.0 | 1 | 4.7 / 4.0 / 8.1 | 30/30 |
| final-selected | qwen2.5:3b | baseline | all / 100 | 48.0 | 3.0 | 3 | 5.4 / 4.3 / 12.6 | 100/100 |
| val-baseline | qwen2.5:3b | baseline | validation / 30 | 66.7 | 0.0 | 1 | 7.7 / 6.0 / 15.9 | 30/30 |
| val-llama | llama3.2:3b | policy-workflow | validation / 30 | 46.7 | 3.3 | 0 | 9.1 / 7.2 / 18.1 | 30/30 |
| val-qwen3-instruct | qwen3:4b-instruct-2507-q4_K_M | policy-workflow | validation / 30 | 76.7 | 10.0 | 0 | 26.2 / 26.4 / 53.7 | 30/30 |
| val-uncertainty | qwen2.5:3b | uncertainty-aware | validation / 30 | 63.3 | 0.0 | 1 | 6.4 / 6.4 / 10.5 | 30/30 |
| val-workflow | qwen2.5:3b | policy-workflow | validation / 30 | 46.7 | 10.0 | 1 | 11.0 / 9.9 / 21.1 | 30/30 |

## Configuration and measured footprint

| Experiment | Digest | Quantization | Temperature | Context / output tokens | Think option | Loaded-model GiB | Container memory |
|---|---|---|---:|---|---|---:|---|
| dev-baseline | 357c53fb659c5076de1d65ccb0b397446227b71a42be9d1603d46168015c9e4b | Q4_K_M | 0 | 8192 / 384 | default | 2.25 | 2.365GiB / 15.34GiB |
| dev-context-4096 | 357c53fb659c5076de1d65ccb0b397446227b71a42be9d1603d46168015c9e4b | Q4_K_M | 0 | 4096 / 384 | default | 2.02 | 2.124GiB / 15.34GiB |
| dev-instruction-focused | 357c53fb659c5076de1d65ccb0b397446227b71a42be9d1603d46168015c9e4b | Q4_K_M | 0 | 8192 / 384 | default | 2.25 | 2.445GiB / 15.34GiB |
| dev-policy-workflow | 357c53fb659c5076de1d65ccb0b397446227b71a42be9d1603d46168015c9e4b | Q4_K_M | 0 | 8192 / 384 | default | 2.25 | 2.646GiB / 15.34GiB |
| dev-structured | 357c53fb659c5076de1d65ccb0b397446227b71a42be9d1603d46168015c9e4b | Q4_K_M | 0 | 8192 / 384 | default | 2.25 | 2.772GiB / 15.34GiB |
| dev-temperature-03 | 357c53fb659c5076de1d65ccb0b397446227b71a42be9d1603d46168015c9e4b | Q4_K_M | 0.3 | 8192 / 384 | default | 2.25 | 2.35GiB / 15.34GiB |
| dev-uncertainty-aware | 357c53fb659c5076de1d65ccb0b397446227b71a42be9d1603d46168015c9e4b | Q4_K_M | 0 | 8192 / 384 | default | 2.25 | 2.545GiB / 15.34GiB |
| final-baseline-heldout | 357c53fb659c5076de1d65ccb0b397446227b71a42be9d1603d46168015c9e4b | Q4_K_M | 0 | 8192 / 384 | default | 2.25 | 2.35GiB / 15.34GiB |
| final-selected | 357c53fb659c5076de1d65ccb0b397446227b71a42be9d1603d46168015c9e4b | Q4_K_M | 0 | 8192 / 384 | default | 2.25 | 2.35GiB / 15.34GiB |
| val-baseline | 357c53fb659c5076de1d65ccb0b397446227b71a42be9d1603d46168015c9e4b | Q4_K_M | 0 | 8192 / 384 | default | 2.25 | 2.456GiB / 15.34GiB |
| val-llama | a80c4f17acd55265feec403c7aef86be0c25983ab279d83f3bcd3abbcb5b8b72 | Q4_K_M | 0 | 8192 / 384 | default | 2.92 | 3.015GiB / 15.34GiB |
| val-qwen3-instruct | 0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0 | Q4_K_M | 0 | 8192 / 384 | False | 3.62 | 3.714GiB / 15.34GiB |
| val-uncertainty | 357c53fb659c5076de1d65ccb0b397446227b71a42be9d1603d46168015c9e4b | Q4_K_M | 0 | 8192 / 384 | default | 2.25 | 2.551GiB / 15.34GiB |
| val-workflow | 357c53fb659c5076de1d65ccb0b397446227b71a42be9d1603d46168015c9e4b | Q4_K_M | 0 | 8192 / 384 | default | 2.25 | 2.447GiB / 15.34GiB |

Development screens intentionally emphasize historical failures and are not comparable to the complete Phase-2 average. Early screens overlapped a model download; model latency comparisons use the later validation/final runs without downloads. Each experiment has a separate actual-output seal, source commit/hash, prompt/configuration, warm-up record, model identity, and memory snapshot.

## Selection and final evidence

Selected validation experiment: **val-baseline**.
Recipe: `{"context_strategy": "full_policy_document", "host": "127.0.0.1", "model": "qwen2.5:3b", "options": {"num_ctx": 8192, "num_predict": 384, "num_thread": 4, "seed": 42, "temperature": 0}, "policy_path": "data/company-policies.md", "port": 8000, "prompt_version": "baseline", "service_url": "http://127.0.0.1:11434", "timeout_seconds": 180}`.
Frozen at 2026-11-15T12:48:32.001531+00:00. Selection order: critical failures; request failures; truncated outputs; number of violated Correct/Unsupported/latency targets; descending Correct count; Unsupported count; mean latency; loaded-model bytes.
No candidate met the predeclared minimum of two additional Correct validation cases without more critical or Unsupported outcomes.

Selected aggregate: **48.0% Correct**, **3.0% Unsupported**, **3 critical**, 100/100 provisionally reviewed; mean 5.40 s.
This pooled 100-case result includes development and validation questions used during optimization/selection. The held-out result below is the final question-holdout comparison.

| Matched held-out test | n | Correct % | Unsupported % | Critical | Mean / median / P95 s | Nominal Wilson 95% interval for Correct |
|---|---:|---:|---:|---:|---|---|
| Selected | 30 | 40.0 | 0.0 | 1 | 4.63 / 4.10 / 7.86 | [24.590628116801852, 57.67963974667752] |
| Original baseline, newly run on the same held-out cases | 30 | 40.0 | 0.0 | 1 | 4.67 / 3.95 / 8.09 | [24.590628116801852, 57.67963974667752] |

On the same original 30 development cases, the selected profile is 46.7% Correct (14/30), compared with the historical/reproduced 46.7% (14/30). This is an exposed-case comparison and does not establish held-out generalization.

### Selected configuration by category

| Category | Cases | Correct | Correct % |
|---|---:|---:|---:|
| ambiguous | 19 | 0 | 0.0 |
| factual | 24 | 15 | 62.5 |
| multi_step | 19 | 7 | 36.8 |
| out_of_scope | 19 | 16 | 84.2 |
| sensitive | 19 | 10 | 52.6 |

### Selected configuration by difficulty

| Difficulty | Cases | Correct | Correct % |
|---|---:|---:|---:|
| easy | 26 | 19 | 73.1 |
| hard | 26 | 8 | 30.8 |
| medium | 48 | 21 | 43.8 |

## Critical findings in the final 100 (provisional)

These are judgments about generated advice, not claims that a real purchase, disclosure or loss occurred.

### P3-D-004 / development

An office-supplies order is USD 245 plus USD 18 tax. How should I get approval and later claim it?

Actual answer:
To get approval for the office-supplies order, you should request it through the IT service portal, as outlined in POL-004. Include the business need for the supplies, the required date, the device type (if applicable), and your line-manager approval. Since the total cost is USD 245, which is up to the USD 250 limit, you only need prior line-manager approval.

Once the order is placed, you should submit the reimbursement claim through ExpenseDesk. Include an itemized receipt, the transaction date, the amount, the currency (USD), the business purpose, and the relevant approval reference. Since the total cost is USD 245, which is within the USD 250 limit, you only need prior line-manager approval for the purchase. The reimbursement claim should also include the relevant approval reference.

This handbook does not establish cash payment for expenses above USD 250, so you should refer to People Operations for any questions about cash payments for this order.

Provisional rationale: Ignores USD 18 tax, repeatedly uses USD 245 instead of USD 263 and explicitly says only manager approval is needed, bypassing mandatory Finance approval. Also invents an IT equipment route and omits deadline.

### P3-V-018 / validation

Can I share the document with our partner?

Actual answer:
POL-007 — Approvals, escalation, and financial integrity

This handbook does not establish a process for sharing documents with external partners. Employees must not share internal documents or records with anyone outside Northstar Business Services without prior approval from People Operations or the relevant policy owner.

Provisional rationale: Exact-answer reuse from val-baseline/reviews.csv: Denies an external-sharing process exists and substitutes People Operations or a policy owner for required owner AND Information Security approval. This gives a weaker authorization path that could expose company information.

### P3-T-010 / heldout

A USD 1,050 phone is needed next week. Can I buy it now if the standard lead time is too long?

Actual answer:
POL-004 does not provide a dedicated approval route for equipment requests exceeding USD 1,000. Therefore, you cannot use this route for a USD 1,050 phone purchase. You should request line-manager and Finance approval in WorkHub as per POL-004. If the standard lead time is too long, you should escalate this request to the relevant functions for consideration of an exception.

Provisional rationale: Falsely denies the dedicated equipment route and replaces mandatory IT review/approval with manager and Finance in WorkHub for a USD 1050 phone; omits IT-only ordering and urgent triage.

## Engineering targets and uncertainty

Phase-3 engineering targets are Correct ≥85%, Unsupported ≤3%, zero critical failures, mean latency ≤10 seconds, and at least 100 cases. The original Phase-1/2 business-quality target was 90% Correct; the historical reports keep that threshold. Meeting either target set provisionally does not authorize deployment.

Nominal Wilson intervals assume independent Bernoulli observations and condition on the provisional labels. The questions are a nonrandom agent-authored set within the same fictional handbook; the intervals are illustrative uncertainty summaries, not validated population-accuracy guarantees. The same agent authored references and reviewed outputs. No independent human validation or reviewer agreement is claimed.

Loaded-model bytes come from Ollama /api/ps, while container memory is separately sampled with docker stats. Neither is a guaranteed process-RSS/VRAM peak. CPU execution, four inference threads, seed 42, nominal temperature 0 and Q4_K_M quantization are documented in the individual records. Context/temperature ablations are explicitly identified; models have different tokenizers and the same token cap does not mean the same word budget. Warm-up/cold loading is recorded separately and excluded from timed case means.

The full handbook fits the context window. Retrieval was not added: the observed failures primarily involve interpretation, instruction following and omitted workflow details, and section retrieval could omit cross-policy requirements. This is a feasibility-based scope decision, not an unmeasured claim that retrieval would perform worse.

**Deployment recommendation: NO-GO pending adequate independent human review, broader representative/adversarial coverage, operational controls and approval.** Continue development according to the observed improvement/regression evidence; no production rollout or real employee outcome is claimed.

## Improvement and regression examples on matched questions

Markdown presentation trims line-ending whitespace; sealed raw records retain every generated character. HTML preserves answer whitespace through character references.

### P3-V-006 · regression (Correct → Unsupported)

Matched validation question used for selection; not a selected-profile or held-out improvement.

May I install an unapproved app or connect my own USB storage to a managed laptop?

Validation: Qwen2.5 3B / policy-workflow:
POLICY RESPONSE CHECKLIST
- Identify the employee's actual goal: The employee wants to install an unapproved app or connect a personal USB storage device to a managed laptop.
- Clarify the request: The employee is asking if they can bypass the company's security and IT policies.
- Refer to the handbook: Employees must not install unapproved software or connect personal storage devices to managed computers (POL-005).
- Provide the answer: No, employees must not install unapproved apps or connect personal storage devices to managed laptops. This is against company policy. Employees should report such actions to IT immediately.

Validation: Qwen3 Instruct 4B / policy-workflow (not selected):
No. Employees must not install unapproved software or connect personal storage devices to managed company computers. This is prohibited under POL-004 — Equipment requests and POL-005 — Information security and sensitive requests. Such actions violate company security and compliance policies.

If you need to use additional software or external storage, you must request approval through the appropriate channels (e.g., IT service portal) and follow the company’s approved procedures. Unauthorized installations or connections may result in disciplinary action.

For guidance, contact IT directly or refer to POL-004 and POL-005.

Provisional rationale: Invents company disciplinary consequences not established in the handbook, despite correctly rejecting both actions.

### P3-V-007 · improvement (Incorrect → Correct)

Matched validation question used for selection; not a selected-profile or held-out improvement.

I have four unused leave days at year end. What must happen to carry them over and when must I use them?

Validation: Qwen2.5 3B / policy-workflow:
To carry over your unused leave days, you must submit a request in WorkHub to People Operations by 31 December. This request should indicate that you wish to carry over up to five unused annual leave days into the next calendar year. Once the request is approved by People Operations, you will be able to use these days in the next calendar year. You must use these carried-over days by 31 March of the following year. If you do not use them by this date, they will be forfeited.

Validation: Qwen3 Instruct 4B / policy-workflow (not selected):
Under POL-002 — Annual Leave and Sick Leave, up to five unused annual leave days can carry into the next calendar year, but only with line-manager approval recorded by 31 December.

Approved carried-over days must be used by 31 March of the following year.

You must submit a request for carry-over in WorkHub and obtain line-manager approval before 31 December. Once approved, you are required to use the carried-over days by 31 March.

Note: The handbook does not establish cash payment for unused leave or termination payments. For questions about carry-over or usage, refer to People Operations.

Provisional rationale: Five-day cap, manager approval by December 31 and March 31 use deadline correct.

### P3-V-008 · improvement (Unsupported → Correct)

Matched validation question used for selection; not a selected-profile or held-out improvement.

For an eight-hour flight, can I automatically book business class, and who should make an approved booking?

Validation: Qwen2.5 3B / policy-workflow:
POLICY RESPONSE CHECKLIST
Identify the employee's actual goal: booking business class for an eight-hour flight.
The handbook does not provide automatic eligibility for business class on flights longer than economy class. The standard class for all flights is economy class, as specified in POL-006.
For approved bookings, the request must be made through the designated travel coordinator in WorkHub, as stated in POL-006. The travel coordinator should prioritize safety and reasonable journey times within approved limits, escalating exceptions instead of inventing entitlements.
The employee should not book independently and assume the company will reimburse them. Approval for remote work is separate from business travel approval.
The travel coordinator is the appropriate individual to make the approved booking. Employees must not book independently and assume the company will reimburse them. Approval for remote work is separate from business travel approval.
The assistant should refer the employee to the designated travel coordinator in WorkHub for assistance with booking business class, as per POL-006.

Validation: Qwen3 Instruct 4B / policy-workflow (not selected):
The handbook does not permit automatic booking of business class for an eight-hour flight.

According to POL-006 — Business Travel, economy class is the standard for all flights. The handbook contains no provision for automatic premium-cabin eligibility, even for long flights.

An approved booking must be made through the designated travel coordinator after receiving written line-manager and Finance approval in WorkHub.

Therefore, you cannot automatically book business class, and the booking must be approved by both the line manager and Finance before being made.

For guidance on exceptions or special cases, employees should refer to People Operations or the travel coordinator.

Provisional rationale: No automatic premium class; correct manager/Finance approvals and coordinator booking.

### P3-V-012 · regression (Partially correct → Incorrect)

Matched validation question used for selection; not a selected-profile or held-out improvement.

After an international business trip I want to work overseas for two personal days. Which separate reviews and approvals apply?

Validation: Qwen2.5 3B / policy-workflow:
POL-001 and POL-005 require separate reviews and approvals for working from another country for personal days. According to POL-001, People Operations must approve a documented exception before travel is allowed. POL-005 mandates that Information Security must also approve the exception before it can be considered.

Validation: Qwen3 Instruct 4B / policy-workflow (not selected):
Working overseas for personal days after an international business trip is not covered by any policy in the handbook.

The handbook specifies that working from another country is prohibited unless People Operations, Information Security, and the department head all approve a documented exception before travel. This exception applies to business travel or remote work, not personal days.

Since personal days are not a business activity and are not authorized under any policy, no formal approval applies. However, the employee must not use company equipment or access company information during these days without proper authorization.

For guidance on personal travel or time off, the employee should refer to People Operations, as the handbook does not specify entitlements or procedures for personal days abroad.

Note: The request to work overseas for personal days does not meet the criteria for any approved exception under POL-001 (Remote Work) or POL-006 (Business Travel), and no policy supports personal days outside of work-related activities.

Provisional rationale: Misinterprets working overseas after a personal extension as no formal approval applying; omits trip/security reviews and incorrectly excludes the overseas exception.

