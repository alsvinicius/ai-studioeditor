import json
import unittest
from unittest.mock import patch

from app import ai_analysis


def segment(segment_id, start, end, text):
    tokens = text.split()
    width = (end - start) / len(tokens)
    words = [{"text": token, "start": start + index * width,
              "end": start + (index + 1) * width}
             for index, token in enumerate(tokens)]
    return {"id": segment_id, "start": start, "end": end,
            "text": text, "words": words}


class RetakeResolverTests(unittest.TestCase):
    def setUp(self):
        self.transcript = [
            segment("s17", 147.28, 154.20,
                    "E isso daqui não se deve só ao propósito probabilístico."),
            segment("s18", 154.78, 156.04, "Vou refazer isso."),
            segment("s19", 156.58, 163.20,
                    "E isso não se deve apenas ao modelo probabilístico que é como um LLM funciona."),
        ]
        self.resolved = json.dumps({
            "status": "resolved",
            "reason": "A explicação é retomada em seguida com a formulação corrigida.",
            "discard_word_ids": [f"s0:w{i}" for i in range(10)],
            "comment_word_ids": [f"s1:w{i}" for i in range(3)],
            "keep_word_ids": [f"s2:w{i}" for i in range(15)],
        })

    def test_retakes_attempt_and_command_as_one_cut_and_shows_kept_restart(self):
        base = json.dumps({"edits": [], "shorts": [], "youtube_cuts": []})
        with patch("app.ai_providers.run_prompt", side_effect=[base, self.resolved]):
            edits, _, _ = ai_analysis.analyze_transcript(self.transcript, 200, provider="codex")
        self.assertEqual(len(edits), 1)
        edit = edits[0]
        self.assertAlmostEqual(edit["start"], 147.28)
        self.assertAlmostEqual(edit["end"], 156.04)
        self.assertEqual(edit["retake_evidence"]["discard"]["text"],
                         "E isso daqui não se deve só ao propósito probabilístico.")
        self.assertEqual(edit["retake_evidence"]["comment"]["text"], "Vou refazer isso.")
        self.assertEqual(edit["retake_evidence"]["keep"]["text"],
                         "E isso não se deve apenas ao modelo probabilístico que é como um LLM funciona.")

    def test_missing_word_alignment_never_promotes_command_alone(self):
        transcript = [{"id": "s0", "start": 10, "end": 11, "text": "Vou refazer isso."}]
        edits, diagnostics = ai_analysis._resolve_retake_edits(transcript, 20, "codex")
        self.assertEqual(edits, [])
        self.assertEqual(diagnostics["status"], "needs-review")

    def test_incomplete_command_cut_is_suppressed_when_retake_is_unresolved(self):
        ambiguous = json.dumps({"status": "ambiguous", "reason": "Tentativa não confirmada.",
            "discard_word_ids": [], "comment_word_ids": [], "keep_word_ids": []})
        for editorial in (True, False):
            with self.subTest(editorial_intent=editorial):
                base = json.dumps({"edits": [{"start": 154.78, "end": 156.04,
                    "reason": "Comentário editorial", "quote": "Vou refazer isso.",
                    "confidence": "high", "editorial_intent": editorial}], "shorts": [], "youtube_cuts": []})
                with patch("app.ai_providers.run_prompt", side_effect=[base, ambiguous]):
                    edits, _, details = ai_analysis.analyze_transcript(self.transcript, 200, provider="codex")
                self.assertEqual(edits, [])
                self.assertEqual(details["codex"]["retake_review"]["status"], "needs-review")

    def test_resolver_rejects_model_that_does_not_confirm_retaking(self):
        with patch("app.ai_providers.run_prompt", return_value=json.dumps({
                "status": "ambiguous", "reason": "A relação não está clara.",
                "discard_word_ids": [], "comment_word_ids": [], "keep_word_ids": []})):
            edits, diagnostics = ai_analysis._resolve_retake_edits(self.transcript, 200, "codex")
        self.assertEqual(edits, [])
        self.assertEqual(diagnostics["status"], "needs-review")

    def test_resolved_response_without_word_evidence_is_visible_for_review(self):
        response = {"status": "resolved", "reason": "retake", "discard_word_ids": [],
                    "comment_word_ids": [], "keep_word_ids": []}
        with patch("app.ai_providers.run_prompt", return_value=json.dumps(response)):
            edits, diagnostics = ai_analysis._resolve_retake_edits(self.transcript, 200, "codex")
        self.assertEqual(edits, [])
        self.assertEqual(diagnostics["items"][0]["reason"], "missing-retake-evidence")

    def test_normal_explanatory_repetition_does_not_create_a_warning(self):
        transcript = [segment("s0", 10, 10.8, "Repetindo o exemplo anterior."),
                      segment("s1", 11, 11.6, "Esse valor continua igual.")]
        response = {"status": "not_editorial", "reason": "continuação normal",
                    "discard_word_ids": [], "comment_word_ids": [], "keep_word_ids": []}
        with patch("app.ai_providers.run_prompt", return_value=json.dumps(response)):
            edits, diagnostics = ai_analysis._resolve_retake_edits(transcript, 20, "codex")
        self.assertEqual(edits, [])
        self.assertIsNone(diagnostics)

    def test_kept_restart_must_be_a_complete_segment(self):
        response = json.loads(self.resolved)
        response["keep_word_ids"] = [f"s2:w{i}" for i in range(6)]
        with patch("app.ai_providers.run_prompt", return_value=json.dumps(response)):
            edits, diagnostics = ai_analysis._resolve_retake_edits(self.transcript, 200, "codex")
        self.assertEqual(len(edits), 1)
        self.assertEqual(edits[0]["retake_evidence"]["keep"]["text"], self.transcript[2]["text"])
        self.assertIsNone(diagnostics)

    def test_resolver_rejects_unselected_speech_inside_removal_interval(self):
        transcript = [self.transcript[0], segment("aside", 154.25, 154.6, "Isso é importante."), *self.transcript[1:]]
        response = json.loads(self.resolved)
        response["discard_word_ids"] = [f"s0:w{i}" for i in range(10)]
        response["comment_word_ids"] = [f"s2:w{i}" for i in range(3)]
        response["keep_word_ids"] = [f"s3:w{i}" for i in range(5)]
        with patch("app.ai_providers.run_prompt", return_value=json.dumps(response)):
            edits, _ = ai_analysis._resolve_retake_edits(transcript, 200, "codex")
        self.assertEqual(edits, [])

    def test_unrelated_asr_anomaly_before_retake_is_not_sent_as_evidence(self):
        suspect = {"id": "bad", "start": 143.18, "end": 145.24,
                   "text": "E você vai ver que o GPT é a mesma coisa",
                   "words": [{"text": token, "start": 143.9, "end": 143.9}
                             for token in "E você vai ver que o GPT é a mesma coisa".split()]}
        transcript = [suspect, *self.transcript]
        response = json.loads(self.resolved)
        response["discard_word_ids"] = [f"s1:w{i}" for i in range(10)]
        response["comment_word_ids"] = [f"s2:w{i}" for i in range(3)]
        response["keep_word_ids"] = [f"s3:w{i}" for i in range(6)]
        with patch("app.ai_providers.run_prompt", return_value=json.dumps(response)) as run:
            edits, diagnostics = ai_analysis._resolve_retake_edits(transcript, 200, "codex")
        prompt = run.call_args.args[1]
        self.assertNotIn("E você vai ver que o GPT", prompt)
        self.assertEqual(len(edits), 1)
        self.assertEqual((edits[0]["start"], edits[0]["end"]), (147.28, 156.04))
        self.assertIsNone(diagnostics)

    def test_previous_decision_on_comment_alone_is_preserved_but_requires_review(self):
        candidate = {"id": "new-retake", "start": 147.28, "end": 156.04,
                     "decision": "pending", "retake_evidence": {
                         "comment": {"start": 154.78, "end": 156.04}}}
        prior = {"id": "old-comment", "start": 154.78, "end": 156.04,
                 "decision": "accepted", "kind": "semantic-removal"}
        result = ai_analysis.preserve_decisions([candidate], [prior])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["decision"], "pending")
        self.assertEqual(result[0]["previous_decision"]["decision"], "accepted")


if __name__ == "__main__":
    unittest.main()
