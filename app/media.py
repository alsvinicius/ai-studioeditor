from __future__ import annotations

import json
import math
import os
import re
import subprocess
from collections import deque
from pathlib import Path
from typing import Any

from . import state, visual as visual_module


TRANSCRIPTION_MODELS = {
    "tiny": "Rápida · menor qualidade",
    "base": "Leve · rápida",
    "small": "Equilibrada · mais rápida",
    "medium": "Alta · recomendada",
    "large-v3": "Máxima · mais lenta, exige mais memória e download",
}

LANGUAGES = {
    "pt": {"label": "Português (Brasil)", "whisper": "pt", "locale": "pt-BR"},
    "en": {"label": "English", "whisper": "en", "locale": "en"},
    "es": {"label": "Español", "whisper": "es", "locale": "es"},
    "fr": {"label": "Français", "whisper": "fr", "locale": "fr"},
    "de": {"label": "Deutsch", "whisper": "de", "locale": "de"},
    "hi": {"label": "हिन्दी", "whisper": "hi", "locale": "hi"},
    "ar": {"label": "العربية", "whisper": "ar", "locale": "ar"},
    "id": {"label": "Bahasa Indonesia", "whisper": "id", "locale": "id"},
    "ja": {"label": "日本語", "whisper": "ja", "locale": "ja"},
    "ru": {"label": "Русский", "whisper": "ru", "locale": "ru"},
    "tr": {"label": "Türkçe", "whisper": "tr", "locale": "tr"},
}

CAPTION_TARGET_LANGUAGES = ("en", "es", "fr", "de", "hi", "ar", "id", "ja", "ru", "tr")


def default_transcription_model() -> str:
    configured = os.getenv("WHISPER_MODEL", "medium")
    return configured if configured in TRANSCRIPTION_MODELS else "medium"


def ffprobe(path: Path) -> dict[str, Any]:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise ValueError(result.stderr.strip() or "Arquivo inválido ou formato não suportado")
    data = json.loads(result.stdout)
    streams = data.get("streams", [])
    video = next((stream for stream in streams if stream.get("codec_type") == "video"), None)
    audio = next((stream for stream in streams if stream.get("codec_type") == "audio"), None)
    if not video:
        raise ValueError("O arquivo não contém uma faixa de vídeo")
    if not audio:
        raise ValueError("O arquivo não contém áudio; não é possível transcrever")
    duration = float(data.get("format", {}).get("duration") or video.get("duration") or 0)
    if duration <= 0:
        raise ValueError("Não foi possível determinar a duração do vídeo")
    return {
        "duration": duration,
        "width": int(video.get("width", 0)),
        "height": int(video.get("height", 0)),
        "video_codec": video.get("codec_name"),
        "audio_codec": audio.get("codec_name"),
        "format": data.get("format", {}).get("format_name"),
        "fps": _fps(video.get("avg_frame_rate")),
        "size_bytes": int(data.get("format", {}).get("size") or path.stat().st_size),
    }


def _fps(value: str | None) -> float | None:
    try:
        numerator, denominator = (value or "").split("/", 1)
        denominator_value = float(denominator)
        return float(numerator) / denominator_value if denominator_value else None
    except (ValueError, ZeroDivisionError):
        return None


