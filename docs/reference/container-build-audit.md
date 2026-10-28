# Container build license record

This record describes the local audit build made from the repository Dockerfile. It is evidence for that build only; rebuild and regenerate the manifests after changing the Dockerfile, locks, base images or Debian packages.

- Target: Linux amd64.
- Python base: `python:3.12-slim`, manifest digest `sha256:12316debbfb86890f6b2d825820612741ba527ad5a44e3902759141d572bfe8f`.
- Node base: `node:22-bookworm-slim`, manifest digest `sha256:de170b39439eb0e5a3444ad7d60b015614a381e10fecae2e30ec9e735122f38d`.
- Python and npm packages install from `uv.lock` and `package-lock.json`; complete license inventories: [Python](python-licenses.md), [npm](npm-licenses.md).
- The exact Debian package names, versions and architectures are listed in [container-debian-packages.txt](container-debian-packages.txt).
- FFmpeg reports GPL version 2 or later and its build enables `--enable-gpl`, `--enable-libx264`, and `--enable-libx265`. Debian copyright files are included in the image under `/usr/share/doc/*/copyright`. An image redistributor must provide the GPL corresponding source/offer required for the exact conveyed image and preserve applicable notices.
- OpenCode and Codex CLI versions: `1.19.4` and `0.164.0`; both execute in the container. Playwright packages are dev-only and not installed into the runtime image.
- Runtime check: `ffmpeg`, `ffprobe`, `opencode --version`, and `codex --version` all ran successfully. `/api/health`, `/`, and `/settings` returned successfully in a disposable container. No model download, YouTube authorization, media analysis, or external provider request was made.

The image was built locally for verification and is not included in the repository. This record does not grant rights to downloaded Whisper/Argos models or external services. Model terms must be checked separately before redistributing model files.
