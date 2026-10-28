from __future__ import annotations

import json
import os
import re
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATA_DIR = Path(os.getenv("APP_DATA_DIR", "data")).resolve()
PROJECTS_DIR = DATA_DIR / "projects"
UPLOADS_DIR = DATA_DIR / "sources"
EXPORTS_DIR = DATA_DIR / "exports"
_TRANSCRIPTION_MODEL_IDS = {"tiny", "base", "small", "medium", "large-v3"}
_configured_model = os.getenv("WHISPER_MODEL", "medium")
DEFAULT_ANALYSIS_MODEL = _configured_model if _configured_model in _TRANSCRIPTION_MODEL_IDS else "medium"
for directory in (PROJECTS_DIR, UPLOADS_DIR, EXPORTS_DIR):
    directory.mkdir(parents=True, exist_ok=True)

_lock = threading.RLock()
AI_SETTINGS_PATH = DATA_DIR / "ai-settings.json"


def get_ai_provider() -> str:
    return get_ai_settings()["provider"]


def get_ai_settings() -> dict[str, Any]:
    try:
        saved = json.loads(AI_SETTINGS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, AttributeError):
        saved = {}
    if not isinstance(saved, dict):
        saved = {}
    provider = saved.get("provider")
    frame_limit = saved.get("visual_frame_limit", 8)
    if not isinstance(frame_limit, int) or isinstance(frame_limit, bool) or not 2 <= frame_limit <= 1024:
        frame_limit = 8
    return {"provider": provider if provider in {"opencode", "codex"} else "opencode",
            "visual_frame_limit": frame_limit}


def save_ai_provider(provider: str) -> None:
    if provider not in {"opencode", "codex"}:
        raise ValueError("Invalid AI provider")
    save_ai_settings(provider=provider)


def save_ai_settings(provider: str | None = None, visual_frame_limit: int | None = None) -> None:
    current = get_ai_settings()
    provider = current["provider"] if provider is None else provider
    visual_frame_limit = current["visual_frame_limit"] if visual_frame_limit is None else visual_frame_limit
    if provider not in {"opencode", "codex"}:
        raise ValueError("Invalid AI provider")
    if not isinstance(visual_frame_limit, int) or isinstance(visual_frame_limit, bool) or not 2 <= visual_frame_limit <= 1024:
        raise ValueError("Invalid visual frame limit")
    AI_SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary = AI_SETTINGS_PATH.with_suffix(".json.tmp")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as output:
            json.dump({"provider": provider, "visual_frame_limit": visual_frame_limit}, output)
        temporary.chmod(0o600)
        temporary.replace(AI_SETTINGS_PATH)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def slug(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9_-]+", "-", value).strip("-").lower()
    return value[:60] or "recording"


def project_path(project_id: str) -> Path:
    if not re.fullmatch(r"[a-f0-9]{32}", project_id):
        raise ValueError("Invalid project ID")
    return PROJECTS_DIR / project_id


def load(project_id: str) -> dict[str, Any]:
    path = project_path(project_id) / "project.json"
    with _lock:
        if not path.exists():
            raise FileNotFoundError("Project not found")
        return json.loads(path.read_text(encoding="utf-8"))


def save(project: dict[str, Any]) -> dict[str, Any]:
    project["updated_at"] = now()
    directory = project_path(project["id"])
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / "project.json"
    temporary = target.with_suffix(".json.tmp")
    with _lock:
        temporary.write_text(json.dumps(project, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(target)
    return project


def create_project(filename: str, source_path: Path, metadata: dict[str, Any]) -> dict[str, Any]:
    project_id = uuid.uuid4().hex
    project = {
        "id": project_id,
        "name": Path(filename).stem,
        "source": str(source_path.resolve()),
        "created_at": now(),
        "updated_at": now(),
        "status": "imported",
        "error": None,
        "metadata": metadata,
        "analysis_model": DEFAULT_ANALYSIS_MODEL,
        "source_language": "pt",
        "transcript": [],
        "edits": [],
        "shorts": [],
        "youtube_cuts": [],
        "visual_analysis": None,
        "color_grade": {"enabled": False, "intensity": 1.0},
        "captions": {"pt": [], "en": []},
        "translated_languages": [],
        "review": {"approved": False, "approved_at": None},
        "exports": [],
        "uploads": [],
        "job": None,
    }
    return save(project)


def list_projects() -> list[dict[str, Any]]:
    items = []
    for path in PROJECTS_DIR.glob("*/project.json"):
        try:
            items.append(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError):
            continue
    return sorted(items, key=lambda item: item.get("updated_at", ""), reverse=True)


def list_project_summaries() -> list[dict[str, Any]]:
    fields = ("id", "name", "status", "metadata", "created_at", "updated_at", "analysis_model", "ai_model")
    return [{key: item[key] for key in fields if key in item} for item in list_projects()]


def recover_interrupted_jobs() -> None:
    """On single-server startup, make orphaned in-process jobs visible and recoverable."""
    for project in list_projects():
        status = project.get("status")
        if status not in {"analyzing", "rendering", "uploading"}:
            continue
        stage = (project.get("job") or {}).get("stage")
        message = "A operação foi interrompida pelo reinício do servidor."
        if status == "uploading":
            project["status"] = "upload-failed"
            for asset in project.get("exports", []):
                if asset.get("upload_status") == "uploading":
                    asset.update({"upload_status": "uploading-unknown", "upload_error": message})
                for track in asset.get("caption_uploads", []):
                    if track.get("status") == "uploading":
                        track.update({"status": "uploading-unknown", "error": message})
                        caption = next((item for item in project["exports"] if item.get("filename") == track.get("filename")), None)
                        if caption:
                            caption.update({"upload_status": "uploading-unknown", "upload_error": message})
            message += " Confira o YouTube Studio antes de repetir o envio."
        elif status == "rendering" or stage == "translating":
            project["status"] = "review-ready"
            message += " Revise e inicie novamente a etapa interrompida."
        else:
            project["status"] = "failed" if stage in {"queued", "visual-analysis", "visual-review", "transcribing"} else "review-ready"
            run = project.get("analysis_run")
            if isinstance(run, dict):
                run["status"] = "partial"
                for capability in run.get("capabilities", {}).values():
                    if capability.get("status") in {"running", "pending"}:
                        capability["status"] = "failed"
            message += " Retome a etapa ou inicie a análise novamente."
        project["error"] = message
        project["job"] = {"stage": "interrupted", "progress": 0.0, "message": message}
        save(project)