def transcribe(path: Path, progress=None, model_name: str | None = None, language: str = "pt") -> list[dict[str, Any]]:
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError("Transcrição local indisponível. Instale as dependências do projeto.") from exc
    model_name = model_name or default_transcription_model()
    if model_name not in TRANSCRIPTION_MODELS:
        raise ValueError("Modelo de transcrição inválido")
    if progress:
        progress(0.03, f"Carregando Whisper {model_name}… O primeiro uso pode baixar o modelo.")
    model = WhisperModel(model_name, device="cpu", compute_type="int8", download_root=os.getenv("MODEL_CACHE_DIR", "models"))
    # Favor accuracy over throughput: medium + beam search reduces common
    # Portuguese transcription errors while keeping the default CPU path local.
    if language not in LANGUAGES:
        raise ValueError("Idioma de transcrição inválido")
    segments, info = model.transcribe(
        str(path), language=LANGUAGES[language]["whisper"], vad_filter=True, beam_size=5,
        condition_on_previous_text=True, word_timestamps=True,
    )
    output = []
    last_report = -15.0
    max_position = -1.0
    stagnant = 0
    recent_positions: deque[float] = deque(maxlen=100)
    try:
        total_duration = float(getattr(info, "duration", 0) or 0)
    except (TypeError, ValueError):
        total_duration = 0.0
    for index, segment in enumerate(segments):
        position = float(segment.end)
        if not math.isfinite(position) or position < 0:
            raise RuntimeError("A transcrição retornou tempos inválidos; tente outra análise.")
        stagnant = stagnant + 1 if position <= max_position + 0.001 else 0
        if stagnant >= 30:
            raise RuntimeError("A transcrição parou de avançar no áudio; tente outro modelo ou refaça a análise.")
        max_position = max(max_position, position)
        recent_positions.append(max_position)
        if len(recent_positions) == recent_positions.maxlen and recent_positions[-1] - recent_positions[0] < 1:
            raise RuntimeError("A transcrição está gerando segmentos excessivos no mesmo trecho; tente outro modelo ou refaça a análise.")
        output.append({
            "id": f"s{index}",
            "start": round(float(segment.start), 3),
            "end": round(float(segment.end), 3),
            "text": segment.text.strip(),
            "words": [
                {"start": round(float(word.start), 3), "end": round(float(word.end), 3),
                 "text": str(word.word).strip(), "probability": round(float(word.probability), 4)}
                for word in (getattr(segment, "words", None) or [])
            ],
            "avg_logprob": round(float(getattr(segment, "avg_logprob", 0.0)), 4),
            "no_speech_prob": round(float(getattr(segment, "no_speech_prob", 0.0)), 4),
            "compression_ratio": round(float(getattr(segment, "compression_ratio", 0.0)), 4),
        })
        if progress and (index == 0 or position - last_report >= 15):
            ratio = min(1.0, position / total_duration) if math.isfinite(total_duration) and total_duration > 0 else 0.0
            elapsed = f"{int(position) // 60:02}:{int(position) % 60:02}"
            total = f"{int(total_duration) // 60:02}:{int(total_duration) % 60:02}" if total_duration > 0 and math.isfinite(total_duration) else "?"
            progress(0.12 + ratio * 0.53, f"Transcrevendo ({info.language}) · {elapsed} de {total}")
            last_report = position
    return output


def translate_segments(segments: list[dict[str, Any]], source: str, target: str) -> list[dict[str, Any]]:
    try:
        import argostranslate.package
        import argostranslate.translate
    except ImportError as exc:
        raise RuntimeError("Tradução local indisponível. Instale as dependências do projeto.") from exc
    installed = argostranslate.translate.get_installed_languages()
    if source not in LANGUAGES or target not in LANGUAGES or source == target:
        raise ValueError("Idiomas de tradução inválidos")
    def get_translation(from_code: str, to_code: str):
        nonlocal installed
        source_lang = next((lang for lang in installed if lang.code == from_code), None)
        target_lang = next((lang for lang in installed if lang.code == to_code), None)
        translation = source_lang.get_translation(target_lang) if source_lang and target_lang else None
        if translation is None:
            argostranslate.package.update_package_index()
            packages = argostranslate.package.get_available_packages()
            package = next((item for item in packages if item.from_code == from_code and item.to_code == to_code), None)
            if not package:
                return None
            downloaded = package.download()
            argostranslate.package.install_from_path(downloaded)
            installed = argostranslate.translate.get_installed_languages()
            source_lang = next((lang for lang in installed if lang.code == from_code), None)
            target_lang = next((lang for lang in installed if lang.code == to_code), None)
            translation = source_lang.get_translation(target_lang) if source_lang and target_lang else None
        return translation

    translation = get_translation(source, target)
    # Argos has broader coverage through English than for every direct pair.
    # Keep translation local and use a two-step route only when it is needed.
    if translation is None and source != "en" and target != "en":
        to_english = get_translation(source, "en")
        from_english = get_translation("en", target)
        if to_english and from_english:
            translation = _TranslationViaPivot(to_english, from_english)
    if translation is None:
        raise RuntimeError(f"Não encontrei modelos locais de tradução de {LANGUAGES[source]['label']} para {LANGUAGES[target]['label']} (nem uma rota pelo inglês).")
    return [
        {"id": item["id"], "start": item["start"], "end": item["end"], "text": translation.translate(item["text"])}
        for item in segments
    ]


