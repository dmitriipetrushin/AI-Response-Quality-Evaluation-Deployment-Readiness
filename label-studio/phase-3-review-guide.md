# Phase 3 independent-review preparation

Phase 3 tasks contain actual selected-model outputs, not synthetic candidate answers. The baseline and existing Label Studio projects/annotations are preserved. The preparation command is `python3 scripts/phase3_label_studio.py`; it requires a sealed final run. Actual runtime import status and the new project ID are recorded in the Phase 3 completion report rather than inferred from prepared JSON/XML.

Each task keeps `experiment_id`, portable `test_id`, exact model identifier/digest, prompt version, dataset split and difficulty, the question, relevant policy evidence, reference answer, acceptance criteria, exact answer, and answer hash. Use the composite experiment/case key when joining exports. The top-level Label Studio ID may change on import. No annotations or predictions are prefilled. The provisional-review artifact path is provided for traceability but its label is not displayed in the annotation interface.

The interface requires one primary classification, a separate critical-failure choice, one or more failure reasons (or None), severity, and reviewer comments. The same contradiction → Incorrect; otherwise material unsupported claim → Unsupported; otherwise important omission → Partially correct; otherwise Correct precedence applies. Semantic correctness and output usability are separate: a response can contain the required facts yet have repetition/truncation flags. An unknown identifier is a deterministic fact; whether it is an asserted unsupported claim requires reading context, including negation.

## Proposed independent review workflow

1. Have policy owners verify the fictional references and criteria before treating them as ground truth. For a real business, replace this fictional corpus with approved source documents.
2. Assign independent reviewers who did not author the dataset or tune prompts. Calibrate on separate examples, not held-out questions. The repository has no actual staffed review team or sponsor sign-off.
3. Keep provisional labels hidden during first-pass review. Review every held-out answer and all observed critical/unsupported cases; preferably double-review the complete final benchmark.
4. Judge the actual question, full policy evidence and criteria. Do not require exact reference-answer wording or all optional reference elaborations. Record a specific reason and severity; do not relax labels to hit a target.
5. Adjudicate disagreements, especially incomplete versus contradictory instructions, the materiality of invented routing, unsafe-intent omissions without actual upload, and valid but irrelevant policy IDs. Record the original decisions and the adjudicated version separately.
6. Export Label Studio JSON and preserve the export with reviewer provenance and approval evidence. Join on experiment/case ID and confirm the answer hash before creating a new reviewed artifact. Existing provisional CSVs and raw outputs remain immutable.

A JSON export containing annotations is not, by itself, proof that an independent human performed the work. Only genuine completed review with the appropriate provenance can be described as human-validated. This build imports actual tasks and verifies the interface but does not submit fabricated human annotations or claim human agreement.

All current quality labels are provisional agent-assisted judgments. Nominal statistical intervals condition on those labels and the authored cases; they do not replace independent review, representativeness, adversarial testing, operational controls, or business approval. Deployment remains NO-GO until defensible reliability evidence and adequate human validation exist.
