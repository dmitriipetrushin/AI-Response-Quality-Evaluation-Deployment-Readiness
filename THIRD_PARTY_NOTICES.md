# Third-party attribution

The open-source annotation foundation for this portfolio is **Label Studio**, maintained at [HumanSignal/label-studio](https://github.com/HumanSignal/label-studio). Upstream Label Studio is licensed under [Apache License 2.0](https://github.com/HumanSignal/label-studio/blob/develop/LICENSE). Label Studio is a separate optional application; its source, binaries, and dependencies are not relicensed by this repository's MIT license. No upstream source has been vendored here.

The XML configuration, task generator, fictional policies, synthetic fixtures, evaluation labels, reporting software, and documentation in this repository are original AI-assisted portfolio work. References to Label Studio do not imply endorsement or partnership.

Integration references: [installation](https://labelstud.io/guide/install_requirements), [task import](https://labelstud.io/guide/tasks), [Choices](https://labelstud.io/tags/choices), and [TextArea](https://labelstud.io/tags/textarea). Setup-guide commands and task bindings follow these official interfaces; prose is original.

Optional runtime verification can use the upstream Docker image and a project-local Playwright installation with the existing Chrome executable. Those separately installed tools retain their own upstream licenses. They are unnecessary for the mandatory standard-library pipeline and are excluded from version control.
