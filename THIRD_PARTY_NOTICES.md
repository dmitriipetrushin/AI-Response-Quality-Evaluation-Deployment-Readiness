# Third-party attribution

The open-source annotation foundation for this portfolio is **Label Studio**, maintained at [HumanSignal/label-studio](https://github.com/HumanSignal/label-studio). Upstream Label Studio is licensed under [Apache License 2.0](https://github.com/HumanSignal/label-studio/blob/develop/LICENSE). Label Studio is a separate optional application; its source, binaries, and dependencies are not relicensed by this repository's MIT license. No upstream source has been vendored here.

The XML configuration, task generator, fictional policies, synthetic fixtures, evaluation labels, reporting software, and documentation in this repository are original AI-assisted portfolio work. References to Label Studio do not imply endorsement or partnership.

Integration references: [installation](https://labelstud.io/guide/install_requirements), [task import](https://labelstud.io/guide/tasks), [Choices](https://labelstud.io/tags/choices), and [TextArea](https://labelstud.io/tags/textarea). Setup-guide commands and task bindings follow these official interfaces; prose is original.

Optional runtime verification can use the upstream Docker image and a project-local Playwright installation with the existing Chrome executable. Those separately installed tools retain their own upstream licenses. They are unnecessary for the mandatory standard-library pipeline and are excluded from version control.

## Phase 2 local inference

[Ollama](https://github.com/ollama/ollama) is used as a separately installed local runtime through its public HTTP API and official Docker image. The tested runtime image is pinned in `config/ollama-image.txt`; the exact version and model metadata are retained in the real-run report. No runtime source or binary is vendored in this repository.

The selected model is [Qwen2.5 3B](https://ollama.com/library/qwen2.5:3b), maintained upstream by the Qwen team. The model artifact page provides its Qwen research license; unlike some other Qwen2.5 sizes, the 3B artifact is not an Apache-2.0 model. Consult the license distributed with the exact model artifact for permitted use. The original project MIT license covers original code, fictional data, and documentation, not these separately downloaded weights or their runtime. This independent portfolio is not endorsed by Ollama, Qwen, or HumanSignal.
