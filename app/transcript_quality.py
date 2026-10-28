from __future__ import annotations

import math
import re
from typing import Any


def anomalies(segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Find obvious alignment failures and unusually fragmented Whisper output."""
    result = []
    fragmented = []
    for index, segment in enumerate(segments):
        words = segment.get("words") or []
        try:
            start, end = float(segment["start"]), float(segment["end"])
            if not (math.isfinite(start) and math.isfinite(end) and start < end):
                continue
            zero = sum(1 for word in words if float(word["end"]) <= float(word["start"]))
        except (KeyError, TypeError, ValueError):
            continue
        collapsed = len(words) >= 5 and zero / len(words) >= 0.4
        text_word_count = len(re.findall(r"\w+", str(segment.get("text", ""))))
        crowded = text_word_count >= 8 and text_word_count / (end - start) > 10
        if text_word_count <= 2 and end - start <= 0.65:
            fragmented.append((index, start, end))
        if collapsed or crowded:
            result.append({"segment_id": segment.get("id"), "segment_index": index,
                "start": start, "end": end, "kind": "word-alignment" if collapsed else "speech-density",
                "zero_duration_words": zero, "word_count": len(words), "text_word_count": text_word_count})
    run = []
    for item in fragmented:
        if run and (item[0] != run[-1][0] + 1 or item[1] - run[-1][2] > 0.6):
            if len(run) >= 12:
                result.append({"segment_id": segments[run[0][0]].get("id"),
                    "segment_index": run[0][0], "start": run[0][1], "end": run[-1][2],
                    "kind": "segment-fragmentation", "segment_count": len(run)})
            run = []
        run.append(item)
    if len(run) >= 12:
        result.append({"segment_id": segments[run[0][0]].get("id"),
            "segment_index": run[0][0], "start": run[0][1], "end": run[-1][2],
            "kind": "segment-fragmentation", "segment_count": len(run)})
    result.sort(key=lambda item: (item["start"], item["kind"]))
    return result


def quote_touches_anomaly(quote: str, segments: list[dict[str, Any]], suspect_indices: set[int]) -> bool:
    """Consider all literal matches: an ambiguous match is unsafe if any match is suspect."""
    tokens = []
    for index, segment in enumerate(segments):
        tokens.extend((word, index) for word in re.findall(r"\w+", str(segment.get("text", "")).lower()))
    sought = re.findall(r"\w+", str(quote).lower())
    if len(sought) < 3:
        return False
    for i in range(len(tokens) - len(sought) + 1):
        match = tokens[i:i + len(sought)]
        if [word for word, _ in match] == sought and any(index in suspect_indices for _, index in match):
            return True
    return False
