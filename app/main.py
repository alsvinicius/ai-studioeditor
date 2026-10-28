from __future__ import annotations

import json
import math
import os
import re
import threading
import time
from html import escape
from pathlib import Path
from typing import Any
from urllib.parse import unquote

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles

from . import ai_analysis, ai_providers, media, mimo_vision, state, transcript_quality, visual

_HERE = Path(__file__).parent
_SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]
_oauth_state = state.DATA_DIR / "youtube-oauth-state.json"
app = FastAPI(title="OBS Post Production", docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=_HERE / "static"), name="static")


@app.on_event("startup")
def recover_interrupted_jobs() -> None:
    state.recover_interrupted_jobs()


@app.get("/", response_class=HTMLResponse)
def home():
    return FileResponse(_HERE / "static" / "index.html", headers={"Cache-Control": "no-store"})


@app.get("/settings", response_class=HTMLResponse)
def settings_page():
    return FileResponse(_HERE / "static" / "index.html", headers={"Cache-Control": "no-store"})


@app.get("/projects/{project_id}", response_class=HTMLResponse)
def project_page(project_id: str):
    return FileResponse(_HERE / "static" / "index.html", headers={"Cache-Control": "no-store"})


@app.get("/api/health")
def health():
    provider = state.get_ai_provider()
    selected = ai_providers.status(provider)
    return {"ok": True, "ffmpeg": _has("ffmpeg"), "ffprobe": _has("ffprobe"), "youtube_authorized": _token().is_file(), "ai_model": selected["model"], "ai_configured": selected["configured"]}


@app.get("/api/settings/youtube")
def youtube_settings():
    return {
        "configured": _oauth_secrets().is_file(),
        "connected": _token().is_file(),
        "redirect_uri": os.getenv("YOUTUBE_REDIRECT_URI", "http://localhost:8000/api/youtube/callback"),
        "visibility": "private",
        "caption_languages": [media.LANGUAGES["pt"]["locale"], *[media.LANGUAGES[language]["locale"] for language in media.CAPTION_TARGET_LANGUAGES]],
    }


@app.get("/api/settings/ai")
def ai_settings():
    selected = state.get_ai_provider()
    active = ai_providers.status(selected)
    return {"provider": selected, "model": active["model"], "effort": active["effort"],
            "configured": active["configured"], "visual_frame_limit": state.get_ai_settings()["visual_frame_limit"],
            "visual_frame_limit_min": 2, "visual_frame_limit_max": 1024,
            "options": {name: ai_providers.status(name) for name in ai_providers.PROVIDERS}}


@app.put("/api/settings/ai")
async def update_ai_settings(request: Request):
    try:
        body = await request.json()
    except Exception as exc:
        raise HTTPException(400, "Configuração de IA inválida") from exc
    provider = body.get("provider") if isinstance(body, dict) else None
    if not isinstance(body, dict):
        raise HTTPException(422, "Configuração de IA inválida")
    current = state.get_ai_settings()
    if provider is None:
        provider = current["provider"]
    if not isinstance(provider, str) or provider not in ai_providers.PROVIDERS:
        raise HTTPException(422, "Escolha OpenCode ou Codex")
    frame_limit = body.get("visual_frame_limit", current["visual_frame_limit"])
    if not isinstance(frame_limit, int) or isinstance(frame_limit, bool) or not 2 <= frame_limit <= 1024:
        raise HTTPException(422, "Escolha entre 2 e 1024 frames visuais")
    state.save_ai_settings(provider=provider, visual_frame_limit=frame_limit)
    return ai_settings()


def _ensure_youtube_idle():
    if any(project.get("status") == "uploading" for project in state.list_projects()):
        raise HTTPException(409, "Aguarde o envio em andamento antes de alterar a conexão do YouTube")


