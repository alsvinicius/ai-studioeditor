import json
import unittest
from unittest.mock import patch

from app import ai_analysis
from app.ai_providers import PROVIDERS


class OpenCodeTextTests(unittest.TestCase):
    def test_transcription_stops_if_many_segments_advance_only_milliseconds(self):
        import sys
        import types
        from pathlib import Path
        from app.media import transcribe
        class Model:
            def __init__(self, *args, **kwargs): pass
            def transcribe(self, *args, **kwargs):
                segments = [types.SimpleNamespace(start=1+i*.009, end=1.001+i*.009, text="fala", words=[], avg_logprob=0, no_speech_prob=0, compression_ratio=1) for i in range(100)]
                return iter(segments), types.SimpleNamespace(language="pt", duration=100)
        with patch.dict(sys.modules, {"faster_whisper": types.SimpleNamespace(WhisperModel=Model)}):
            with self.assertRaisesRegex(RuntimeError, "segmentos excessivos"):
                transcribe(Path("video.mp4"), model_name="medium")

    def test_transcription_stops_if_timestamps_never_advance(self):
        import sys
        import types
        from pathlib import Path
        from app.media import transcribe
        segment = types.SimpleNamespace(start=1, end=2, text="fala", words=[], avg_logprob=0, no_speech_prob=0, compression_ratio=1)
        class Model:
            def __init__(self, *args, **kwargs): pass
            def transcribe(self, *args, **kwargs): return iter([segment] * 31), types.SimpleNamespace(language="pt", duration=100)
        with patch.dict(sys.modules, {"faster_whisper": types.SimpleNamespace(WhisperModel=Model)}):
            with self.assertRaisesRegex(RuntimeError, "parou de avançar"):
                transcribe(Path("video.mp4"), model_name="medium")

    def test_extreme_text_density_is_reviewable_without_word_timestamps(self):
        from app.transcript_quality import anomalies
        segment = {"id": "s1", "start": 1, "end": 1.5, "text": "uma frase de dez palavras que apareceu em meio segundo"}
        found = anomalies([segment])
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]["kind"], "speech-density")

    def test_long_run_of_tiny_segments_is_reported_as_one_fragmentation_range(self):
        from app.transcript_quality import anomalies
        segments = [{"id": f"s{i}", "start": i * 0.3, "end": i * 0.3 + 0.2, "text": f"palavra{i}"}
                    for i in range(20)]
        found = anomalies(segments)
        fragmentation = [item for item in found if item["kind"] == "segment-fragmentation"]
        self.assertEqual(len(fragmentation), 1)
        self.assertEqual(fragmentation[0]["segment_count"], 20)
        self.assertEqual(fragmentation[0]["start"], 0)
        self.assertAlmostEqual(fragmentation[0]["end"], 5.9)

    def test_short_normal_transcript_is_not_flagged_as_fragmented(self):
        from app.transcript_quality import anomalies
        segments = [{"id": f"s{i}", "start": i * 0.3, "end": i * 0.3 + 0.2, "text": f"palavra{i}"}
                    for i in range(11)]
        self.assertEqual(anomalies(segments), [])

    def test_malformed_evidence_cannot_abort_the_whole_analysis(self):
        transcript = [{"start": 0, "end": 3, "text": "uma frase comum aqui"}]
        response = json.dumps({"edits": [
            {"start": 0, "end": 3, "quote": {"bad": "type"}, "reason": "erro", "confidence": "high", "editorial_intent": True},
            {"start": 0, "end": 3, "quote": "uma frase comum aqui", "reason": "candidato válido", "confidence": "medium"}],
            "shorts": [], "youtube_cuts": []})
        with patch("app.ai_providers.run_prompt", return_value=response):
            edits, _, result = ai_analysis.analyze_transcript(transcript, 10)
        self.assertEqual(result["opencode"]["status"], "complete")
        self.assertEqual(len(edits), 1)

    def test_semantic_quote_must_be_anchored_to_proposed_interval(self):
        words = [{"start": 90 + i, "end": 90.5 + i, "text": word} for i, word in enumerate("frase citada em outro momento".split())]
        segment = {"start": 0, "end": 100, "text": "frase citada em outro momento", "words": words}
        quote = segment["text"]
        self.assertFalse(ai_analysis._quote_matches(quote, [segment], 5, 10))
        self.assertTrue(ai_analysis._quote_matches(quote, [segment], 90, 95))
        legacy = {"start": 0, "end": 100, "text": quote}
        self.assertFalse(ai_analysis._quote_matches(quote, [legacy], 5, 10))
        self.assertTrue(ai_analysis._quote_matches(quote, [legacy], 0, 100))

    def test_cli_timeout_is_reported_without_sensitive_command(self):
        import subprocess
        error = subprocess.TimeoutExpired(cmd=["secret-command"], timeout=240)
        self.assertEqual(ai_analysis._safe_error(error), "tempo limite esgotado")

    def test_transcription_progress_uses_audio_position(self):
        import sys
        import types
        from pathlib import Path
        from app.media import transcribe
        segment = lambda end: types.SimpleNamespace(start=end - 1, end=end, text="fala", words=[], avg_logprob=0, no_speech_prob=0, compression_ratio=1)
        class Model:
            def __init__(self, *args, **kwargs): pass
            def transcribe(self, *args, **kwargs):
                return iter([segment(2), segment(18), segment(40)]), types.SimpleNamespace(language="pt", duration=100)
        updates = []
        with patch.dict(sys.modules, {"faster_whisper": types.SimpleNamespace(WhisperModel=Model)}):
            transcribe(Path("video.mp4"), lambda value, message: updates.append((value, message)), "medium", "pt")
        self.assertIn("00:40 de 01:40", updates[-1][1])
        self.assertAlmostEqual(updates[-1][0], .12 + .4 * .53)

    def test_transcript_gap_does_not_create_a_silence_cut(self):
        from app.media import suggest_edits, suggest_audio_silence_edits
        segments = [{"start": 4, "end": 5, "text": "um"}, {"start": 12, "end": 14, "text": "dois"}]
        self.assertEqual(suggest_edits(segments, 20), [])
        self.assertEqual(suggest_audio_silence_edits(segments, 20, []), [])

    def test_tail_suggestion_cannot_start_before_measured_silence(self):
        from app.media import suggest_audio_silence_edits
        segments = [{"start": 0, "end": 10, "text": "última fala reconhecida"}]
        edits = suggest_audio_silence_edits(segments, 20, [{"start": 17, "end": 20}])
        self.assertEqual(len(edits), 1)
        self.assertEqual(edits[0]["start"], 17.1)

    def test_does_not_suggest_removal_from_collapsed_asr_words(self):
        suspect = {"id": "s1", "start": 501.08, "end": 503.28,
            "text": "Ele tem o Cloud que é mais barato Então ele tem o Cloud que é mais barato",
            "words": [{"start": 502.22, "end": 502.22, "text": word} for word in
                      "Ele tem o Cloud que é mais barato Então ele tem o Cloud que é mais barato".split()]}
        healthy = {"id": "s2", "start": 510, "end": 513, "text": "Agora vamos falar de contexto",
            "words": [{"start": 510+i*.3, "end": 510+i*.3+.2, "text": word} for i, word in enumerate("Agora vamos falar de contexto".split())]}
        response = json.dumps({"edits": [
            {"start": 501.08, "end": 503.28, "quote": suspect["text"], "reason": "repetição", "confidence": "high"},
            {"start": 510, "end": 513, "quote": healthy["text"], "reason": "trecho", "confidence": "medium"},
        ], "shorts": [], "youtube_cuts": []})
        with patch("app.ai_providers.run_prompt", return_value=response):
            edits, _, details = ai_analysis.analyze_transcript([suspect, healthy], 520)
        self.assertEqual([(e["start"], e["end"]) for e in edits], [(510, 513)])
        self.assertEqual(details["opencode"]["blocked_edits_asr"], 1)

    def test_external_editorial_quote_with_bad_alignment_does_not_validate_cut(self):
        from app import transcript_quality
        target = {"id": "s1", "start": 10, "end": 13, "text": "Esta é a tentativa anterior"}
        quote = "Vou cortar essa última parte"
        suspect = {"id": "s2", "start": 15, "end": 16, "text": quote,
                   "words": [{"start": 15.5, "end": 15.5, "text": word} for word in quote.split()]}
        self.assertEqual(len(transcript_quality.anomalies([target, suspect])), 1)
        response = json.dumps({"edits": [{"start": 10, "end": 13, "quote": quote,
            "reason": "tentativa", "confidence": "high", "editorial_intent": True}], "shorts": [], "youtube_cuts": []})
        with patch("app.ai_providers.run_prompt", return_value=response):
            edits, _, _ = ai_analysis.analyze_transcript([target, suspect], 20)
        self.assertEqual(edits, [])

    def test_editorial_command_without_a_locatable_restart_is_not_a_complete_cut(self):
        # An explicit command alone cannot prove which previous speech to remove.
        transcript = [
            {"start": 67.7, "end": 76.16, "text": "tentativa anterior", "words": [{"start": 67.7, "end": 68, "text": "tentativa"}, {"start": 68, "end": 76.16, "text": "anterior"}]},
            {"start": 79.32, "end": 82.28, "text": "Vou cortar essa última parte, deu uma gaguejada.", "words": [
                {"start": a, "end": b, "text": t} for a, b, t in [
                    (79.32, 79.78, "Vou"), (79.78, 80.24, "cortar"), (80.24, 80.42, "essa"),
                    (80.42, 80.64, "última"), (80.64, 81.06, "parte,"), (81.16, 81.38, "deu"),
                    (81.38, 81.7, "uma"), (81.7, 82.28, "gaguejada.")]]},
            {"start": 82.44, "end": 85.14, "text": "Então opções pagas", "words": [
                {"start": 82.44, "end": 82.58, "text": "Então"}, {"start": 82.6, "end": 83.42, "text": "opções"}, {"start": 83.42, "end": 85.14, "text": "pagas"}]},
        ]
        response = json.dumps({"edits": [{"start": 67.7, "end": 76.16, "reason": "tentativa anterior",
            "quote": transcript[1]["text"], "confidence": "medium", "editorial_intent": True}], "shorts": [], "youtube_cuts": []})
        with patch("app.ai_providers.run_prompt", return_value=response):
            edits, _, details = ai_analysis.analyze_transcript(transcript, 100)
        self.assertEqual(edits, [])
        self.assertEqual(details["opencode"]["retake_review"]["status"], "needs-review")

    def test_editorial_comment_requires_unique_unchanged_word_alignment(self):
        quote = "Vou cortar essa última parte"
        words = [{"start": i + 5, "end": i + 5.5, "text": w} for i, w in enumerate(quote.split())]
        segment = {"start": 5, "end": 9.5, "text": quote, "words": words}
        locate = ai_analysis._editorial_comment_interval
        self.assertEqual(locate(quote, [segment], 1, 5, 30), (5.0, 9.5))
        self.assertIsNone(locate(quote, [segment, segment], 1, 5, 30))
        self.assertIsNone(locate(quote, [{**segment, "text": "texto corrigido"}], 1, 5, 30))
        distant = {**segment, "words": [{**word, "start": word["start"] + 2, "end": word["end"] + 2} for word in words]}
        self.assertIsNone(locate(quote, [distant], 0, 1, 30))

    def test_editorial_comment_without_a_locatable_restart_is_not_promoted(self):
        transcript = [
            {"start": 70.5, "end": 80.08, "text": "tentativa vou", "words": [
                {"start": 70.5, "end": 76.44, "text": "tentativa"}, {"start": 79.14, "end": 80.08, "text": "vou"}]},
            {"start": 80.08, "end": 83.2, "text": "cortar essa parte deu uma gaguejada então", "words": [
                {"start": a, "end": b, "text": t} for a, b, t in [(80.08, 80.38, "cortar"),
                    (80.38, 80.56, "essa"), (80.56, 81.18, "parte"), (81.6, 81.68, "deu"),
                    (81.68, 81.92, "uma"), (81.92, 82.46, "gaguejada"), (83.1, 83.2, "então")]]},
        ]
        response = json.dumps({"edits": [{"start": 70.5, "end": 80.08, "reason": "tentativa",
            "quote": "vou cortar essa parte deu uma gaguejada", "confidence": "medium", "editorial_intent": True}], "shorts": [], "youtube_cuts": []})
        with patch("app.ai_providers.run_prompt", return_value=response):
            edits, _, _ = ai_analysis.analyze_transcript(transcript, 100)
        self.assertEqual(edits, [])

    def test_retry_preserves_reviewed_items_and_user_changes(self):
        previous = [
            {"id": "a", "start": 1, "end": 4, "decision": "accepted", "title": "Meu título", "crop_x": 0.3},
            {"id": "b", "start": 8, "end": 10, "decision": "rejected"},
        ]
        candidates = [{"id": "new", "start": 1, "end": 4, "decision": "pending", "title": "Modelo"}]
        result = ai_analysis.preserve_decisions(candidates, previous)
        self.assertEqual(result[0]["title"], "Meu título")
        self.assertEqual(result[0]["crop_x"], 0.3)
        self.assertEqual(result[1], previous[1])

    def test_transcript_analysis_uses_fixed_opencode_model(self):
        outputs = []
        transcript = [{"start": 0.0, "end": 3.0, "text": "Olá pessoal, vamos começar."}]
        response = json.dumps({"edits": [], "shorts": [], "youtube_cuts": []})
        with patch("app.ai_providers.run_prompt", side_effect=lambda provider, prompt, **kwargs: outputs.append(prompt) or response):
            edits, cuts, models = ai_analysis.analyze_transcript(transcript, 10)

        self.assertEqual(PROVIDERS["opencode"]["model"], "opencode/mimo-v2.6-flash-free")
        self.assertIn("Olá pessoal", outputs[0])
        self.assertEqual(models["opencode"]["model"], PROVIDERS["opencode"]["model"])
        self.assertEqual(models["opencode"]["status"], "complete")
        self.assertEqual((edits, cuts), ([], []))

    def test_lexical_similarity_alone_does_not_create_a_retake(self):
        segments = [
            {"start": 0, "end": 2, "text": "Python resolve outro problema"},
            {"start": 2, "end": 4, "text": "C resolve outro problema"},
            {"start": 4, "end": 6, "text": "R resolve outro problema"},
        ]
        edits = ai_analysis.merge_edits([], __import__("app.media", fromlist=["suggest_edits"]).suggest_edits(segments, 8))
        self.assertFalse(any(item["kind"] == "possible-retake" for item in edits))

    def test_measured_audio_tail_below_three_seconds_becomes_reviewable(self):
        from app.media import suggest_audio_silence_edits
        segments = [{"start": 982.1, "end": 982.82, "text": "muito obrigado gente"}]
        intervals = [{"start": 982.524, "end": 985.429, "duration": 2.905, "noise_db": -35}]
        edits = suggest_audio_silence_edits(segments, 985.45, intervals)
        self.assertEqual(len(edits), 1)
        self.assertEqual(edits[0]["kind"], "ending-silence")
        self.assertEqual(edits[0]["decision"], "pending")
        self.assertGreaterEqual(edits[0]["start"], segments[-1]["end"])
        self.assertAlmostEqual(edits[0]["start"], 982.92)
        self.assertEqual(edits[0]["end"], 985.45)

    def test_parallel_list_is_not_proposed_as_retake_without_editorial_cue(self):
        transcript = [
            {"start": 0, "end": 2, "text": "Python resolve outro problema"},
            {"start": 2, "end": 4, "text": "C resolve outro problema"},
            {"start": 4, "end": 6, "text": "R resolve outro problema"},
        ]
        response = json.dumps({"edits": [{"start": 0, "end": 6, "reason": "repetição", "quote": "Python resolve outro problema C resolve outro problema R resolve outro problema", "confidence": "high"}], "shorts": [], "youtube_cuts": []})
        with patch("app.ai_providers.run_prompt", return_value=response):
            edits, _, _ = ai_analysis.analyze_transcript(transcript, 8)
        self.assertEqual(edits, [])

    def test_model_must_return_horizontal_cut_collection(self):
        with self.assertRaises(ValueError):
            ai_analysis._parse_model_json('{"edits":[],"shorts":[]}')


if __name__ == "__main__":
    unittest.main()
