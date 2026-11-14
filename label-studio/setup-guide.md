# Label Studio integration and setup

**Status: Installed and runtime-verified locally.** Label Studio 1.23.0 ran in Docker, accepted the XML configuration, imported 30 tasks through its HTTP API, and rendered the annotation interface in Chrome. The smoke test interacted with primary classification, criticality, and reviewer comments. **Zero annotations were submitted.** This is an interface test, not an independent human review or a production deployment.

The verified image is `heartexlabs/label-studio@sha256:afcc516a22775a39d0d66f4c2ddc95d01be3e3d3862b21fcf4f9de34b4ad4e12`. This pins the tested artifact instead of relying on a changing `latest` tag. The upstream project is [HumanSignal/label-studio](https://github.com/HumanSignal/label-studio); its documented Docker registry namespace is `heartexlabs`. See the official [installation guide](https://labelstud.io/guide/install_requirements).

## What was verified

- Label Studio `/health` returned HTTP 200 with `status=UP`.
- Project creation with `labeling-config.xml` returned HTTP 201, including configuration validation.
- Task import returned HTTP 201 and a task count and assigned-ID list of 30.
- An imported task retained `data.test_id=TC-001`.
- Chrome displayed the first case's question, policy context, reference answer, and candidate response, plus all four primary choices, Yes/No criticality, and comments.
- Selecting a classification and criticality and entering a smoke-test comment worked. The Submit action was deliberately not used, preserving the distinction from actual annotations.

See [machine-readable browser evidence](../reports/evidence/browser-verification.json), [genuine interface screenshot](../reports/evidence/label-studio-interface.png), and [completion record](../reports/completion-report.md). This verifies one interface flow, not every Label Studio feature, all 30 annotation interactions, an export round trip, independent agreement, or an operational deployment. Temporary attempts used only synthetic data. The local test container is stopped after verification; its demo projects remain inside its writable layer. No runtime database, session cookie, password, or token is included in the repository.

## Offline preparation — mandatory and dependency free

```bash
python3 scripts/validate_dataset.py
python3 scripts/generate_label_studio.py
python3 scripts/verify_project.py
```

Tasks are a JSON list with `data` fields matching the XML's `$question`, `$policy_context`, `$reference_answer`, `$acceptance_criteria`, `$candidate_response`, and `$test_id` bindings. The top-level IDs 1–30 are deterministic in the generated file. Label Studio can assign different database IDs on import: **`data.test_id` is the portable join key** and must be preserved through exports. Tasks intentionally contain no `annotations` or `predictions`, and do not expose the baseline classifications.

## Optional interactive installation

Docker is not required by the reporting pipeline. On a machine with Docker and network access, start a separate local review instance from the repository root:

```bash
docker run -d --name northstar-review \
  -p 127.0.0.1:8088:8080 \
  -e COLLECT_ANALYTICS=false \
  heartexlabs/label-studio@sha256:afcc516a22775a39d0d66f4c2ddc95d01be3e3d3862b21fcf4f9de34b4ad4e12
```

Open `http://127.0.0.1:8088`, create your own local reviewer account, create a project titled “AI Response Quality Evaluation Pilot” (within the server's 50-character title limit), and paste `labeling-config.xml` into Settings → Labeling Interface. Import `import-tasks.json` through Data Import. Confirm 30 rows and inspect a case. Select one primary label, Yes/No criticality, and add a policy-grounded rationale. Use the rubric before submitting any real review. The interface uses `single-radio` for explicit exclusive selection.

The container's writable layer keeps its database across stop/start. Keep it if annotations matter: removing the container discards those annotations unless separately exported or backed up. Stop with `docker stop northstar-review`; restart with `docker start northstar-review`. These commands affect only the explicitly named demo instance. This setup is for localhost demonstration and does not configure a production service.

Alternatively, follow the official virtual-environment installation instructions (`python3 -m venv .venv-label-studio` followed by `.venv-label-studio/bin/python -m pip install label-studio`). Package versions and prerequisites may change; the pinned Docker image is the artifact actually verified here. Do not install globally or make the offline core depend on this optional application.

## Optional automated smoke-test reproduction

The repository includes `scripts/verify_local_browser.py`, an optional test harness. Unlike the mandatory scripts, it needs Playwright, Docker, and `/usr/bin/google-chrome`. No browser or model download is required when the existing Chrome executable is used. Tested versions: Playwright 1.65.2 and Chrome 157.0.8103.78.

```bash
python3 -m venv .venv-label-studio
.venv-label-studio/bin/python -m pip install playwright==1.65.2
```

To rerun against the existing verification container on this build machine:

```bash
docker start northstar-quality-pilot
.venv-label-studio/bin/python scripts/verify_local_browser.py --label-studio
docker stop northstar-quality-pilot
```

On a fresh machine, first create that harness container with the same pinned image:

```bash
docker run -d --name northstar-quality-pilot \
  -p 127.0.0.1:8087:8080 \
  -e LABEL_STUDIO_DISABLE_SIGNUP_WITHOUT_LINK=true \
  -e COLLECT_ANALYTICS=false \
  -e DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1 \
  heartexlabs/label-studio@sha256:afcc516a22775a39d0d66f4c2ddc95d01be3e3d3862b21fcf4f9de34b4ad4e12
```

Wait for `/health` to return UP before running the harness. It initializes only a fictional local `reviewer@example.invalid` account and demonstration organization, creates a new project on each run, and imports the synthetic tasks. Its random password is handled only in process memory; no credentials are printed or committed. It checks desktop/mobile dashboard behavior and captures real screenshots. Run it without `--label-studio` to check just the local HTML dashboard. The harness is tailored to the tested Label Studio version and is separate from the mandatory offline suite.

## Future independent annotation and export

Use reviewers who did not author the fixtures, calibrate on separate examples, and adjudicate disagreements. Export JSON from Label Studio and retain it separately from `data/evaluation-results.csv`. Map `data.test_id` to cases, `classification` choice to the primary label, `critical_failure` Yes/No to lowercase CSV true/false, and `reviewer_comments` to a rationale. Preserve actual reviewer and model provenance in a separate dataset and never overwrite the simulated baseline. An automated export converter and independent annotation exercise are not implemented here.

Official references: [task format](https://labelstud.io/guide/tasks), [Choices](https://labelstud.io/tags/choices), and [TextArea](https://labelstud.io/tags/textarea). If this optional runtime cannot be installed elsewhere, use the generated artifacts and mark that machine's integration **Prepared but not runtime-verified**; all offline reports still work.