class _TranslationViaPivot:
    def __init__(self, first, second):
        self.first = first
        self.second = second

    def translate(self, text: str) -> str:
        return self.second.translate(self.first.translate(text))


def translate_pt_en(segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return translate_segments(segments, "pt", "en")


def suggest_edits(segments: list[dict[str, Any]], duration: float) -> list[dict[str, Any]]:
    # Missing transcript is not evidence of silence; only measured audio below
    # may generate a silence candidate. Similar words alone do not prove retake.
    return []


def detect_silence(path: Path, duration: float, noise_db: float = -35.0,
                   min_duration: float = 1.2) -> list[dict[str, float]]:
    """Measure quiet intervals locally; results remain editorial suggestions."""
    command = ["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-vn",
               "-af", f"silencedetect=noise={noise_db:g}dB:d={min_duration:g}", "-f", "null", "-"]
    result = subprocess.run(command, capture_output=True, text=True, timeout=180, check=False)
    if result.returncode:
        raise RuntimeError("Não foi possível medir silêncio no áudio")
    log = result.stderr or ""
    starts = [float(value) for value in re.findall(r"silence_start:\s*([0-9.]+)", log)]
    ends = [float(value) for value in re.findall(r"silence_end:\s*([0-9.]+)", log)]
    intervals = []
    for index, start in enumerate(starts):
        end = ends[index] if index < len(ends) else duration
        start, end = max(0.0, min(duration, start)), max(0.0, min(duration, end))
        if end - start >= min_duration:
            intervals.append({"start": round(start, 3), "end": round(end, 3),
                              "duration": round(end - start, 3), "noise_db": noise_db})
    return intervals


def suggest_audio_silence_edits(segments: list[dict[str, Any]], duration: float,
                                intervals: list[dict[str, float]]) -> list[dict[str, Any]]:
    """Suggest clear audio gaps without treating low-confidence ASR as audio."""
    if not segments:
        return []
    result = []
    last_end = max(float(segment["end"]) for segment in segments)
    tail = next((item for item in reversed(intervals)
                 if float(item["end"]) >= duration - 0.25
                 and float(item["start"]) >= last_end - 0.75), None)
    if tail and duration - last_end >= 1.25:
        start = min(duration, max(last_end + 0.1, float(tail["start"]) + 0.1))
        if start < duration:
            result.append(_edit("ending-silence", start, duration,
                                "Silêncio detectado após a última fala", "high"))
    for item in intervals:
        start, end = float(item["start"]), float(item["end"])
        if end >= duration - 0.25 or end - start < 1.5:
            continue
        if any(float(segment["start"]) < end and float(segment["end"]) > start for segment in segments):
            continue
        safe_start, safe_end = start + 0.1, end - 0.1
        if safe_end - safe_start >= 1.25:
            opening = start <= 0.1
            result.append(_edit("opening-silence" if opening else "long-pause", safe_start, safe_end,
                                "Silêncio detectado no início" if opening else "Silêncio detectado no áudio", "medium"))
    return result


def _edit(kind: str, start: float, end: float, label: str, confidence: str) -> dict[str, Any]:
    return {"id": f"edit-{kind}-{round(start * 1000)}", "kind": kind, "start": round(max(0, start), 3), "end": round(max(start, end), 3), "label": label, "confidence": confidence, "decision": "pending"}


def suggest_shorts(segments: list[dict[str, Any]], duration: float, edits: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    if duration < 30 or not segments:
        return []
    window = min(45.0, duration)
    step = max(15.0, window / 3)
    candidates = []
    excluded = [(item["start"], item["end"]) for item in edits or []]
    safe_intervals = _kept_intervals(duration, excluded)
    for safe_start, safe_end in safe_intervals:
        start = safe_start
        while start + 30 <= safe_end:
            end = min(safe_end, start + window)
            words = sum(len(segment["text"].split()) for segment in segments if segment["start"] < end and segment["end"] > start)
            if words >= 15:
                candidates.append({"start": min(round(start, 3), duration), "end": min(round(end, 3), duration), "score": words / max(end - start, 1)})
            start += step
    candidates.sort(key=lambda item: item["score"], reverse=True)
    selected = []
    for index, item in enumerate(candidates):
        if all(abs(item["start"] - prior["start"]) >= window * 0.7 for prior in selected):
            selected.append({"id": f"short-{index+1}", **item, "decision": "pending", "crop_x": 0.5, "title": f"Corte {len(selected)+1}"})
        if len(selected) >= 5:
            break
    return sorted(selected, key=lambda item: item["start"])


def render_video(project: dict[str, Any], destination: Path, cut: tuple[float, float] | None = None, vertical: bool = False, caption_file: Path | None = None, crop_x: float = 0.5, horizontal: bool = False, crop_track: list[dict[str, Any]] | None = None, crop_mode: str = "steady") -> None:
    source = Path(project["source"])
    duration = project["metadata"]["duration"]
    removed = [(item["start"], item["end"]) for item in project.get("edits", []) if item.get("decision") == "accepted"]
    keep = _output_intervals(duration, removed, cut)
    keep = [(start, end) for start, end in keep if end > start]
    if not keep:
        raise ValueError("A edição não contém nenhum trecho para exportar")
    parts = []
    visual = project.get("visual_analysis") or {}
    grade_segments = visual.get("grade_segments") or []
    decisions = (project.get("color_grade") or {}).get("segments") or {}
    unsafe_legacy_review = visual_module.legacy_incomplete_review(visual)
    active_grade_segments = [segment for segment in grade_segments
        if segment.get("layout") == "camera" and segment.get("status") == "reviewable"
        and decisions.get(segment.get("id"), {}).get("enabled") and not unsafe_legacy_review]
    relevant_segments = [segment for segment in grade_segments if any(
        float(segment["start"]) < float(active["end"]) and float(segment["end"]) > float(active["start"])
        for active in active_grade_segments)]
    chunks = []
    for start, end in keep:
        boundaries = sorted({start, end, *[
            point for segment in relevant_segments for point in (float(segment["start"]), float(segment["end"]))
            if start < point < end
        ]})
        chunks.extend((left, right) for left, right in zip(boundaries, boundaries[1:]) if right > left)
    for index, (start, end) in enumerate(chunks):
        vlabel, alabel = f"v{index}", f"a{index}"
        video_filter = f"[0:v]trim=start={start:.3f}:end={end:.3f},setpts=PTS-STARTPTS"
        matches = [segment for segment in grade_segments
                   if float(segment["start"]) <= start and float(segment["end"]) >= end]
        matched = matches[0] if len(matches) == 1 else None
        setting = decisions.get(matched.get("id"), {}) if matched else {}
        if matched and matched.get("layout") == "camera" and matched.get("status") == "reviewable" and setting.get("enabled") and not unsafe_legacy_review:
            suggestion = matched.get("suggestion", {})
            intensity = min(1.0, max(0.0, float(setting.get("intensity", 1))))
            brightness = min(0.05, max(-0.05, float(suggestion.get("brightness", 0)))) * intensity
            contrast = 1 + (min(1.08, max(0.96, float(suggestion.get("contrast", 1)))) - 1) * intensity
            saturation = 1 + (min(1.08, max(0.92, float(suggestion.get("saturation", 1)))) - 1) * intensity
            video_filter += f",eq=brightness={brightness:.4f}:contrast={contrast:.4f}:saturation={saturation:.4f}"
        parts.append(f"{video_filter}[{vlabel}]")
        parts.append(f"[0:a]atrim=start={start:.3f}:end={end:.3f},asetpts=PTS-STARTPTS[{alabel}]")
    inputs = "".join(f"[v{i}][a{i}]" for i in range(len(chunks)))
    parts.append(f"{inputs}concat=n={len(chunks)}:v=1:a=1[basev][basea]")
    grade = project.get("color_grade", {})
    grade_policy = (project.get("visual_analysis") or {}).get("grade_policy", {})
    if grade.get("enabled") and not grade_segments and grade_policy.get("mode") != "preserve" and not unsafe_legacy_review:
        intensity = min(1.0, max(0.0, float(grade.get("intensity", 1.0))))
        suggestion = (project.get("visual_analysis") or {}).get("grade_suggestion", {})
        brightness = min(0.05, max(-0.05, float(suggestion.get("brightness", 0)))) * intensity
        contrast = 1 + (min(1.08, max(0.96, float(suggestion.get("contrast", 1)))) - 1) * intensity
        saturation = 1 + (min(1.08, max(0.92, float(suggestion.get("saturation", 1)))) - 1) * intensity
        parts.append(f"[basev]eq=brightness={brightness:.4f}:contrast={contrast:.4f}:saturation={saturation:.4f}[graded]")
        base_video = "[graded]"
    else:
        base_video = "[basev]"
    if vertical:
        crop_x = min(1.0, max(0.0, crop_x))
        crop_expression = f"{crop_x:.4f}"
        if crop_mode == "track" and crop_track:
            output_track = _crop_track_for_output(crop_track, keep)
            if output_track:
                crop_expression = _crop_expression(output_track, crop_x)
        vertical_filter = f"{base_video}scale=-2:1920,crop=1080:1920:x='(iw-ow)*{crop_expression}':y=0"
        if caption_file and caption_file.is_file():
            subtitle_path = str(caption_file.resolve()).replace("\\", "/").replace(":", "\\:").replace("'", "\\'")
            vertical_filter += f",subtitles=filename='{subtitle_path}':force_style='FontName=DejaVu Sans,FontSize=18,Outline=2,Shadow=0,Alignment=2,MarginV=100'"
        parts.append(f"{vertical_filter}[vout]")
        video_map = "[vout]"
    elif horizontal:
        parts.append(f"{base_video}scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2[landscape]")
        video_map = "[landscape]"
    else:
        video_map = base_video
    destination.parent.mkdir(parents=True, exist_ok=True)
    common = ["ffmpeg", "-hide_banner", "-y", "-i", str(source), "-filter_complex", ";".join(parts), "-map", video_map, "-map", "[basea]"]
    result = None
    if os.getenv("DISABLE_INTEL_QSV") != "1" and Path("/dev/dri/renderD128").exists():
        qsv = common + ["-c:v", "h264_qsv", "-global_quality", "23", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(destination)]
        result = subprocess.run(qsv, capture_output=True, text=True, check=False)
    if result is None or result.returncode != 0:
        cpu = common + ["-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(destination)]
        result = subprocess.run(cpu, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(result.stderr[-3000:] or "FFmpeg export failed")


def _crop_at(track: list[dict[str, Any]], time_s: float, fallback: float) -> float:
    points = sorted((float(item["time"]), min(1.0, max(0.0, float(item["x"])))) for item in track)
    if not points:
        return fallback
    if time_s <= points[0][0]:
        return points[0][1]
    for (left_t, left_x), (right_t, right_x) in zip(points, points[1:]):
        if time_s <= right_t:
            ratio = (time_s - left_t) / max(0.001, right_t - left_t)
            return left_x + (right_x - left_x) * ratio
    return points[-1][1]


def _crop_track_for_output(track: list[dict[str, Any]], keep: list[tuple[float, float]]) -> list[tuple[float, float]]:
    mapped = []
    output_start = 0.0
    for source_start, source_end in keep:
        mapped.append((output_start, _crop_at(track, source_start, 0.5)))
        for item in track:
            source_time = float(item["time"])
            if source_start < source_time < source_end:
                mapped.append((output_start + source_time - source_start, _crop_at(track, source_time, 0.5)))
        mapped.append((output_start + source_end - source_start, _crop_at(track, source_end, 0.5)))
        output_start += source_end - source_start
    return mapped


def _crop_expression(track: list[tuple[float, float]], fallback: float) -> str:
    track = sorted(track)
    expression = f"{track[-1][1]:.4f}" if track else f"{min(1.0, max(0.0, fallback)):.4f}"
    for (left_t, left_x), (right_t, right_x) in reversed(list(zip(track, track[1:]))):
        if right_t <= left_t:
            continue
        segment = f"({left_x:.4f}+({right_x-left_x:.4f})*(t-{left_t:.4f})/{right_t-left_t:.4f})"
        expression = f"if(lte(t,{right_t:.4f}),{segment},{expression})"
    if track:
        expression = f"if(lte(t,{track[0][0]:.4f}),{track[0][1]:.4f},{expression})"
    return expression


def _kept_intervals(duration: float, removed: list[tuple[float, float]]) -> list[tuple[float, float]]:
    intervals = []
    cursor = 0.0
    for start, end in sorted(removed):
        start = min(duration, max(cursor, start))
        end = min(duration, max(start, end))
        if start - cursor >= 0.15:
            intervals.append((cursor, start))
        cursor = max(cursor, end)
    if duration - cursor >= 0.15:
        intervals.append((cursor, duration))
    return intervals


def _output_intervals(duration: float, removed: list[tuple[float, float]], cut: tuple[float, float] | None) -> list[tuple[float, float]]:
    if cut is None:
        return _kept_intervals(duration, removed)
    start, end = max(0.0, cut[0]), min(duration, cut[1])
    if end <= start:
        return []
    local_removed = [(max(a, start) - start, min(b, end) - start) for a, b in removed if b > start and a < end]
    return [(start + a, start + b) for a, b in _kept_intervals(end - start, local_removed)]


def write_captions(project: dict[str, Any], destination: Path, language: str, cut: tuple[float, float] | None = None) -> None:
    captions = project.get("captions", {}).get(language, [])
    duration = project["metadata"]["duration"]
    removed = [(item["start"], item["end"]) for item in project.get("edits", []) if item.get("decision") == "accepted"]
    keep = _output_intervals(duration, removed, cut)
    captions = _map_captions(captions, keep)
    blocks = []
    is_vtt = destination.suffix.lower() == ".vtt"
    for index, item in enumerate(captions, 1):
        start, end = _srt_time(item["start"], is_vtt), _srt_time(item["end"], is_vtt)
        prefix = "" if is_vtt else f"{index}\n"
        blocks.append(f"{prefix}{start} --> {end}\n{item['text']}\n")
    destination.write_text(("WEBVTT\n\n" if is_vtt else "") + "\n".join(blocks), encoding="utf-8")


def _shift_captions(captions: list[dict[str, Any]], removed: list[tuple[float, float]]) -> list[dict[str, Any]]:
    result = []
    for item in captions:
        midpoint = (item["start"] + item["end"]) / 2
        if any(start <= midpoint <= end for start, end in removed):
            continue
        shift = sum(end - start for start, end in removed if end <= item["start"])
        result.append({**item, "start": max(0, item["start"] - shift), "end": max(0.05, item["end"] - shift)})
    return result


def _map_captions(captions: list[dict[str, Any]], keep: list[tuple[float, float]]) -> list[dict[str, Any]]:
    """Clip captions to rendered source intervals and map them onto output time."""
    result = []
    output_offset = 0.0
    for source_start, source_end in keep:
        for item in captions:
            start, end = max(item["start"], source_start), min(item["end"], source_end)
            if end > start:
                result.append({**item, "start": output_offset + start - source_start, "end": output_offset + end - source_start})
        output_offset += source_end - source_start
    return sorted(result, key=lambda item: item["start"])


def _srt_time(value: float, vtt: bool = False) -> str:
    millis = int(max(0, value) * 1000)
    hours, millis = divmod(millis, 3_600_000)
    minutes, millis = divmod(millis, 60_000)
    seconds, millis = divmod(millis, 1000)
    separator = "." if vtt else ","
    return f"{hours:02}:{minutes:02}:{seconds:02}{separator}{millis:03}"
