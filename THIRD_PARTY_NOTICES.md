# Third-party notices

Sovereign AI iBuddy depends on third-party packages listed in the package lockfiles and Python requirement files. It also installs the model and inference runtime below from their upstream projects. This file is an overview, not a replacement for the license texts and notices distributed by each dependency.

## Qwen3-8B-GGUF

- Project: [Qwen/Qwen3-8B-GGUF](https://huggingface.co/Qwen/Qwen3-8B-GGUF)
- Selected file: `Qwen3-8B-Q5_K_M.gguf`
- Selected revision: `4f02e7c52b572082828edf5058a87e2e7dc3e4d5`
- Upstream license: Apache License 2.0
- Distribution: downloaded separately during model installation; not included in this repository

## llama.cpp

- Project: [ggml-org/llama.cpp](https://github.com/ggml-org/llama.cpp)
- Selected release: `b10408`, Windows CPU x64 asset
- Upstream license: [MIT License](https://github.com/ggml-org/llama.cpp/blob/master/LICENSE)
- Distribution: downloaded separately during model installation; not included in this repository

## Application dependencies

- Python dependencies and exact direct versions: [`backend/requirements.txt`](backend/requirements.txt) and [`backend/requirements-dev.txt`](backend/requirements-dev.txt)
- Optional local Transformers dependency profile: [`backend/requirements-local.txt`](backend/requirements-local.txt)
- Root JavaScript dependency graph and license metadata: [`package-lock.json`](package-lock.json)
- Frontend JavaScript dependency graph and license metadata: [`frontend/package-lock.json`](frontend/package-lock.json)

An organization redistributing binaries, bundled dependencies, containers, model weights, or an offline installation package must generate and review a complete dependency/license inventory for that artifact and carry forward all applicable copyright, attribution, source, notice, offer, and license obligations.

The Apache-2.0 license selected for this project's own source does not replace or modify any third-party terms. Review current upstream terms before use or redistribution; model and dependency terms can change between versions.
