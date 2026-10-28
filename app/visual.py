from __future__ import annotations

import io
import math
from pathlib import Path
from typing import Any


def legacy_incomplete_review(analysis: dict[str, Any]) -> bool:
    """Older results omitted missing frames and could extrapolate their neighbours."""
    scene = analysis.get("scene_review") or {}
    count = scene.get("sample_count")
    frames = scene.get("frames")
    return (scene.get("classified_count") is None and isinstance(count, int) and count > 0
            and isinstance(frames, list) and len(frames) < count)


def analyze_video(path: Path, duration: float, width: int, height: int,
                  start: float = 0.0, end: float | None = None, sample_budget: int = 240) -> dict[str, Any]:
    """Inspect sampled frames locally for face framing and conservative image correction."""
    try:
        import cv2
        import numpy as np
    except ImportError as exc:
        raise RuntimeError("Análise visual local indisponível. Recrie a imagem do aplicativo.") from exc

    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        raise ValueError("Não foi possível ler o vídeo para análise visual")
    detector = cv2.CascadeClassifier(str(Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"))
    end = min(duration, duration if end is None else end)
    start = max(0.0, min(end, start))
    sample_step = max(0.5, (end - start) / max(1, sample_budget))
    samples: list[dict[str, float]] = []
    luma, shadow_clip, highlight_clip, saturation = [], [], [], []
    frame_differences, edge_density, face_area_ratio = [], [], []
    previous_thumbnail = None
    previous: tuple[float, float] | None = None
    detected = 0
    frame_metrics: list[dict[str, float]] = []
    time_s = start
    try:
        while time_s <= duration:
            capture.set(cv2.CAP_PROP_POS_MSEC, time_s * 1000)
            ok, frame = capture.read()
            if not ok:
                time_s += sample_step
                continue
            frame_h, frame_w = frame.shape[:2]
            scale = min(1.0, 640 / max(frame_w, frame_h))
            if scale < 1:
                frame = cv2.resize(frame, (round(frame_w * scale), round(frame_h * scale)))
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = detector.detectMultiScale(gray, scaleFactor=1.12, minNeighbors=5, minSize=(30, 30))
            if len(faces):
                center = (frame.shape[1] / 2, frame.shape[0] / 2) if previous is None else previous
                face = min(faces, key=lambda item: math.dist((item[0] + item[2] / 2, item[1] + item[3] / 2), center) - item[2] * 0.18)
                cx = (float(face[0]) + float(face[2]) / 2) / frame.shape[1]
                cy = (float(face[1]) + float(face[3]) / 2) / frame.shape[0]
                previous = (cx * frame.shape[1], cy * frame.shape[0])
                detected += 1
                # Place the detected face near the upper-middle portion of a 9:16 frame.
                target_scaled_x = cx * width * 1920 / height
                source_scaled_width = width * 1920 / height
                crop_width = 1080
                crop_x = min(1.0, max(0.0, (target_scaled_x - crop_width * 0.5) / max(1.0, source_scaled_width - crop_width)))
                samples.append({"time": round(time_s, 3), "x": round(crop_x, 4), "face_y": round(cy, 4)})
                face_area_ratio.append(float(face[2] * face[3]) / (frame.shape[0] * frame.shape[1]))
            small = cv2.resize(frame, (160, 90))
            thumbnail = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
            if previous_thumbnail is not None:
                frame_differences.append(float(np.mean(cv2.absdiff(previous_thumbnail, thumbnail))) / 255)
            previous_thumbnail = thumbnail
            edge_density.append(float(np.mean(cv2.Canny(thumbnail, 80, 160) > 0)))
            yuv = cv2.cvtColor(small, cv2.COLOR_BGR2YCrCb)
            hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
            plane = yuv[:, :, 0]
            luma.append(float(np.mean(plane)) / 255)
            shadow_clip.append(float(np.mean(plane <= 16)))
            highlight_clip.append(float(np.mean(plane >= 240)))
            saturation.append(float(np.mean(hsv[:, :, 1])) / 255)
            frame_metrics.append({"time": round(time_s, 3),
                                  "luma": round(float(np.mean(plane)) / 255, 4),
                                  "shadow_clipping": round(float(np.mean(plane <= 16)), 4),
                                  "highlight_clipping": round(float(np.mean(plane >= 240)), 4),
                                  "saturation": round(float(np.mean(hsv[:, :, 1])) / 255, 4)})
            time_s += sample_step
    finally:
        capture.release()

    if not luma:
        raise ValueError("Não foi possível extrair quadros para análise visual")
    smoothed_track = []
    for index, sample in enumerate(samples):
        neighbors = samples[max(0, index - 1):min(len(samples), index + 2)]
        smoothed_x = sum(float(item["x"]) for item in neighbors) / len(neighbors)
        smoothed_track.append({**sample, "x": round(smoothed_x, 4)})
    median_luma = float(np.median(luma))
    median_sat = float(np.median(saturation))
    stable_scene_ratio = float(np.mean(np.asarray(frame_differences) < 0.025)) if frame_differences else 0.0
    screen_like = bool(
        len(frame_differences) >= 8 and stable_scene_ratio >= 0.7
        and float(np.median(edge_density)) >= 0.035
        and (not face_area_ratio or float(np.median(face_area_ratio)) <= 0.08)
    )
    brightness = round(min(0.05, max(-0.05, (0.46 - median_luma) * 0.12)), 4)
    contrast = round(min(1.08, max(0.96, 1.02 + (0.20 - float(np.median(shadow_clip) + np.median(highlight_clip))) * 0.08)), 4)
    saturation_gain = 1.04 if median_sat < 0.16 else 1.0
    confidence = "high" if len(samples) >= 3 and detected / max(1, len(luma)) >= 0.55 else "medium" if samples else "low"
    return {
        "status": "complete", "sample_count": len(luma), "sample_interval": round(sample_step, 2),
        "sample_range": {"start": round(start, 3), "end": round(end, 3)}, "frame_metrics": frame_metrics,
        "face_detection_ratio": round(detected / max(1, len(luma)), 3), "framing_confidence": confidence,
        "scene_analysis": {"local_presentation_suspected": screen_like,
                           "stable_scene_ratio": round(stable_scene_ratio, 3),
                           "median_edge_density": round(float(np.median(edge_density)), 3)},
        "grade_policy": {"mode": "preserve" if screen_like else "global_allowed",
                         "reason": "Conteúdo de tela estático ocupa a maior parte do quadro" if screen_like else "Nenhum conteúdo de tela dominante detectado localmente",
                         "source": "local-heuristic"},
        "crop_track": smoothed_track, "metrics": {
            "median_luma": round(median_luma, 3), "shadow_clipping": round(float(np.median(shadow_clip)), 3),
            "highlight_clipping": round(float(np.median(highlight_clip)), 3), "median_saturation": round(median_sat, 3),
        },
        "grade_suggestion": {"brightness": brightness, "contrast": contrast, "saturation": saturation_gain},
    }


def grade_segments(path: Path, duration: float, segments: list[dict[str, Any]],
                   width: int, height: int) -> list[dict[str, Any]]:
    """Measure camera scenes independently; unknown and screen scenes stay neutral."""
    result = []
    for index, scene in enumerate(segments):
        layout = scene.get("layout", "unknown")
        start, end = float(scene.get("start", 0)), float(scene.get("end", 0))
        grade = {"brightness": 0.0, "contrast": 1.0, "saturation": 1.0}
        metrics = None
        status = "preserve"
        reason = "Layout não classificado como câmera; cores preservadas."
        if layout == "camera" and scene.get("confidence") in {"medium", "high"} and end > start:
            try:
                analysis = analyze_video(path, duration, width, height, start, end, sample_budget=24)
                metrics = analysis["metrics"]
                grade = analysis["grade_suggestion"]
                status = "reviewable"
                reason = "Sugestão medida somente neste intervalo de câmera."
            except Exception as exc:
                reason = f"Medição indisponível ({type(exc).__name__}); cores preservadas."
        result.append({"id": scene.get("id", f"scene-{index+1}"), "start": start, "end": end,
                       "layout": layout, "confidence": scene.get("confidence", "low"),
                       "status": status, "enabled": False, "intensity": 1.0,
                       "metrics": metrics, "suggestion": grade, "reason": reason})
    return result


def inspect_render(path: Path, cut_boundaries: list[float] | None = None, expected_size: tuple[int, int] | None = None, expected_duration: float | None = None) -> dict[str, Any]:
    """Check output dimensions and sampled exposure, including windows around edit joins."""
    import cv2
    import numpy as np

    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        raise ValueError("Não foi possível verificar o vídeo exportado")
    fps = capture.get(cv2.CAP_PROP_FPS) or 30.0
    count = capture.get(cv2.CAP_PROP_FRAME_COUNT)
    duration = count / fps if fps else 0.0
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    points = {0.5, max(0.0, duration - 0.5), duration / 2}
    for boundary in cut_boundaries or []:
        points.update({max(0.0, boundary - 1.5), max(0.0, boundary - 0.25), min(duration, boundary + 0.25), min(duration, boundary + 1.5)})
    samples = []
    try:
        for point in sorted(value for value in points if 0 <= value < duration):
            capture.set(cv2.CAP_PROP_POS_MSEC, point * 1000)
            ok, frame = capture.read()
            if not ok:
                samples.append({"time": round(point, 3), "readable": False})
                continue
            gray = cv2.cvtColor(cv2.resize(frame, (160, 90)), cv2.COLOR_BGR2GRAY)
            samples.append({"time": round(point, 3), "readable": True, "luma": round(float(np.mean(gray)) / 255, 3), "dark_fraction": round(float(np.mean(gray <= 16)), 3), "bright_fraction": round(float(np.mean(gray >= 240)), 3)})
    finally:
        capture.release()
    warnings = []
    if expected_size and (width, height) != expected_size:
        warnings.append(f"Dimensão inesperada: {width} × {height}; esperado {expected_size[0]} × {expected_size[1]}.")
    if expected_duration is not None and abs(duration - expected_duration) > max(0.12, 2 / max(fps, 1)):
        warnings.append(f"Duração diferente do esperado: {duration:.2f}s; esperado {expected_duration:.2f}s.")
    if any(not sample.get("readable") for sample in samples):
        warnings.append("Alguns quadros da verificação não puderam ser lidos.")
    if any(sample.get("dark_fraction", 0) > 0.4 for sample in samples):
        warnings.append("Há quadros com áreas muito escuras; confira a imagem exportada.")
    if any(sample.get("bright_fraction", 0) > 0.4 for sample in samples):
        warnings.append("Há quadros com áreas muito claras; confira a imagem exportada.")
    boundary_samples = [sample for sample in samples if any(abs(sample["time"] - boundary) <= 1.6 for boundary in cut_boundaries or [])]
    for left, right in zip(boundary_samples, boundary_samples[1:]):
        if left.get("luma") is not None and right.get("luma") is not None and abs(left["luma"] - right["luma"]) > 0.28:
            warnings.append(f"Variação forte de exposição perto de {right['time']:.2f}s; confira a transição.")
            break
    return {"width": width, "height": height, "duration": round(duration, 3), "samples": samples, "warnings": warnings}


def preview_contact_sheet(
    path: Path,
    duration: float,
    grade_suggestion: dict[str, Any],
    intensity: float = 1.0,
    crop_x: float = 0.5,
    preserve_colors: bool = False,
    moments: list[float] | None = None,
) -> bytes:
    """Build a local contact sheet comparing source, suggested grade, and 9:16 crops."""
    import cv2
    import numpy as np

    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        raise ValueError("Não foi possível ler o vídeo para gerar a prévia visual")

    bounded_intensity = min(1.0, max(0.0, float(intensity)))
    bounded_crop_x = min(1.0, max(0.0, float(crop_x)))
    brightness = min(0.05, max(-0.05, float(grade_suggestion.get("brightness", 0)))) * bounded_intensity
    contrast = 1 + (min(1.08, max(0.96, float(grade_suggestion.get("contrast", 1)))) - 1) * bounded_intensity
    saturation = 1 + (min(1.08, max(0.92, float(grade_suggestion.get("saturation", 1)))) - 1) * bounded_intensity

    tile_width, tile_height, label_height = 480, 270, 30
    moments = moments or [min(max(0.0, duration - 0.05), duration * fraction) for fraction in (0.12, 0.5, 0.88)]
    moments = [min(max(0.0, duration - 0.05), float(value)) for value in moments[:3]]
    vertical_height = 480
    canvas = np.full((2 * (tile_height + label_height) + vertical_height + label_height, 3 * tile_width, 3), (25, 32, 29), dtype=np.uint8)

    def fit(frame, width: int, height: int):
        scale = min(width / frame.shape[1], height / frame.shape[0])
        resized = cv2.resize(frame, (max(1, round(frame.shape[1] * scale)), max(1, round(frame.shape[0] * scale))))
        output = np.full((height, width, 3), (20, 26, 23), dtype=np.uint8)
        top, left = (height - resized.shape[0]) // 2, (width - resized.shape[1]) // 2
        output[top:top + resized.shape[0], left:left + resized.shape[1]] = resized
        return output

    def apply_grade(frame):
        graded = np.clip(((frame.astype(np.float32) / 255.0 - 0.5) * contrast + 0.5 + brightness) * 255.0, 0, 255).astype(np.uint8)
        if abs(saturation - 1.0) > 0.0001:
            yuv = cv2.cvtColor(graded, cv2.COLOR_BGR2YUV).astype(np.float32)
            yuv[:, :, 1:] = np.clip((yuv[:, :, 1:] - 128.0) * saturation + 128.0, 0, 255)
            graded = cv2.cvtColor(yuv.astype(np.uint8), cv2.COLOR_YUV2BGR)
        return graded

    def vertical_crop(frame):
        frame_h, frame_w = frame.shape[:2]
        target_ratio = 9 / 16
        if frame_w / frame_h > target_ratio:
            crop_w = max(1, round(frame_h * target_ratio))
            left = round((frame_w - crop_w) * bounded_crop_x)
            frame = frame[:, left:left + crop_w]
        else:
            crop_h = max(1, round(frame_w / target_ratio))
            top = max(0, (frame_h - crop_h) // 2)
            frame = frame[top:top + crop_h, :]
        return frame

    try:
        for column, timestamp in enumerate(moments):
            capture.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)
            ok, frame = capture.read()
            if not ok:
                raise ValueError(f"Não foi possível ler um quadro em {timestamp:.2f}s")
            graded = apply_grade(frame)
            vertical = vertical_crop(graded)
            clock = f"{int(timestamp // 60):02d}:{int(timestamp % 60):02d}"
            middle_label = "ORIGINAL PRESERVADO" if preserve_colors else "GRADE"
            panels = [(frame, f"ORIGINAL {clock}"), (graded, f"{middle_label} {clock}"), (vertical, f"VERTICAL 9:16 {clock}")]
            for row, (panel, label) in enumerate(panels):
                x = column * tile_width
                y = row * (tile_height + label_height) if row < 2 else 2 * (tile_height + label_height)
                cv2.putText(canvas, label, (x + 12, y + 21), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (214, 231, 221), 1, cv2.LINE_AA)
                if row < 2:
                    canvas[y + label_height:y + label_height + tile_height, x:x + tile_width] = fit(panel, tile_width, tile_height)
                else:
                    canvas[y + label_height:y + label_height + vertical_height, x:x + tile_width] = fit(panel, tile_width, vertical_height)
    finally:
        capture.release()

    encoded, buffer = cv2.imencode(".jpg", canvas, [cv2.IMWRITE_JPEG_QUALITY, 86])
    if not encoded:
        raise ValueError("Não foi possível codificar a prévia visual")
    return buffer.tobytes()
