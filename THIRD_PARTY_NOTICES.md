# Third-party components

The source repository does not vendor the dependencies below. They are downloaded by the package managers or Docker build. Exact Python and npm resolutions are recorded in `uv.lock`, `package-lock.json`, [the Python license inventory](docs/reference/python-licenses.md), and [the npm license inventory](docs/reference/npm-licenses.md). Each component remains under its own license; this project’s Apache-2.0 license does not replace those terms. Review the package metadata and accompanying notices for the exact resolved versions before redistributing a built image.

## Direct Python dependencies

| Component | Declared range | License (upstream metadata) |
|---|---:|---|
| FastAPI | `>=0.115,<1` | MIT |
| Uvicorn | `>=0.30,<1` | BSD-3-Clause |
| python-multipart | `>=0.0.9,<1` | Apache-2.0 |
| faster-whisper | `>=1.1,<2` | MIT |
| PyAV (`av`) | `>=11,<19` | BSD-3-Clause |
| Argos Translate | `>=1.10,<1.11` | MIT or CC0 (dual licensed) |
| google-api-python-client | `>=2.150,<3` | Apache-2.0 |
| google-auth-oauthlib | `>=1.2,<2` | Apache-2.0 |
| opencv-python-headless | `>=4.10,<5` | Apache-2.0; includes separate third-party notices |
| PyTorch (`torch`) | `2.14.0` in Docker build | BSD-style license; includes third-party notices |
| httpx | `>=0.28,<1`, test extra | BSD-3-Clause |

`uv.lock` resolves the transitive Python dependencies used by the project and Docker build. The default lock uses CPU-only PyTorch to avoid adding NVIDIA proprietary CUDA wheels. Argos Translate is capped below 1.11 because 1.11 adds MiniSBD (AGPL-3) as a dependency; MiniSBD is not needed by this project’s chosen Argos version. Package licenses and notices remain distributed with their packages; this summary is not a substitute for inspecting those files in the resolved environment.

## JavaScript and command-line components

- Playwright Test, Playwright, and Playwright Core: Apache-2.0, versions pinned by `package-lock.json`.
- `opencode-ai`: MIT, pinned to `1.19.4` in the Dockerfile.
- `@openai/codex`: Apache-2.0, pinned to `0.164.0` in the Dockerfile.

The full resolved npm dependency set, including the CLI platform packages, is recorded in `package-lock.json` and [the npm license inventory](docs/reference/npm-licenses.md). Retain package notices when redistributing an image.

The `uv` build tool is installed at version `0.8.22`; uv is dual licensed MIT OR Apache-2.0. It is not part of the application runtime.

## System image

The Dockerfile uses the official Node 22 Bookworm Slim and Python 3.12 Slim images and installs Debian FFmpeg and runtime libraries. These components have their own licenses and notices. The Dockerfile pins Node/Python base images by digest; Debian package versions are resolved at build time from the Debian repository. The audit build used the pinned Node/Python base image digests and its exact Debian package inventory is in [the container build record](docs/reference/container-build-audit.md) and [package manifest](docs/reference/container-debian-packages.txt). Debian FFmpeg is GPL-2.0-or-later and is built with GPL codecs (`libx264`, `libx265`); redistributing that image requires complying with those GPL terms and retaining Debian copyright notices/corresponding source. The repository contains no built image. Re-audit when base digests or Debian packages change.

## Downloaded models and external services

Whisper and Argos language models are downloaded separately at runtime and are not covered by this repository’s Apache-2.0 license. Check the license accompanying each selected model/package before redistribution or commercial use. YouTube, OpenCode, Codex, and hosted model services have their own terms; using this application does not grant rights to their services or model outputs.

## Verification sources

Package lockfiles are authoritative for resolved versions. Upstream metadata checked for direct packages includes PyPI project metadata and npm package metadata; license declarations may change between versions. Re-audit when changing dependency ranges, lockfiles, Docker base images, or model catalogs.
