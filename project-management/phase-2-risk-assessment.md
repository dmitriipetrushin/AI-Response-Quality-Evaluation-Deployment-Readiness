# Phase 2 risk assessment

Independent portfolio simulation; owner roles below are proposed business responsibilities, not a real team. This extends the original risk register without closing risks merely because a local model runs.

| Risk | Likelihood / impact | Implemented mitigation or evidence | Residual exposure / proposed owner |
|---|---|---|---|
| Invented company rules or benefits | Medium / High | Full authoritative handbook, grounded instructions, unchanged unknown-information test cases, exact output preservation | Instructions are not a guarantee; independent substantive review required. Policy owner. |
| Incorrect or misleading citations | Medium / High | Check generated IDs against actual sections; expose source text; separate identifier validation from support review | A valid ID may support none of the claim. QA reviewer. |
| Missing approvals, deadlines, or evidence | Medium / High | Multi-step cases, completeness criteria, provisional rationales, output-limit warnings | Small model and output budget can omit steps. QA reviewer / Finance. |
| Slow CPU inference | High / Medium | One inference slot in the UI, explicit busy response, loading state, configurable timeout, recorded batch latency | Real timing is not a concurrent-load SLA. Implementation engineer. |
| RAM or disk constraints | Medium / High | Select a roughly 1.9 GB quantized model; verify native/configured context; restrict default parallelism | Model weights, KV cache, and runtime consume more than download size; competing processes vary. Implementation engineer. |
| Model or runtime unavailable | Medium / High | Loopback health check, useful errors, reproducible setup command, persisted ignored model cache | New installations require initial internet access and Docker permissions. Implementation engineer. |
| Incomplete evaluation or silent failures | Medium / High | Atomic response checkpoints, explicit error records, strict resume checks, attempted/successful/failed counters | Partial reviews keep gates pending and block approval. AI Project Manager. |
| Shared-author review bias | High / High | Label every real-output judgment provisional agent-assisted; hash reviews to exact responses | No independent human adjudication or reviewer agreement yet. QA lead. |
| Privacy or credential disclosure | Medium / Critical | Fictional data only, no cloud inference, no question logging, refuse embedded instructions through system prompt, explicit UI notice | Prompt-only controls are insufficient for real restricted records; real authorization must sit outside the model. Security lead. |
| Prompt injection changes behavior | Medium / Critical | Treat questions and quoted content as untrusted; no tools or command-execution interface | One dataset cannot establish injection resistance; adversarial variants needed. Security lead. |
| Browser-origin abuse or unsafe output rendering | Low / High | Loopback binding, Host/Origin checks, JSON/input bounds, strict file allowlist, textContent rendering, no evaluation of answer HTML | A localhost demonstration is not a hardened multi-user service. Security lead. |
| Unreproducible results or changed model tag | Medium / Medium | Record model digest, runtime version, options, policy/question/prompt hashes and exact raw replies; pin runtime image | Seed is not cross-platform determinism; model tag can resolve differently on a future download. Implementation engineer. |
| Baseline accidentally overwritten | Low / High | Protected output targets, separate actual-run paths, baseline fingerprint check and original tests | New runs should use new output files; preserve historical decisions. AI Project Manager. |
| Model licensing misunderstood | Low / High | Keep upstream model license separate from repository MIT; document Qwen2.5 3B's Qwen research license | A real use case needs its own license review. Sponsor. |

Acceptance of these residual risks is not recorded or implied. The phase-2 executive report makes the recommendation using actual evidence and provisional review status; no business stakeholders signed off during this simulation.