@app.put("/api/settings/youtube/client")
async def configure_youtube_client(request: Request):
    _ensure_youtube_idle()
    raw = await request.body()
    if len(raw) > 65536:
        raise HTTPException(413, "O JSON OAuth deve ter até 64 KB")
    try:
        data = json.loads(raw)
        client = data.get("web") if isinstance(data, dict) else None
        if not isinstance(client, dict) or not all(isinstance(client.get(key), str) and client[key].strip() for key in ("client_id", "client_secret", "auth_uri", "token_uri")):
            raise ValueError()
        if client["auth_uri"] not in {"https://accounts.google.com/o/oauth2/auth", "https://accounts.google.com/o/oauth2/v2/auth"} or client["token_uri"] not in {"https://oauth2.googleapis.com/token", "https://accounts.google.com/o/oauth2/token"}:
            raise ValueError()
        redirects = client.get("redirect_uris")
        if not isinstance(redirects, list) or not all(isinstance(uri, str) for uri in redirects):
            raise ValueError()
        redirect_uri = youtube_settings()["redirect_uri"]
        if redirect_uri not in redirects:
            raise HTTPException(422, f"Adicione {redirect_uri} aos URIs de redirecionamento do cliente OAuth no Google Cloud")
    except (json.JSONDecodeError, ValueError, TypeError, UnicodeDecodeError):
        raise HTTPException(422, "Escolha o JSON de uma credencial OAuth Google do tipo aplicativo Web")
    target = state.DATA_DIR / "youtube-client-secret.json"
    temporary = target.with_suffix(".json.tmp")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    os.fchmod(descriptor, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as output:
        json.dump(data, output)
    temporary.chmod(0o600)
    temporary.replace(target)
    _token().unlink(missing_ok=True)
    _oauth_state.unlink(missing_ok=True)
    return youtube_settings()


@app.delete("/api/settings/youtube/connection")
def disconnect_youtube():
    _ensure_youtube_idle()
    _token().unlink(missing_ok=True)
    _oauth_state.unlink(missing_ok=True)
    return youtube_settings()


@app.get("/api/projects")
def projects():
    return state.list_project_summaries()


@app.get("/api/projects/{project_id}")
def get_project(project_id: str):
    return _load(project_id)


@app.put("/api/projects/{project_id}/name")
async def rename_project(project_id: str, request: Request):
    project = _load(project_id)
    if project.get("status") in {"analyzing", "rendering", "uploading"}:
        raise HTTPException(409, "Aguarde o processamento terminar antes de renomear o projeto")
    try:
        body = await request.json()
        name = body.get("name") if isinstance(body, dict) else None
    except Exception as exc:
        raise HTTPException(400, "Nome de projeto inválido") from exc
    if not isinstance(name, str) or not name.strip():
        raise HTTPException(422, "Informe um nome para o projeto")
    name = re.sub(r"[\\/\x00-\x1f]", " ", name).strip()
    name = re.sub(r"\s+", " ", name)[:120].strip()
    if not name:
        raise HTTPException(422, "Informe um nome válido para o projeto")
    project["name"] = name
    state.save(project)
    return project


@app.post("/api/projects/upload")
async def upload_recording(request: Request):
    filename = unquote(request.headers.get("x-file-name", "recording.mp4"))
    suffix = Path(filename).suffix.lower()
    if suffix not in {".mkv", ".mp4"}:
        raise HTTPException(400, "Escolha uma gravação MKV ou MP4")
    name = re.sub(r"[^\w. -]", "_", Path(filename).name).strip() or f"recording{suffix}"
    temporary = state.UPLOADS_DIR / f"upload-{time.time_ns()}{suffix}"
    try:
        with temporary.open("wb") as output:
            async for chunk in request.stream():
                output.write(chunk)
        metadata = media.ffprobe(temporary)
        source = state.UPLOADS_DIR / f"{temporary.stem}-{name}"
        temporary.replace(source)
        return state.create_project(name, source, metadata)
    except ValueError as exc:
        temporary.unlink(missing_ok=True)
        raise HTTPException(422, str(exc)) from exc
    except Exception as exc:
        temporary.unlink(missing_ok=True)
        raise HTTPException(500, f"Falha ao importar gravação: {exc}") from exc


@app.get("/api/projects/{project_id}/source")
def source(project_id: str):
    project = _load(project_id)
    path = Path(project["source"])
    if not path.is_file():
        raise HTTPException(404, "Arquivo-fonte não encontrado")
    kind = "video/mp4" if path.suffix.lower() == ".mp4" else "video/x-matroska"
    return FileResponse(path, media_type=kind)


@app.get("/api/projects/{project_id}/visual-preview")
def visual_preview(project_id: str, intensity: float = 1.0, crop_x: float = 0.5, scene_id: str | None = None):
    project = _load(project_id)
    analysis = project.get("visual_analysis") or {}
    if analysis.get("status") != "complete":
        raise HTTPException(409, "Conclua a análise visual antes de gerar a prévia")
    if not 0 <= intensity <= 1 or not 0 <= crop_x <= 1:
        raise HTTPException(422, "Intensidade e posição do crop devem estar entre 0 e 1")
    path = Path(project["source"])
    if not path.is_file():
        raise HTTPException(404, "Arquivo-fonte não encontrado")
    try:
        segments = analysis.get("grade_segments", [])
        segment = next((item for item in segments if item.get("id") == scene_id), None) if scene_id else None
        if scene_id and visual.legacy_incomplete_review(analysis):
            raise HTTPException(422, "A classificação visual antiga está incompleta; reanalise para revisar cores")
        if scene_id and (not segment or segment.get("layout") != "camera" or segment.get("status") != "reviewable"):
            raise HTTPException(422, "Este intervalo não está classificado como câmera; as cores são preservadas")
        suggestion = segment.get("suggestion", {}) if segment else analysis.get("grade_suggestion", {})
        preserve = segment is None and analysis.get("grade_policy", {}).get("mode") == "preserve"
        if preserve:
            suggestion = {"brightness": 0, "contrast": 1, "saturation": 1}
        moments = None
        if segment:
            left, right = float(segment["start"]), float(segment["end"])
            edge = min(0.25, max(0.02, (right-left)*0.1))
            moments = [left+edge, (left+right)/2, max(left+edge, right-edge)]
        contact_sheet = visual.preview_contact_sheet(
            path,
            float(project["metadata"]["duration"]),
            suggestion,
            intensity=intensity,
            crop_x=crop_x,
            preserve_colors=preserve,
            moments=moments,
        )
        return Response(content=contact_sheet, media_type="image/jpeg", headers={"Cache-Control": "no-store"})
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@app.post("/api/projects/{project_id}/analyze")
async def analyze(project_id: str, request: Request):
    project = _load(project_id)
    if project.get("status") in {"analyzing", "rendering", "uploading"}:
        raise HTTPException(409, "Este projeto já está ocupado")
    raw_body = await request.body()
    try:
        body = json.loads(raw_body) if raw_body else {}
    except json.JSONDecodeError as exc:
        raise HTTPException(400, "Opções de análise inválidas") from exc
    if not isinstance(body, dict):
        raise HTTPException(400, "Opções de análise inválidas")
    model_name = body.get("model", project.get("analysis_model", media.default_transcription_model()))
    if not isinstance(model_name, str) or model_name not in media.TRANSCRIPTION_MODELS:
        raise HTTPException(422, "Selecione um modelo de transcrição disponível")
    source_language = body.get("source_language", "pt")
    if not isinstance(source_language, str) or source_language not in media.LANGUAGES:
        raise HTTPException(422, "Selecione um idioma de gravação disponível")
    provider = state.get_ai_provider()
    visual_frame_limit = state.get_ai_settings()["visual_frame_limit"]
    selected_provider = ai_providers.status(provider)
    visual_review = body.get("visual_review", True)
    if not isinstance(visual_review, bool):
        raise HTTPException(422, "Opção de análise visual inválida")
    if not selected_provider["configured"]:
        label = "OpenCode" if provider == "opencode" else "Codex"
        raise HTTPException(422, f"Instale e autentique o provedor selecionado ({label}) para analisar")
    project["analysis_model"] = model_name
    project["source_language"] = source_language
    project["translated_languages"] = []
    project["captions"] = {source_language: []}
    project["ai_provider"] = provider
    project["ai_model"] = selected_provider["model"]
    project["ai_effort"] = selected_provider["effort"]
    project["visual_frame_limit"] = visual_frame_limit
    project["analysis_generation"] = int(project.get("analysis_generation", 0)) + 1
    project["analysis_run"] = {"generation": project["analysis_generation"], "provider": provider,
        "model": selected_provider["model"], "effort": selected_provider["effort"],
        "visual_frame_limit": visual_frame_limit, "status": "running", "capabilities": {"semantic": {"status": "pending"},
        "visual": {"status": "pending" if visual_review else "skipped"}, "audio": {"status": "pending"}}}
    project["status"], project["error"] = "analyzing", None
    project["job"] = {"stage": "queued", "progress": 0.0, "message": f"Na fila · Whisper {model_name} · {media.LANGUAGES[source_language]['label']}"}
    state.save(project)
    project["visual_review_requested"] = visual_review
    state.save(project)
    threading.Thread(target=_analysis_job, args=(project_id, model_name, visual_review, source_language, provider, visual_frame_limit), daemon=True).start()
    return project


@app.put("/api/projects/{project_id}/transcript")
def save_transcript(project_id: str, body: dict[str, Any]):
    project = _load(project_id)
    if project.get("status") != "review-ready":
        raise HTTPException(409, "A transcrição só pode ser revisada quando a análise estiver pronta")
    submitted = body.get("segments")
    existing = project.get("transcript", [])
    if not isinstance(submitted, list) or len(submitted) != len(existing):
        raise HTTPException(422, "A lista de segmentos da transcrição é inválida")
    updated = []
    for old, new in zip(existing, submitted):
        if not isinstance(new, dict) or new.get("id") != old.get("id") or not isinstance(new.get("text"), str) or len(new["text"]) > 2000:
            raise HTTPException(422, "Não altere a estrutura ou os tempos dos segmentos")
        updated.append({**old, "text": new["text"].strip()})
    changed = any(old.get("text") != new.get("text") for old, new in zip(existing, updated))
    project["transcript"] = updated
    source = project.get("source_language", "pt")
    if changed:
        project["captions"] = {source: updated}
        project["translated_languages"] = []
        project["transcript_edited_at"] = state.now()
        if project.get("ai_analysis"):
            project["ai_analysis"]["status"] = "stale"
            project["ai_analysis"]["stale_reason"] = "transcript-edited"
            project.setdefault("analysis_run", {}).setdefault("capabilities", {})["semantic"] = {"status": "stale"}
            project["analysis_run"]["status"] = "partial"
    else:
        project.setdefault("captions", {})[source] = updated
    state.save(project)
    return project


@app.post("/api/projects/{project_id}/analysis/retry")
async def retry_analysis(project_id: str, request: Request):
    project = _load(project_id)
    if project.get("status") != "review-ready":
        raise HTTPException(409, "A retomada só está disponível durante a revisão")
    try:
        body = await request.json()
    except Exception as exc:
        raise HTTPException(400, "Etapa de análise inválida") from exc
    capability = body.get("capability") if isinstance(body, dict) else None
    if capability not in {"semantic", "visual", "audio"}:
        raise HTTPException(422, "Escolha análise de texto, imagem ou áudio")
    if capability == "semantic" and not project.get("transcript"):
        raise HTTPException(409, "Nenhuma fala foi transcrita; revise o áudio e execute uma nova análise")
    if capability == "visual" and (project.get("color_grade") or {}).get("segments"):
        raise HTTPException(409, "A retomada visual substituiria cenas já revisadas. Preserve os ajustes e inicie uma nova análise em um projeto separado.")
    provider = project.get("ai_provider", "opencode")
    if capability == "visual":
        run = project.setdefault("analysis_run", {})
        used = int(run.get("visual_frames_used", 0))
        limit = int(project.get("visual_frame_limit", 8))
        if limit - used < 1:
            raise HTTPException(409, "O limite visual desta análise já foi consumido; aumente a preferência para novas análises")
    if capability != "audio" and not ai_providers.status(provider)["configured"]:
        raise HTTPException(422, f"O provedor original ({provider}) não está disponível; a retomada mantém a origem desta execução")
    capability_state = project.setdefault("analysis_run", {}).setdefault("capabilities", {}).setdefault(capability, {})
    if int(capability_state.get("retry_count", 0)) >= 1:
        raise HTTPException(409, "A única retomada desta etapa já foi usada; revise os resultados atuais")
    project["analysis_generation"] = int(project.get("analysis_generation", 1)) + 1
    run = project.setdefault("analysis_run", {})
    run["status"] = "running"
    capability_state.update({"status": "running", "retry_count": int(capability_state.get("retry_count", 0)) + 1})
    project["status"], project["error"] = "analyzing", None
    project["job"] = {"stage": {"semantic": "semantic-analysis", "visual": "visual-review", "audio": "audio-analysis"}[capability],
                       "progress": 0.0, "message": f"Retomando somente a etapa de {capability}…"}
    state.save(project)
    threading.Thread(target=_retry_analysis_job, args=(project_id, capability, provider,
                       project["analysis_generation"]), daemon=True).start()
    return project


def _retry_analysis_job(project_id: str, capability: str, provider: str, generation: int) -> None:
    try:
        project = _load(project_id)
        model = ai_providers.PROVIDERS[provider]["model"]
        if capability == "audio":
            silence = media.detect_silence(Path(project["source"]), float(project["metadata"]["duration"]))
            project = _load(project_id)
            if project.get("analysis_generation") != generation:
                return
            project["audio_analysis"] = {"status": "complete", "provider": "ffmpeg", "silence_intervals": silence,
                                          "noise_db": -35.0, "min_duration": 1.2}
            rule_edits = media.suggest_edits(project.get("transcript", []), float(project["metadata"]["duration"]))
            rule_edits.extend(media.suggest_audio_silence_edits(project.get("transcript", []),
                float(project["metadata"]["duration"]), silence))
            previous = list(project.get("edits", []))
            merged = ai_analysis.merge_edits(rule_edits, [item for item in previous if item.get("source") != "rules"])
            project["edits"] = ai_analysis.preserve_decisions(merged, previous)
            project.setdefault("analysis_run", {}).setdefault("capabilities", {}).setdefault("audio", {}).update(
                {"status": "complete", "intervals": len(silence)})
        elif capability == "semantic":
            previous_edits = list(project.get("edits", []))
            previous_shorts = list(project.get("shorts", []))
            previous_youtube = list(project.get("youtube_cuts", []))
            edits, cuts, result = ai_analysis.analyze_transcript(project["transcript"],
                float(project["metadata"]["duration"]), source_language=project.get("source_language", "pt"), provider=provider)
            project = _load(project_id)
            if project.get("analysis_generation") != generation:
                return
            project.setdefault("analysis_run", {})["provider_result"] = result.get(provider, {})
            if result.get(provider, {}).get("status") != "complete":
                project.setdefault("ai_analysis", {}).update({"provider": provider, "model": model,
                    "effort": ai_providers.PROVIDERS[provider]["effort"], "transcript": result.get(provider, {}),
                    "status": "partial"})
                project.setdefault("analysis_run", {}).setdefault("capabilities", {}).setdefault("semantic", {}).update(
                    {"status": "failed"})
                project["analysis_run"]["status"] = "partial"
                project["status"], project["error"] = "review-ready", None
                project["job"] = {"stage": "partial", "progress": 1.0,
                    "message": "Análise de texto indisponível; resultados anteriores preservados"}
                state.save(project)
                return
            local_edits = [item for item in project.get("edits", []) if item.get("source") != provider]
            project["edits"] = ai_analysis.preserve_decisions(ai_analysis.merge_edits(local_edits, edits), previous_edits)
            project["shorts"] = ai_analysis.preserve_decisions(ai_analysis.merge_shorts(project.get("shorts", []),
                [item for item in cuts if item.get("format") != "horizontal"], project["edits"]), previous_shorts)
            project["youtube_cuts"] = ai_analysis.preserve_decisions(ai_analysis.merge_youtube_cuts(
                [item for item in cuts if item.get("format") == "horizontal"], project["edits"]), previous_youtube)
            project.setdefault("ai_analysis", {}).update({"provider": provider, "model": model,
                "effort": ai_providers.PROVIDERS[provider]["effort"], "transcript": result.get(provider, {}),
                "status": "complete" if result.get(provider, {}).get("status") == "complete" else "partial"})
            project.setdefault("analysis_run", {}).setdefault("capabilities", {}).setdefault("semantic", {}).update(
                {"status": "complete" if result.get(provider, {}).get("status") == "complete" else "failed"})
        else:
            run = project.get("analysis_run", {})
            remaining = int(project.get("visual_frame_limit", 8)) - int(run.get("visual_frames_used", 0))
            scene = mimo_vision.review_scenes(Path(project["source"]), float(project["metadata"]["duration"]), provider,
                                              remaining)
            project = _load(project_id)
            if project.get("analysis_generation") != generation:
                return
            project.setdefault("analysis_run", {})["visual_frames_used"] = int(
                project.get("analysis_run", {}).get("visual_frames_used", 0)) + scene.get("sample_count", 0)
            project["analysis_run"]["visual_grid_images_used"] = int(
                project["analysis_run"].get("visual_grid_images_used", 0)) + scene.get("grid_image_count", 0)
            project.setdefault("visual_analysis", {})["scene_review"] = scene
            project["visual_analysis"]["grade_segments"] = visual.grade_segments(
                Path(project["source"]), float(project["metadata"]["duration"]), scene.get("scene_segments", []),
                int(project["metadata"]["width"]), int(project["metadata"]["height"]))
            project.setdefault("ai_analysis", {}).update({"provider": provider, "model": model,
                "effort": ai_providers.PROVIDERS[provider]["effort"], "visual": {"status": scene.get("status", "partial")}})
            project.setdefault("analysis_run", {}).setdefault("capabilities", {}).setdefault("visual", {}).update(
                {"status": scene.get("status", "partial"), "frames": project["analysis_run"].get("visual_frames_used", 0),
                 "classified_frames": scene.get("classified_count", 0), "requested_frames": scene.get("requested_sample_count", 0),
                 "last_attempt_frames": scene.get("sample_count", 0),
                 "grid_images": project["analysis_run"].get("visual_grid_images_used", 0),
                 "last_attempt_grid_images": scene.get("grid_image_count", 0)})
        capabilities = project.setdefault("analysis_run", {}).setdefault("capabilities", {})
        project["analysis_run"]["status"] = "partial" if any(
            item.get("status") in {"failed", "unavailable", "partial", "stale"} for item in capabilities.values()
        ) else "complete"
        project["analysis_run"]["generation"] = generation
        project["status"] = "review-ready"
        project["job"] = {"stage": "partial" if project["analysis_run"]["status"] == "partial" else "complete",
                           "progress": 1.0, "message": f"Etapa {capability} retomada"}
        project["error"] = None
        state.save(project)
    except Exception as exc:
        project = _load(project_id)
        if project.get("analysis_generation") == generation:
            if capability == "visual":
                attempted = int(getattr(exc, "visual_frames_attempted", 0))
                run = project.setdefault("analysis_run", {})
                run["visual_frames_used"] = int(run.get("visual_frames_used", 0)) + attempted
                attempted_grids = int(getattr(exc, "visual_grid_images_attempted", 0))
                run["visual_grid_images_used"] = int(run.get("visual_grid_images_used", 0)) + attempted_grids
                visual_capability = run.setdefault("capabilities", {}).setdefault("visual", {})
                visual_capability["frames"] = run["visual_frames_used"]
                visual_capability["last_attempt_frames"] = attempted
                visual_capability["grid_images"] = run["visual_grid_images_used"]
                visual_capability["last_attempt_grid_images"] = attempted_grids
            project["status"], project["error"] = "review-ready", type(exc).__name__
            project.setdefault("analysis_run", {}).setdefault("capabilities", {}).setdefault(capability, {}).update(
                {"status": "failed", "error": type(exc).__name__})
            project["analysis_run"]["status"] = "partial"
            project["job"] = {"stage": "partial", "progress": 1.0, "message": f"Etapa {capability} indisponível; resultados anteriores preservados"}
            state.save(project)


@app.post("/api/projects/{project_id}/translate")
def translate_captions(project_id: str, body: dict[str, Any]):
    project = _load(project_id)
    if project.get("status") != "review-ready":
        raise HTTPException(409, "Aguarde a análise terminar antes de traduzir")
    source = project.get("source_language", "pt")
    languages = body.get("languages")
    if not isinstance(languages, list) or not languages or any(not isinstance(item, str) or item not in media.LANGUAGES or item == source for item in languages):
        raise HTTPException(422, "Selecione ao menos um idioma de destino válido")
    languages = list(dict.fromkeys(languages))
    project["translation_targets"] = languages
    project["status"], project["error"] = "analyzing", None
    project["job"] = {"stage": "translating", "progress": 0.0, "message": "Preparando tradução local…"}
    state.save(project)
    threading.Thread(target=_translation_job, args=(project_id, languages), daemon=True).start()
    return project


@app.put("/api/projects/{project_id}/review")
def review(project_id: str, body: dict[str, Any]):
    project = _load(project_id)
    if project.get("status") != "review-ready":
        raise HTTPException(409, "O projeto ainda não está pronto para revisão")
    _update_decisions(project, body)
    project["review"] = {"approved": False, "approved_at": None}
    state.save(project)
    return project


@app.post("/api/projects/{project_id}/export")
def export(project_id: str):
    project = _load(project_id)
    if project.get("status") != "review-ready":
        raise HTTPException(409, "Analise e revise o projeto antes de exportar")
    project["status"], project["error"] = "rendering", None
    project["job"] = {"stage": "rendering", "progress": 0.0, "message": "Preparando exportação…"}
    state.save(project)
    threading.Thread(target=_export_job, args=(project_id,), daemon=True).start()
    return project


@app.get("/api/projects/{project_id}/assets/{asset_id}")
def get_asset(project_id: str, asset_id: str):
    project = _load(project_id)
    item = next((asset for asset in project.get("exports", []) if asset["id"] == asset_id), None)
    if not item or not Path(item["path"]).is_file():
        raise HTTPException(404, "Arquivo exportado não encontrado")
    return FileResponse(item["path"], filename=item["filename"])


@app.put("/api/projects/{project_id}/assets")
def select_assets(project_id: str, body: dict[str, Any]):
    project = _load(project_id)
    if project.get("status") not in {"export-ready", "uploaded", "upload-failed"}:
        raise HTTPException(409, "Exporte o projeto antes de selecionar arquivos")
    selected = {item.get("id"): bool(item.get("youtube_selected")) for item in body.get("assets", [])}
    for asset in project.get("exports", []):
        if asset["type"] in {"master", "short", "youtube-cut"} and asset["id"] in selected:
            asset["youtube_selected"] = selected[asset["id"]]
    project.setdefault("youtube", {}).update(body.get("youtube", {}))
    project["review"] = {"approved": False, "approved_at": None}
    state.save(project)
    return project


@app.post("/api/youtube/connect")
def youtube_connect():
    secrets = _oauth_secrets()
    if not secrets.is_file():
        raise HTTPException(400, "Importe o JSON OAuth do Google em Configurações → YouTube antes de conectar")
    try:
        from google_auth_oauthlib.flow import Flow
        flow = Flow.from_client_secrets_file(str(secrets), scopes=_SCOPES)
        flow.redirect_uri = os.getenv("YOUTUBE_REDIRECT_URI", "http://localhost:8000/api/youtube/callback")
        url, value = flow.authorization_url(access_type="offline", include_granted_scopes="true", prompt="consent")
        _oauth_state.write_text(json.dumps({"state": value, "redirect_uri": flow.redirect_uri}), encoding="utf-8")
        _oauth_state.chmod(0o600)
        return {"authorization_url": url}
    except Exception as exc:
        raise HTTPException(400, f"Não foi possível iniciar OAuth: {exc}") from exc


@app.get("/api/youtube/callback")
def youtube_callback(code: str | None = None, state: str | None = None, error: str | None = None):
    if error:
        return HTMLResponse(f"<h1>Autorização não concluída</h1><p>{escape(error)}</p><a href='/settings'>Voltar</a>", status_code=400)
    if not code or not state or not _oauth_state.is_file():
        return HTMLResponse("<h1>Retorno OAuth inválido</h1><a href='/settings'>Voltar</a>", status_code=400)
    expected = json.loads(_oauth_state.read_text(encoding="utf-8"))
    if state != expected.get("state"):
        return HTMLResponse("<h1>Estado OAuth não corresponde</h1><a href='/settings'>Voltar</a>", status_code=400)
    try:
        from google_auth_oauthlib.flow import Flow
        flow = Flow.from_client_secrets_file(str(_oauth_secrets()), scopes=_SCOPES, state=state)
        flow.redirect_uri = expected["redirect_uri"]
        flow.fetch_token(code=code)
        _token().write_text(flow.credentials.to_json(), encoding="utf-8")
        _token().chmod(0o600)
        _oauth_state.unlink(missing_ok=True)
        return HTMLResponse("<h1>YouTube conectado</h1><p>A conexão está disponível para todos os projetos.</p><a href='/settings'>Voltar às configurações</a>")
    except Exception as exc:
        return HTMLResponse(f"<h1>Falha ao concluir OAuth</h1><p>{escape(str(exc))}</p><a href='/settings'>Voltar</a>", status_code=400)


@app.post("/api/projects/{project_id}/youtube/retry-caption")
def retry_caption(project_id: str, body: dict[str, Any]):
    project = _load(project_id)
    if project.get("status") != "upload-failed" or body.get("confirmed_absent") is not True:
        raise HTTPException(409, "Confirme no YouTube Studio que esta faixa não foi criada antes de liberar nova tentativa")
    asset = next((item for item in project.get("exports", []) if item["id"] == body.get("asset_id") and item["type"] == "caption" and item["filename"].endswith(".srt")), None)
    if asset is None or asset.get("upload_status") != "uploading-unknown":
        raise HTTPException(404, "Faixa com resultado desconhecido não encontrada")
    track = next((track for video in project.get("exports", []) for track in video.get("caption_uploads", []) if track.get("filename") == asset["filename"]), None)
    if track is None or track.get("status") != "uploading-unknown":
        raise HTTPException(409, "Não encontrei um envio incerto correspondente a esta faixa")
    track.update({"status": "not-uploaded", "error": None})
    asset.update({"upload_status": "not-uploaded", "upload_error": None})
    state.save(project)
    return project


@app.post("/api/projects/{project_id}/youtube/retry-video")
def retry_video(project_id: str, body: dict[str, Any]):
    project = _load(project_id)
    if project.get("status") != "upload-failed" or body.get("confirmed_absent") is not True:
        raise HTTPException(409, "Confirme no YouTube Studio que este vídeo não foi criado antes de liberar nova tentativa")
    asset = next((item for item in project.get("exports", []) if item.get("id") == body.get("asset_id")
                  and item.get("type") in {"master", "short", "youtube-cut"}), None)
    if asset is None or asset.get("upload_status") != "uploading-unknown" or asset.get("youtube_id"):
        raise HTTPException(404, "Vídeo com resultado desconhecido não encontrado")
    asset.update({"upload_status": "not-uploaded", "upload_error": None})
    state.save(project)
    return project


@app.post("/api/projects/{project_id}/youtube/upload")
def upload_to_youtube(project_id: str, body: dict[str, Any]):
    project = _load(project_id)
    if body.get("approved") is not True:
        raise HTTPException(400, "A aprovação explícita é obrigatória antes do upload")
    if project.get("status") not in {"export-ready", "upload-failed"}:
        raise HTTPException(409, "O projeto precisa estar exportado")
    if not _token().is_file():
        raise HTTPException(401, "Conecte uma conta do YouTube antes de enviar")
    selected = [item for item in project.get("exports", []) if item.get("youtube_selected") and item["type"] in {"master", "short", "youtube-cut"}]
    if not selected:
        raise HTTPException(400, "Selecione pelo menos um vídeo para enviar")
    for item in selected:
        languages = _caption_languages(project)
        caption_ids = [f"caption-{language}" for language in languages] if item["id"] == "master" else [f"{item['id']}-caption-{language}" for language in languages]
        captions = {asset["id"]: asset for asset in project.get("exports", []) if asset["id"] in caption_ids}
        if len(captions) != len(languages) or any(not Path(asset["path"]).is_file() for asset in captions.values()):
            raise HTTPException(409, f"Gere as faixas de legenda selecionadas de {item['filename']} antes do envio")
    unresolved = [item["filename"] for item in selected if item.get("upload_status") == "uploading-unknown"]
    unresolved.extend(
        track.get("filename", track.get("language", "legenda"))
        for item in selected
        for track in item.get("caption_uploads", [])
        if track.get("status") == "uploading-unknown"
    )
    if unresolved:
        raise HTTPException(409, "Confira no YouTube Studio antes de repetir: " + ", ".join(unresolved))
    project["review"] = {"approved": True, "approved_at": state.now()}
    project["status"], project["error"] = "uploading", None
    project["job"] = {"stage": "uploading", "progress": 0.0, "message": "Enviando ativos selecionados…"}
    state.save(project)
    threading.Thread(target=_upload_job, args=(project_id,), daemon=True).start()
    return project


def _analysis_job(project_id: str, model_name: str, visual_review: bool = True, source_language: str = "pt", provider: str | None = None, visual_frame_limit: int = 8) -> None:
    try:
        project = _load(project_id)
        provider = provider or project.get("ai_provider") or state.get_ai_provider()
        model = ai_providers.PROVIDERS[provider]["model"]

        project["job"] = {"stage": "visual-analysis", "progress": 0.02, "message": "Analisando enquadramento e cor localmente…"}
        state.save(project)
        try:
            project["visual_analysis"] = visual.analyze_video(Path(project["source"]), project["metadata"]["duration"], project["metadata"]["width"], project["metadata"]["height"])
        except Exception as visual_error:
            project["visual_analysis"] = {"status": "unavailable", "error": str(visual_error), "crop_track": [], "grade_suggestion": {"brightness": 0, "contrast": 1, "saturation": 1}}
        if visual_review:
            project["job"] = {"stage": "visual-review", "progress": 0.08, "message": f"Classificando frames com {ai_providers.PROVIDERS[provider]['label']}…"}
            state.save(project)
            try:
                scene = mimo_vision.review_scenes(Path(project["source"]), float(project["metadata"]["duration"]), provider, visual_frame_limit)
                project["analysis_run"]["visual_frames_used"] = scene.get("sample_count", 0)
                project["analysis_run"]["visual_grid_images_used"] = scene.get("grid_image_count", 0)
                project["visual_analysis"]["scene_review"] = scene
                project["visual_analysis"]["grade_segments"] = visual.grade_segments(
                    Path(project["source"]), float(project["metadata"]["duration"]), scene.get("scene_segments", []),
                    int(project["metadata"]["width"]), int(project["metadata"]["height"]))
                project["analysis_run"]["capabilities"]["visual"] = {"status": scene.get("status", "partial"), "frames": scene.get("sample_count", 0), "classified_frames": scene.get("classified_count", 0), "requested_frames": scene.get("requested_sample_count", 0), "last_attempt_frames": scene.get("sample_count", 0), "grid_images": scene.get("grid_image_count", 0), "last_attempt_grid_images": scene.get("grid_image_count", 0)}
            except Exception as scene_error:
                project["analysis_run"]["visual_frames_used"] = int(getattr(scene_error, "visual_frames_attempted", 0))
                project["analysis_run"]["visual_grid_images_used"] = int(getattr(scene_error, "visual_grid_images_attempted", 0))
                project["visual_analysis"]["scene_review"] = {"provider": provider, "model": model, "status": "unavailable", "error": type(scene_error).__name__}
                project["analysis_run"]["capabilities"]["visual"] = {"status": "failed", "error": type(scene_error).__name__,
                    "frames": project["analysis_run"]["visual_frames_used"],
                    "last_attempt_frames": project["analysis_run"]["visual_frames_used"],
                    "grid_images": project["analysis_run"]["visual_grid_images_used"],
                    "last_attempt_grid_images": project["analysis_run"]["visual_grid_images_used"]}
                project["visual_analysis"]["grade_segments"] = [{"id": "scene-unknown", "start": 0,
                    "end": float(project["metadata"]["duration"]), "layout": "unknown", "confidence": "low",
                    "status": "preserve", "enabled": False, "intensity": 1.0,
                    "suggestion": {"brightness": 0, "contrast": 1, "saturation": 1},
                    "reason": "Classificação indisponível; cores preservadas."}]
        else:
            project["visual_analysis"]["grade_segments"] = [{"id": "scene-unknown", "start": 0,
                "end": float(project["metadata"]["duration"]), "layout": "unknown", "confidence": "low",
                "status": "preserve", "enabled": False, "intensity": 1.0,
                "suggestion": {"brightness": 0, "contrast": 1, "saturation": 1},
                "reason": "Revisão visual desativada; cores preservadas."}]
            project["analysis_run"]["capabilities"]["visual"] = {"status": "skipped"}
        project["visual_analysis"]["grade_policy"] = {"mode": "preserve", "reason": "Ajustes globais desativados; revisão por cena."}
        project["visual_analysis"]["grade_suggestion"] = {"brightness": 0, "contrast": 1, "saturation": 1}
        project["color_grade"] = {"enabled": False, "intensity": 1.0, "segments": {}}
        state.save(project)

        def progress(value: float, message: str):
            current = _load(project_id)
            stage = "semantic-analysis" if message.startswith("Análise semântica") else "transcribing"
            current["job"] = {"stage": stage, "progress": value, "message": message}
            state.save(current)

        transcript = media.transcribe(Path(project["source"]), progress, model_name, source_language)
        project = _load(project_id)
        project["transcript"] = transcript
        project["captions"] = {source_language: transcript}
        project["analysis_run"]["capabilities"]["audio"] = {"status": "running"}
        project["job"] = {"stage": "semantic-analysis", "progress": 0.78, "message": f"Analisando a transcrição com {ai_providers.PROVIDERS[provider]['label']}…"}
        state.save(project)
        try:
            silence = media.detect_silence(Path(project["source"]), float(project["metadata"]["duration"]))
            project["audio_analysis"] = {"status": "complete", "provider": "ffmpeg", "silence_intervals": silence,
                                          "noise_db": -35.0, "min_duration": 1.2}
            project["analysis_run"]["capabilities"]["audio"] = {"status": "complete", "intervals": len(silence)}
        except Exception as audio_error:
            project["audio_analysis"] = {"status": "unavailable", "provider": "ffmpeg", "error": type(audio_error).__name__}
            project["analysis_run"]["capabilities"]["audio"] = {"status": "failed", "error": type(audio_error).__name__}
            silence = []
        state.save(project)
        if transcript:
            semantic_edits, semantic_cuts, providers = ai_analysis.analyze_transcript(transcript, project["metadata"]["duration"], progress, source_language, provider)
        else:
            semantic_edits, semantic_cuts = [], []
            providers = {provider: {"status": "unavailable", "provider": provider, "model": model,
                                    "error": "empty-transcript"}}
        project = _load(project_id)
        project["captions"] = {source_language: transcript}
        project["translated_languages"] = []
        rule_edits = media.suggest_edits(transcript, project["metadata"]["duration"])
        rule_edits.extend(media.suggest_audio_silence_edits(transcript, project["metadata"]["duration"], silence))
        project["edits"] = ai_analysis.merge_edits(rule_edits, semantic_edits)
        rule_shorts = media.suggest_shorts(transcript, project["metadata"]["duration"], project["edits"])
        project["shorts"] = ai_analysis.merge_shorts(rule_shorts, [item for item in semantic_cuts if item.get("format") != "horizontal"], project["edits"])
        project["youtube_cuts"] = ai_analysis.merge_youtube_cuts([item for item in semantic_cuts if item.get("format") == "horizontal"], project["edits"])
        project["ai_analysis"] = {"models": providers}
        semantic_status = providers.get(provider, {}).get("status", "unavailable")
        project["analysis_run"]["capabilities"]["semantic"] = {"status": semantic_status}
        project["analysis_run"]["provider_result"] = providers.get(provider, {})
        project["analysis_run"]["status"] = "partial" if any(
            item.get("status") in {"failed", "unavailable", "partial", "stale"}
            for item in project["analysis_run"]["capabilities"].values()) else "complete"
        project["ai_analysis"].update({"provider": provider, "model": model,
            "effort": ai_providers.PROVIDERS[provider]["effort"], "status": project["analysis_run"]["status"]})
        project["status"] = "review-ready"
        successes = sum(model.get("status") == "complete" for model in providers.values())
        requested = 1
        message = "Análise pronta para revisão" if successes == requested else f"Análise pronta · IA disponível em {successes}/{requested} modelos; heurísticas locais mantidas"
        project["job"] = {"stage": "complete", "progress": 1.0, "message": message}
        project["error"] = None
        state.save(project)
    except Exception as exc:
        project = _load(project_id)
        project["status"], project["error"] = "failed", str(exc)
        project["job"] = {"stage": "failed", "progress": 0.0, "message": "Análise interrompida"}
        state.save(project)


def _translation_job(project_id: str, languages: list[str]) -> None:
    try:
        project = _load(project_id)
        source = project.get("source_language", "pt")
        transcript = project.get("transcript", [])
        for index, language in enumerate(languages, 1):
            project["job"] = {"stage": "translating", "progress": (index - 1) / len(languages), "message": f"Traduzindo para {media.LANGUAGES[language]['label']} localmente…"}
            state.save(project)
            translated = media.translate_segments(transcript, source, language)
            project = _load(project_id)
            project.setdefault("captions", {})[language] = translated
            project["translated_languages"] = list(dict.fromkeys([*project.get("translated_languages", []), language]))
            state.save(project)
        project["translated_languages"] = list(dict.fromkeys([*project.get("translated_languages", []), *languages]))
        project["status"], project["error"] = "review-ready", None
        project["job"] = {"stage": "complete", "progress": 1.0, "message": "Traduções prontas para revisão"}
        state.save(project)
    except Exception as exc:
        project = _load(project_id)
        project["status"], project["error"] = "failed", str(exc)
        project["job"] = {"stage": "failed", "progress": 0.0, "message": "Tradução interrompida"}
        state.save(project)


def _export_job(project_id: str) -> None:
    project = _load(project_id)
    directory = state.EXPORTS_DIR / project_id
    directory.mkdir(parents=True, exist_ok=True)
    try:
        base = state.slug(project["name"])
        master = directory / f"{base}-youtube.mp4"
        media.render_video(project, master)
        assets = [{"id": "master", "type": "master", "title": project["name"], "filename": master.name, "path": str(master), "youtube_selected": True, "upload_status": "not-uploaded", "quality_check": _render_quality_check(project, master, expected_size=(project["metadata"]["width"], project["metadata"]["height"]))}]
        for language in _caption_languages(project):
            caption = directory / f"{base}.{language}.srt"
            media.write_captions(project, caption, language)
            assets.append({"id": f"caption-{language}", "type": "caption", "title": f"{language.upper()} subtitles", "filename": caption.name, "path": str(caption), "youtube_selected": False, "upload_status": "not-uploaded"})
            web_caption = directory / f"{base}.{language}.vtt"
            media.write_captions(project, web_caption, language)
            assets.append({"id": f"caption-{language}-vtt", "type": "caption", "title": f"{language.upper()} subtitles (WebVTT)", "filename": web_caption.name, "path": str(web_caption), "youtube_selected": False, "upload_status": "not-uploaded"})
        for index, short in enumerate(project.get("shorts", []), 1):
            if short.get("decision") != "accepted":
                continue
            interval = (float(short["start"]), float(short["end"]))
            video = directory / f"{base}-short-{index}.mp4"
            source_language = project.get("source_language", "pt")
            source_caption = directory / f"{base}-short-{index}.{source_language}.srt"
            media.write_captions(project, source_caption, source_language, cut=interval)
            track = (project.get("visual_analysis") or {}).get("crop_track", [])
            media.render_video(project, video, cut=interval, vertical=True, caption_file=source_caption, crop_x=float(short.get("crop_x", 0.5)), crop_track=track, crop_mode=short.get("crop_mode", "steady"))
            assets.append({"id": short["id"], "type": "short", "title": short.get("title") or f"{project['name']} short {index}", "filename": video.name, "path": str(video), "youtube_selected": True, "upload_status": "not-uploaded", "quality_check": _render_quality_check(project, video, interval, (1080, 1920))})
            for language in _caption_languages(project):
                caption = directory / f"{base}-short-{index}.{language}.srt"
                media.write_captions(project, caption, language, cut=interval)
                assets.append({"id": f"{short['id']}-caption-{language}", "type": "caption", "title": f"Short {index} {language.upper()} subtitles", "filename": caption.name, "path": str(caption), "youtube_selected": False, "upload_status": "not-uploaded"})
                web_caption = directory / f"{base}-short-{index}.{language}.vtt"
                media.write_captions(project, web_caption, language, cut=interval)
                assets.append({"id": f"{short['id']}-caption-{language}-vtt", "type": "caption", "title": f"Short {index} {language.upper()} subtitles (WebVTT)", "filename": web_caption.name, "path": str(web_caption), "youtube_selected": False, "upload_status": "not-uploaded"})
        for index, cut_item in enumerate(project.get("youtube_cuts", []), 1):
            if cut_item.get("decision") != "accepted":
                continue
            interval = (float(cut_item["start"]), float(cut_item["end"]))
            video = directory / f"{base}-youtube-cut-{index}.mp4"
            media.render_video(project, video, cut=interval, horizontal=True)
            assets.append({"id": cut_item["id"], "type": "youtube-cut", "title": cut_item.get("title") or f"Corte horizontal {index}", "filename": video.name, "path": str(video), "youtube_selected": True, "upload_status": "not-uploaded", "quality_check": _render_quality_check(project, video, interval, (1920, 1080))})
            for language in _caption_languages(project):
                caption = directory / f"{base}-youtube-cut-{index}.{language}.srt"
                media.write_captions(project, caption, language, cut=interval)
                assets.append({"id": f"{cut_item['id']}-caption-{language}", "type": "caption", "title": f"Corte horizontal {index} {language.upper()} subtitles", "filename": caption.name, "path": str(caption), "youtube_selected": False, "upload_status": "not-uploaded"})
                web_caption = directory / f"{base}-youtube-cut-{index}.{language}.vtt"
                media.write_captions(project, web_caption, language, cut=interval)
                assets.append({"id": f"{cut_item['id']}-caption-{language}-vtt", "type": "caption", "title": f"Corte horizontal {index} {language.upper()} subtitles (WebVTT)", "filename": web_caption.name, "path": str(web_caption), "youtube_selected": False, "upload_status": "not-uploaded"})
        project = _load(project_id)
        project["exports"], project["status"], project["error"] = assets, "export-ready", None
        project["job"] = {"stage": "complete", "progress": 1.0, "message": "Exportação pronta"}
        metadata = project.setdefault("youtube", {})
        metadata.setdefault("title", project["name"][:100])
        metadata.setdefault("description", "")
        metadata.setdefault("tags", [])
        metadata.setdefault("chapters", _chapters(project.get("transcript", [])))
        state.save(project)
    except Exception as exc:
        project = _load(project_id)
        project["status"], project["error"] = "failed", str(exc)
        project["job"] = {"stage": "failed", "progress": 0.0, "message": "Exportação interrompida"}
        state.save(project)


def _upload_job(project_id: str) -> None:
    try:
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request as GoogleRequest

        token = _token()
        credentials = Credentials.from_authorized_user_file(str(token), _SCOPES)
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(GoogleRequest())
            token.write_text(credentials.to_json(), encoding="utf-8")
            token.chmod(0o600)
        service = build("youtube", "v3", credentials=credentials, cache_discovery=False)
        project = _load(project_id)
        for asset in project.get("exports", []):
            if not asset.get("youtube_selected") or asset["type"] not in {"master", "short", "youtube-cut"}:
                continue
            if asset.get("upload_status") == "uploading-unknown":
                continue
            project = _load(project_id)
            current = next(item for item in project["exports"] if item["id"] == asset["id"])
            if current.get("upload_status") != "uploaded":
                current["upload_status"], current["upload_error"] = "uploading", None
                state.save(project)
                metadata = project.get("youtube", {})
                title = (current.get("title") or metadata.get("title") or project["name"])[:100]
                description = metadata.get("description", "").strip()
                chapters = metadata.get("chapters", "").strip()
                if chapters:
                    description = f"{description}\n\n{chapters}".strip()
                body = {"snippet": {"title": title, "description": description[:5000], "tags": metadata.get("tags", [])[:500], "categoryId": "27", "defaultLanguage": media.LANGUAGES[project.get("source_language", "pt")]["locale"]}, "status": {"privacyStatus": "private"}}
                request = service.videos().insert(part="snippet,status", body=body, media_body=MediaFileUpload(current["path"], chunksize=8 * 1024 * 1024, resumable=True))
                response = None
                while response is None:
                    _, response = request.next_chunk()
                current.update({"upload_status": "uploaded", "youtube_id": response["id"], "youtube_url": f"https://www.youtube.com/watch?v={response['id']}", "privacy_status": "private"})
                state.save(project)

            # Each selected video receives the source and translated SRT tracks.
            for language in _caption_languages(project):
                language_name = media.LANGUAGES.get(language, {}).get("label", language)
                caption_id = f"caption-{language}" if current["id"] == "master" else f"{current['id']}-caption-{language}"
                caption = next((item for item in project["exports"] if item["id"] == caption_id), None)
                if caption is None or not Path(caption["path"]).is_file():
                    raise RuntimeError(f"Arquivo SRT {language.upper()} ausente para {current['filename']}")
                uploads = current.setdefault("caption_uploads", [])
                track = next((item for item in uploads if item.get("language") == language), None)
                if track and track.get("status") == "uploaded":
                    continue
                if track and track.get("status") == "uploading-unknown":
                    continue
                if track is None:
                    track = {"language": language, "language_name": language_name, "filename": caption["filename"], "status": "not-uploaded"}
                    uploads.append(track)
                track.update({"status": "uploading", "error": None})
                state.save(project)
                snippet = {"videoId": current["youtube_id"], "language": media.LANGUAGES[language]["locale"], "name": language_name, "isDraft": False}
                request = service.captions().insert(part="id,snippet", body={"snippet": snippet}, media_body=MediaFileUpload(caption["path"], mimetype="application/octet-stream", resumable=True))
                response = None
                while response is None:
                    _, response = request.next_chunk()
                youtube_caption_status = response.get("snippet", {}).get("status")
                upload_status = "failed" if youtube_caption_status == "failed" else "uploaded"
                track.update({"status": upload_status, "youtube_caption_id": response["id"], "youtube_status": youtube_caption_status, "error": response.get("snippet", {}).get("failureReason")})
                caption.update({"upload_status": upload_status, "youtube_video_id": current["youtube_id"], "upload_error": track["error"]})
                state.save(project)
        project = _load(project_id)
        project["status"], project["error"] = "uploaded", None
        state.save(project)
    except Exception as exc:
        project = _load(project_id)
        for asset in project.get("exports", []):
            if asset.get("upload_status") == "uploading":
                asset["upload_status"], asset["upload_error"] = "uploading-unknown", str(exc)
            for track in asset.get("caption_uploads", []):
                if track.get("status") == "uploading":
                    track.update({"status": "uploading-unknown", "error": str(exc)})
                caption_asset = next((item for item in project.get("exports", []) if item.get("filename") == track.get("filename")), None)
                if caption_asset:
                    caption_asset.update({"upload_status": track.get("status"), "upload_error": track.get("error")})
        project["status"], project["error"] = "upload-failed", str(exc)
        state.save(project)


def _update_decisions(project: dict[str, Any], body: dict[str, Any]) -> None:
    for group in ("edits", "shorts", "youtube_cuts"):
        known = {item["id"]: item for item in project.get(group, [])}
        for change in body.get(group, []):
            target = known.get(change.get("id"))
            if not target:
                continue
            decision = change.get("decision")
            if decision not in {"pending", "accepted", "rejected"}:
                raise HTTPException(422, "Decisão inválida")
            target["decision"] = decision
            start, end = float(change.get("start", target["start"])), float(change.get("end", target["end"]))
            duration = float(project["metadata"]["duration"])
            # UI values are displayed to milliseconds; tolerate rounding of
            # ffprobe's higher precision, then clamp back to media duration.
            if not (math.isfinite(start) and math.isfinite(end) and 0 <= start < end <= duration + 0.001):
                raise HTTPException(422, "Intervalo inválido")
            start, end = min(start, duration), min(end, duration)
            if start >= end:
                raise HTTPException(422, "Intervalo inválido")
            if group == "youtube_cuts" and decision == "accepted":
                conflicts = [edit for edit in project.get("edits", [])
                             if edit.get("decision") != "rejected" and start < float(edit["end"]) and end > float(edit["start"])]
                if conflicts:
                    raise HTTPException(422, "Resolva ou rejeite as remoções conflitantes antes de aprovar o corte horizontal")
            target["start"], target["end"] = round(start, 3), round(end, 3)
            if group in {"shorts", "youtube_cuts"} and "title" in change:
                target["title"] = str(change["title"])[:100]
            if group == "shorts" and "crop_x" in change:
                target["crop_x"] = min(1.0, max(0.0, float(change["crop_x"])))
            if group == "shorts" and "crop_mode" in change:
                if change["crop_mode"] not in {"steady", "track"}:
                    raise HTTPException(422, "Modo de enquadramento inválido")
                target["crop_mode"] = change["crop_mode"]
    visual_change = body.get("visual")
    if visual_change is not None:
        if not isinstance(visual_change, dict):
            raise HTTPException(422, "Configuração visual inválida")
        segments = visual_change.get("grade_segments")
        if segments is not None:
            if not isinstance(segments, list):
                raise HTTPException(422, "Ajustes por cena inválidos")
            known = {item.get("id"): item for item in (project.get("visual_analysis") or {}).get("grade_segments", [])}
            choices = {}
            for choice in segments:
                if not isinstance(choice, dict) or choice.get("id") not in known:
                    raise HTTPException(422, "Cena de cor desconhecida")
                segment = known[choice["id"]]
                enabled, intensity = choice.get("enabled"), choice.get("intensity", 1)
                if enabled and visual.legacy_incomplete_review(project.get("visual_analysis") or {}):
                    raise HTTPException(422, "A classificação visual antiga está incompleta; reanalise para revisar cores")
                if segment.get("layout") != "camera" or segment.get("status") != "reviewable":
                    if enabled:
                        raise HTTPException(422, "Só cenas de câmera verificadas podem receber correção")
                if not isinstance(enabled, bool) or not isinstance(intensity, (int,float)) or not math.isfinite(float(intensity)) or not 0 <= float(intensity) <= 1:
                    raise HTTPException(422, "Ajuste de cor inválido")
                choices[choice["id"]] = {"enabled": enabled, "intensity": float(intensity)}
            for scene_id, scene in known.items():
                choices.setdefault(scene_id, {"enabled": False, "intensity": 1.0})
            project["color_grade"] = {"enabled": any(item["enabled"] for item in choices.values()),
                                      "intensity": 1.0, "segments": choices}
            return
        intensity, enabled = visual_change.get("intensity", 1), visual_change.get("grade_enabled", False)
        if not isinstance(intensity, (int, float)) or not math.isfinite(float(intensity)) or not 0 <= float(intensity) <= 1 or not isinstance(enabled, bool):
            raise HTTPException(422, "Ajuste de cor inválido")
        if enabled and (project.get("visual_analysis") or {}).get("grade_policy", {}).get("mode") == "preserve":
            raise HTTPException(422, "Correção global bloqueada para preservar cores de slides ou conteúdo de tela")
        project["color_grade"] = {"enabled": enabled, "intensity": float(intensity)}


def _render_quality_check(project: dict[str, Any], path: Path, cut: tuple[float, float] | None = None, expected_size: tuple[int, int] | None = None) -> dict[str, Any]:
    duration = float(project["metadata"]["duration"])
    removed = [(float(item["start"]), float(item["end"])) for item in project.get("edits", []) if item.get("decision") == "accepted"]
    keep = media._output_intervals(duration, removed, cut)
    expected_duration = sum(end - start for start, end in keep)
    boundaries = []
    output_time = 0.0
    for start, end in keep[:-1]:
        output_time += end - start
        boundaries.append(output_time)
    return visual.inspect_render(path, boundaries, expected_size, expected_duration)


def _chapters(segments: list[dict[str, Any]]) -> str:
    chapters, last = [], -300
    for segment in segments:
        seconds = int(segment["start"])
        if seconds - last >= 300:
            text = " ".join(segment["text"].split()[:7]).strip(".,!? ") or "Capítulo"
            chapters.append(f"{seconds // 60:02}:{seconds % 60:02} {text}")
            last = seconds
    if not chapters or not chapters[0].startswith("00:"):
        chapters.insert(0, "00:00 Início")
    return "\n".join(chapters)


def _load(project_id: str) -> dict[str, Any]:
    try:
        project = state.load(project_id)
        project["visual_legacy_incomplete"] = visual.legacy_incomplete_review(project.get("visual_analysis") or {})
        project["transcript_anomalies"] = transcript_quality.anomalies(project.get("transcript", []))
        anomalies = project["transcript_anomalies"]
        suspect = {item["segment_index"] for item in anomalies}
        for edit in project.get("edits", []):
            edit.pop("asr_uncertain_reason", None)
            if any(float(edit["start"]) < item["end"] and float(edit["end"]) > item["start"] for item in anomalies):
                edit["asr_uncertain_reason"] = "interval"
            elif suspect and edit.get("quote") and transcript_quality.quote_touches_anomaly(edit["quote"], project.get("transcript", []), suspect):
                edit["asr_uncertain_reason"] = "quote"
        project.setdefault("source_language", "pt")
        if "translated_languages" not in project:
            project["translated_languages"] = [language for language, segments in project.get("captions", {}).items() if language != project["source_language"] and segments]
        return project
    except (ValueError, FileNotFoundError):
        raise HTTPException(404, "Projeto não encontrado")


def _caption_languages(project: dict[str, Any]) -> list[str]:
    source = project.get("source_language", "pt")
    return [language for language in dict.fromkeys([source, *project.get("translated_languages", [])]) if language in media.LANGUAGES and project.get("captions", {}).get(language)]


def _has(command: str) -> bool:
    from shutil import which
    return which(command) is not None


def _oauth_secrets() -> Path:
    configured = state.DATA_DIR / "youtube-client-secret.json"
    if configured.is_file():
        return configured
    return Path(os.getenv("YOUTUBE_CLIENT_SECRETS", "secrets/client_secret.json")).expanduser().resolve()


def _token() -> Path:
    return state.DATA_DIR / "youtube-token.json"
