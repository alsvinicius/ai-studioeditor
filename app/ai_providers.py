from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from . import opencode_runner

CODEX_MODEL = "gpt-6-luna"
CODEX_EFFORT = "medium"
PROVIDERS = {
    "opencode": {"label": "OpenCode · MiMo V2.6 Flash Free", "model": opencode_runner.MODEL, "effort": None},
    "codex": {"label": "Codex · GPT-6 Luna · Medium", "model": CODEX_MODEL, "effort": CODEX_EFFORT},
}


def status(provider: str) -> dict[str, Any]:
    if provider == "opencode":
        return {**PROVIDERS[provider], "configured": opencode_runner.configured(),
                "binary_available": bool(os.getenv("OPENCODE_BIN") or shutil.which("opencode")),
                "auth_available": Path(os.getenv("OPENCODE_AUTH_FILE", str(Path.home() / ".local/share/opencode/auth.json"))).is_file()}
    if provider == "codex":
        binary = os.getenv("CODEX_BIN") or shutil.which("codex")
        auth = Path(os.getenv("CODEX_AUTH_FILE", "/run/secrets/codex-auth.json"))
        return {**PROVIDERS[provider], "configured": bool(binary and auth.is_file()),
                "binary_available": bool(binary), "auth_available": auth.is_file()}
    raise ValueError("Provedor de análise inválido")


def run_prompt(provider: str, prompt: str, files: list[Path] | None = None,
               timeout: int = 240, schema: dict[str, Any] | None = None) -> str:
    if provider == "opencode":
        return opencode_runner.run_prompt(prompt, files, timeout)
    if provider != "codex":
        raise ValueError("Provedor de análise inválido")
    return _run_codex(prompt, files or [], timeout, schema)


def _run_codex(prompt: str, files: list[Path], timeout: int,
               schema: dict[str, Any] | None) -> str:
    binary = os.getenv("CODEX_BIN") or shutil.which("codex")
    auth_file = Path(os.getenv("CODEX_AUTH_FILE", "/run/secrets/codex-auth.json"))
    if not binary:
        raise RuntimeError("Codex CLI não encontrado")
    if not auth_file.is_file():
        raise RuntimeError("Autenticação Codex indisponível")

    with tempfile.TemporaryDirectory(prefix="recording-codex-") as temporary:
        root = Path(temporary)
        workspace, home = root / "workspace", root / "home"
        workspace.mkdir(mode=0o700)
        home.mkdir(mode=0o700)
        # Codex gets only a short-lived, private copy of the auth file. User
        # profiles, sessions, project instructions and MCP configuration are
        # neither mounted nor loaded.
        (home / "auth.json").write_bytes(auth_file.read_bytes())
        (home / "auth.json").chmod(0o600)
        attached = []
        for index, source in enumerate(files):
            suffix = source.suffix.lower()
            if suffix not in {".jpg", ".jpeg", ".png", ".webp"}:
                raise ValueError("Codex recebe somente imagens JPEG/PNG/WebP nesta etapa")
            destination = workspace / f"frame-{index + 1:02d}{suffix}"
            shutil.copyfile(source, destination)
            destination.chmod(0o600)
            attached.append(destination)
        schema_file = None
        if schema is not None:
            schema_file = workspace / "response-schema.json"
            schema_file.write_text(json.dumps(schema), encoding="utf-8")
            schema_file.chmod(0o600)

        command = [binary, "exec", "--model", CODEX_MODEL,
                   "--config", f'model_reasoning_effort="{CODEX_EFFORT}"',
                   "--config", 'web_search="disabled"',
                   "--sandbox", "read-only", "--ephemeral", "--ignore-user-config",
                   "--disable", "shell_tool", "--disable", "multi_agent", "--disable", "memories",
                   "--disable", "goals", "--disable", "remote_plugin",
                   "--skip-git-repo-check", "--json", "-C", str(workspace)]
        if schema_file:
            command.extend(["--output-schema", str(schema_file)])
        if attached:
            command.extend(["--image", *[str(path) for path in attached]])
        environment = {"PATH": os.path.dirname(binary) + os.pathsep + "/usr/local/bin:/usr/bin:/bin",
                       "HOME": str(home), "CODEX_HOME": str(home), "NO_COLOR": "1"}
        result = subprocess.run(command, input=prompt, capture_output=True, text=True,
                                timeout=timeout, check=False, cwd=workspace, env=environment)
        if result.returncode:
            # Never persist provider stderr or event streams; they can contain
            # user content, account details, or internal paths.
            raise RuntimeError(f"Codex terminou com código {result.returncode}")
        texts = []
        for line in result.stdout.splitlines():
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            item = event.get("item", {}) if isinstance(event, dict) else {}
            if event.get("type") == "item.completed" and item.get("type") == "agent_message":
                value = item.get("text")
                if isinstance(value, str):
                    texts.append(value)
        if not texts:
            raise ValueError("Codex não retornou uma mensagem final")
        return "\n".join(texts).strip()
