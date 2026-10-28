from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path


MODEL = "opencode/mimo-v2.6-flash-free"
TIMEOUT_SECONDS = 240


def configured() -> bool:
    binary = os.getenv("OPENCODE_BIN") or shutil.which("opencode")
    auth_file = Path(os.getenv("OPENCODE_AUTH_FILE", str(Path.home() / ".local/share/opencode/auth.json")))
    return bool(binary and auth_file.is_file())


def run_prompt(prompt: str, files: list[Path] | None = None, timeout: int = TIMEOUT_SECONDS) -> str:
    binary = os.getenv("OPENCODE_BIN") or shutil.which("opencode")
    if not binary:
        raise RuntimeError("OpenCode CLI não encontrado")
    command = [binary, "run", "--model", MODEL, "--format", "json", "--agent", "plan"]
    for path in files or []:
        command.extend(["--file", str(path)])
    result = subprocess.run(command, input=prompt, capture_output=True, text=True, timeout=timeout, check=False)
    if result.returncode:
        # CLI stderr can contain prompt or account details; persist only a safe status.
        raise RuntimeError(f"OpenCode terminou com código {result.returncode}")
    texts = []
    for line in result.stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        part = event.get("part", {}) if isinstance(event, dict) else {}
        if event.get("type") == "text" and isinstance(part.get("text"), str):
            texts.append(part["text"])
    if not texts:
        raise ValueError("OpenCode não retornou texto de resposta")
    return "\n".join(texts).strip()
