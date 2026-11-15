# Third-party attribution

The open-source annotation foundation for this portfolio is **Label Studio**, maintained at [HumanSignal/label-studio](https://github.com/HumanSignal/label-studio). Upstream Label Studio is licensed under [Apache License 2.0](https://github.com/HumanSignal/label-studio/blob/develop/LICENSE). Label Studio is a separate optional application; its source, binaries, and dependencies are not relicensed by this repository's MIT license. No upstream source has been vendored here.

The XML configuration, task generator, fictional policies, synthetic fixtures, evaluation labels, reporting software, and documentation in this repository are original AI-assisted portfolio work. References to Label Studio do not imply endorsement or partnership.

Integration references: [installation](https://labelstud.io/guide/install_requirements), [task import](https://labelstud.io/guide/tasks), [Choices](https://labelstud.io/tags/choices), and [TextArea](https://labelstud.io/tags/textarea). Setup-guide commands and task bindings follow these official interfaces; prose is original.

Optional runtime verification can use the upstream Docker image and a project-local Playwright installation with the existing Chrome executable. Those separately installed tools retain their own upstream licenses. They are unnecessary for the mandatory standard-library pipeline and are excluded from version control.

## Phase 2 local inference

[Ollama](https://github.com/ollama/ollama) is used as a separately installed local runtime through its public HTTP API and official Docker image. The tested runtime image is pinned in `config/ollama-image.txt`; the exact version and model metadata are retained in the real-run report. No runtime source or binary is vendored in this repository.

The selected model is [Qwen2.5 3B](https://ollama.com/library/qwen2.5:3b), maintained upstream by the Qwen team. The model artifact page provides its Qwen research license; unlike some other Qwen2.5 sizes, the 3B artifact is not an Apache-2.0 model. Consult the license distributed with the exact model artifact for permitted use. The original project MIT license covers original code, fictional data, and documentation, not these separately downloaded weights or their runtime. This independent portfolio is not endorsed by Ollama, Qwen, or HumanSignal.

## Phase 3 comparison weights

The study additionally executes [Qwen3 4B Instruct 2507 Q4_K_M](https://ollama.com/library/qwen3:4b-instruct-2507-q4_K_M) and [Llama 3.2 3B](https://ollama.com/library/llama3.2:3b). Ollama's actual artifact license metadata identifies the explicit Qwen3 instruct weights as **Apache License 2.0** and the Llama weights as the **Llama 3.2 Community License Agreement** (September 25, 2024). Consult the license bundled with the exact digest, including its conditions and any upstream use restrictions. The generic Qwen3 4B tag was also downloaded for a compatibility probe and excluded from the matched comparison because its thinking behavior differed.

Exact artifact digests and quantization metadata are retained in `experiments/phase-3/` and `reports/phase-3-evidence/`; weights are cached separately and are not distributed in Git or relicensed under MIT. This project does not claim endorsement by Meta or the Qwen team. The selected Phase-3 application model is recorded in `config/assistant.json`, independently of the historical Phase-2 selection above.
