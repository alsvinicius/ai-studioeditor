import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from app import ai_providers, main, media, mimo_vision, state


class VisualPolicyTests(unittest.TestCase):
    def test_empty_transcript_is_partial_and_does_not_invoke_semantic_model(self):
        project = state.create_project("video.mp4", self.root / "video.mp4", {"duration": 10, "width": 1920, "height": 1080})
        project.update({"status": "analyzing", "analysis_run": {"status": "running", "capabilities": {
            "semantic": {"status": "pending"}, "visual": {"status": "skipped"}, "audio": {"status": "pending"}}}})
        state.save(project)
        with patch("app.visual.analyze_video", return_value={"status": "complete"}), \
             patch("app.media.transcribe", return_value=[]), patch("app.media.detect_silence", return_value=[]), \
             patch("app.ai_analysis.analyze_transcript") as semantic:
            main._analysis_job(project["id"], "medium", False, "pt", "opencode")
        saved = state.load(project["id"])
        self.assertEqual(saved["analysis_run"]["status"], "partial")
        self.assertEqual(saved["analysis_run"]["provider_result"]["error"], "empty-transcript")
        semantic.assert_not_called()

    def test_restart_marks_orphaned_jobs_without_losing_review(self):
        project = state.create_project("video.mp4", self.root / "video.mp4", {"duration": 10})
        project.update({"status": "analyzing", "job": {"stage": "semantic-analysis"},
            "transcript": [{"id": "s0", "start": 0, "end": 2, "text": "fala corrigida"}],
            "edits": [{"id": "e1", "start": 0, "end": 1, "decision": "accepted"}],
            "analysis_run": {"status": "running", "capabilities": {"semantic": {"status": "running"}}}})
        state.save(project)
        with TestClient(main.app):
            pass
        saved = state.load(project["id"])
        self.assertEqual(saved["status"], "review-ready")
        self.assertEqual(saved["transcript"], project["transcript"])
        self.assertEqual(saved["edits"], project["edits"])
        self.assertEqual(saved["analysis_run"]["capabilities"]["semantic"]["status"], "failed")

    def test_restart_marks_uncertain_upload_and_requires_confirmation(self):
        project = state.create_project("video.mp4", self.root / "video.mp4", {"duration": 10})
        project.update({"status": "uploading", "exports": [{"id": "master", "type": "master", "filename": "master.mp4", "upload_status": "uploading"}]})
        state.save(project)
        state.recover_interrupted_jobs()
        saved = state.load(project["id"])
        self.assertEqual(saved["status"], "upload-failed")
        self.assertEqual(saved["exports"][0]["upload_status"], "uploading-unknown")
        route = f"/api/projects/{project['id']}/youtube/retry-video"
        self.assertEqual(self.client.post(route, json={"asset_id": "master"}).status_code, 409)
        response = self.client.post(route, json={"asset_id": "master", "confirmed_absent": True})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["exports"][0]["upload_status"], "not-uploaded")

    def test_failed_semantic_provider_marks_analysis_partial(self):
        project = state.create_project("video.mp4", self.root / "video.mp4", {"duration": 10, "width": 1920, "height": 1080})
        project.update({"status": "analyzing", "analysis_run": {"status": "running", "capabilities": {
            "semantic": {"status": "pending"}, "visual": {"status": "skipped"}, "audio": {"status": "pending"}}}})
        state.save(project)
        transcript = [{"start": 0, "end": 2, "text": "fala válida", "id": "s0"}]
        with patch("app.visual.analyze_video", return_value={"status": "complete"}), \
             patch("app.media.transcribe", return_value=transcript), patch("app.media.detect_silence", return_value=[]), \
             patch("app.ai_analysis.analyze_transcript", return_value=([], [], {"opencode": {"status": "unavailable"}})):
            main._analysis_job(project["id"], "medium", False, "pt", "opencode")
        saved = state.load(project["id"])
        self.assertEqual(saved["analysis_run"]["status"], "partial")
        self.assertEqual(saved["analysis_run"]["capabilities"]["semantic"]["status"], "unavailable")
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.projects = self.root / "projects"
        self.projects.mkdir()
        self.patches = [patch.object(state, "DATA_DIR", self.root), patch.object(state, "PROJECTS_DIR", self.projects), patch.object(state, "AI_SETTINGS_PATH", self.root / "ai-settings.json")]
        for item in self.patches:
            item.start()
        self.client = TestClient(main.app)

    def tearDown(self):
        self.client.close()
        for item in reversed(self.patches):
            item.stop()
        self.directory.cleanup()

    def test_failed_semantic_retry_preserves_prior_results(self):
        project = state.create_project("video.mp4", self.root / "video.mp4", {"duration": 10})
        project.update({"status": "analyzing", "analysis_generation": 2,
            "analysis_run": {"capabilities": {"semantic": {"status": "running"}}},
            "transcript": [{"start": 0, "end": 2, "text": "Olá"}],
            "edits": [{"id": "edit-1", "start": 0, "end": 1, "decision": "accepted", "source": "opencode"}],
            "shorts": [], "youtube_cuts": [{"id": "cut-1", "start": 2, "end": 8, "decision": "accepted"}]})
        state.save(project)
        with patch("app.ai_analysis.analyze_transcript", return_value=([], [], {"opencode": {"status": "unavailable"}})):
            main._retry_analysis_job(project["id"], "semantic", "opencode", 2)
        saved = state.load(project["id"])
        self.assertEqual(saved["edits"], project["edits"])
        self.assertEqual(saved["youtube_cuts"], project["youtube_cuts"])
        self.assertEqual(saved["analysis_run"]["capabilities"]["semantic"]["status"], "failed")

    def test_successful_semantic_retry_updates_latest_provider_and_generation(self):
        project = state.create_project("video.mp4", self.root / "video.mp4", {"duration": 10})
        project.update({"status": "analyzing", "analysis_generation": 2,
            "analysis_run": {"generation": 1, "status": "running", "capabilities": {
                "semantic": {"status": "running"}, "visual": {"status": "complete"}, "audio": {"status": "complete"}}},
            "transcript": [{"start": 0, "end": 2, "text": "Olá"}], "edits": [], "shorts": [], "youtube_cuts": []})
        state.save(project)
        provider_result = {"status": "complete", "provider": "opencode", "model": "model-x"}
        with patch("app.ai_analysis.analyze_transcript", return_value=([], [], {"opencode": provider_result})):
            main._retry_analysis_job(project["id"], "semantic", "opencode", 2)
        saved = state.load(project["id"])
        self.assertEqual(saved["analysis_run"]["generation"], 2)
        self.assertEqual(saved["analysis_run"]["provider_result"], provider_result)
        self.assertEqual(saved["analysis_run"]["status"], "complete")
        self.assertEqual(saved["job"]["stage"], "complete")


    def test_visual_retry_blocks_replacing_reviewed_color_scenes(self):
        project = state.create_project("video.mp4", self.root / "video.mp4", {"duration": 10})
        project.update({"status": "review-ready", "color_grade": {"segments": {"scene-1": {"enabled": True, "intensity": 0.5}}}})
        state.save(project)
        response = self.client.post(f"/api/projects/{project['id']}/analysis/retry", json={"capability": "visual"})
        self.assertEqual(response.status_code, 409)
        self.assertEqual(state.load(project["id"])["color_grade"], project["color_grade"])

    def test_ai_settings_report_selected_model_and_auth_readiness(self):
        configured = {**ai_providers.PROVIDERS["opencode"], "configured": True, "binary_available": True, "auth_available": True}
        with patch("app.ai_providers.status", return_value=configured):
            response = self.client.get("/api/settings/ai")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["configured"])
        self.assertEqual(response.json()["provider"], "opencode")
        self.assertEqual(response.json()["model"], "opencode/mimo-v2.6-flash-free")

    def test_ai_provider_can_be_selected_and_persisted_without_exposing_auth(self):
        def status(provider):
            return {**ai_providers.PROVIDERS[provider], "configured": provider == "codex",
                    "binary_available": True, "auth_available": True}
        with patch("app.ai_providers.status", side_effect=status):
            response = self.client.put("/api/settings/ai", json={"provider": "codex"})
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["provider"], "codex")
            self.assertEqual(data["model"], "gpt-6-luna")
            self.assertEqual(data["effort"], "medium")
            self.assertTrue(data["configured"])
            self.assertNotIn("access_token", json.dumps(data).lower())
            self.assertNotIn("auth.json", json.dumps(data).lower())
            self.assertEqual(self.client.get("/api/settings/ai").json()["provider"], "codex")
            self.assertEqual(self.client.put("/api/settings/ai", json={"provider": "invalid"}).status_code, 422)

    def test_review_rejects_global_grade_for_presentation(self):
        project = state.create_project("slide.mp4", self.root / "slide.mp4", {"duration": 10})
        project["status"] = "review-ready"
        project["visual_analysis"] = {"status": "complete", "grade_policy": {"mode": "preserve"}}
        state.save(project)
        response = self.client.put(f"/api/projects/{project['id']}/review", json={"visual": {"grade_enabled": True, "intensity": 1}})
        self.assertEqual(response.status_code, 422)
        self.assertIn("preservar cores", response.text)

    def test_review_accepts_grade_only_for_verified_camera_scene(self):
        project = state.create_project("scene.mp4", self.root / "scene.mp4", {"duration": 10})
        project["status"] = "review-ready"
        project["visual_analysis"] = {"status": "complete", "grade_segments": [
            {"id": "cam", "start": 0, "end": 5, "layout": "camera", "status": "reviewable"},
            {"id": "slides", "start": 5, "end": 10, "layout": "slides", "status": "preserve"},
        ]}
        state.save(project)
        response = self.client.put(f"/api/projects/{project['id']}/review", json={"visual": {"grade_segments": [
            {"id": "cam", "enabled": True, "intensity": 0.5},
            {"id": "slides", "enabled": True, "intensity": 1},
        ]}})
        self.assertEqual(response.status_code, 422)
        response = self.client.put(f"/api/projects/{project['id']}/review", json={"visual": {"grade_segments": [
            {"id": "cam", "enabled": True, "intensity": 0.5},
            {"id": "slides", "enabled": False, "intensity": 1},
        ]}})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["color_grade"]["segments"]["cam"], {"enabled": True, "intensity": 0.5})
        self.assertFalse(response.json()["color_grade"]["segments"]["slides"]["enabled"])

    def test_legacy_incomplete_visual_review_preserves_saved_decisions_and_blocks_grade(self):
        project = state.create_project("legacy.mp4", self.root / "legacy.mp4", {"duration": 10, "width": 1920, "height": 1080})
        project.update({"status": "review-ready", "visual_analysis": {"status": "complete",
            "scene_review": {"status": "complete", "sample_count": 8, "frames": [{"time": 1, "layout": "camera"}]},
            "grade_segments": [{"id": "cam", "start": 0, "end": 10, "layout": "camera", "status": "reviewable", "suggestion": {"brightness": .05}}]},
            "color_grade": {"segments": {"cam": {"enabled": True, "intensity": 1}}}})
        state.save(project)
        self.assertTrue(self.client.get(f"/api/projects/{project['id']}").json()["visual_legacy_incomplete"])
        response = self.client.put(f"/api/projects/{project['id']}/review", json={"visual": {"grade_segments": [{"id": "cam", "enabled": True}]}})
        self.assertEqual(response.status_code, 422)
        self.assertEqual(self.client.put(f"/api/projects/{project['id']}/review", json={}).status_code, 200)
        self.assertTrue(state.load(project["id"])["color_grade"]["segments"]["cam"]["enabled"])
        calls = []
        with patch.object(media.subprocess, "run", side_effect=lambda args, **kwargs: calls.append(args) or type("Result", (), {"returncode": 0, "stderr": ""})()):
            media.render_video(project, self.root / "legacy-out.mp4")
        graph = calls[-1][calls[-1].index("-filter_complex") + 1]
        self.assertNotIn("eq=", graph)

    def test_horizontal_cut_acceptance_requires_conflict_resolution(self):
        project = state.create_project("cuts.mp4", self.root / "cuts.mp4", {"duration": 20})
        project.update({"status": "review-ready", "edits": [{"id": "edit-1", "start": 5, "end": 6, "decision": "pending"}],
                        "youtube_cuts": [{"id": "cut-1", "start": 0, "end": 10, "decision": "pending"}]})
        state.save(project)
        response = self.client.put(f"/api/projects/{project['id']}/review", json={"youtube_cuts": [{"id": "cut-1", "decision": "accepted"}]})
        self.assertEqual(response.status_code, 422)
        response = self.client.put(f"/api/projects/{project['id']}/review", json={"edits": [{"id": "edit-1", "decision": "rejected"}], "youtube_cuts": [{"id": "cut-1", "decision": "accepted"}]})
        self.assertEqual(response.status_code, 200)

    def test_audio_retry_does_not_require_an_ai_provider(self):
        project = state.create_project("audio.mp4", self.root / "audio.mp4", {"duration": 10})
        project.update({"status": "review-ready", "transcript": [{"id": "s1", "start": 0, "end": 8, "text": "muito obrigado"}],
                        "analysis_run": {"generation": 1, "status": "partial", "capabilities": {"audio": {"status": "failed"}}}})
        state.save(project)
        with patch("app.ai_providers.status", return_value={"configured": False}), patch("app.main.threading.Thread") as worker:
            response = self.client.post(f"/api/projects/{project['id']}/analysis/retry", json={"capability": "audio"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(worker.call_args.kwargs["args"][1], "audio")

    def test_ai_analysis_requires_selected_provider_for_text_and_optional_image(self):
        project = state.create_project("slide.mp4", self.root / "slide.mp4", {"duration": 10})
        with patch("app.ai_providers.status", return_value={"configured": False, "model": "x", "effort": None}):
            response = self.client.post(f"/api/projects/{project['id']}/analyze", json={"model": "tiny", "visual_review": False})
        self.assertEqual(response.status_code, 422)
        self.assertIn("provedor selecionado", response.text)
        self.assertEqual(state.load(project["id"])["status"], "imported")

    def test_configured_provider_defaults_image_review_on_and_can_be_switched_off(self):
        project = state.create_project("slide.mp4", self.root / "slide.mp4", {"duration": 10})
        with patch("app.ai_providers.status", return_value={"configured": True, "model": ai_providers.PROVIDERS["opencode"]["model"], "effort": None}), patch("app.main.threading.Thread") as worker:
            response = self.client.post(f"/api/projects/{project['id']}/analyze", json={"model": "tiny"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(worker.call_args.kwargs["args"][2])
        self.assertEqual(len(worker.call_args.kwargs["args"]), 6)
        self.assertEqual(worker.call_args.kwargs["args"][4], "opencode")
        self.assertEqual(worker.call_args.kwargs["args"][5], 8)
        self.assertEqual(response.json()["ai_model"], "opencode/mimo-v2.6-flash-free")

        second = state.create_project("slides-2.mp4", self.root / "slides-2.mp4", {"duration": 10})
        with patch("app.ai_providers.status", return_value={"configured": True, "model": ai_providers.PROVIDERS["opencode"]["model"], "effort": None}), patch("app.main.threading.Thread") as worker:
            response = self.client.post(f"/api/projects/{second['id']}/analyze", json={"model": "tiny", "visual_review": False})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(worker.call_args.kwargs["args"][2])

    def test_scene_sampling_caps_at_eight_and_spreads_transitions(self):
        stderr = "".join(f"pts_time:{n * 4}.000" for n in range(1, 31))
        result = type("Result", (), {"stderr": stderr, "returncode": 0})()
        with patch("app.mimo_vision.subprocess.run", return_value=result):
            times = mimo_vision.select_sample_times(Path("synthetic.mp4"), 120)
        self.assertLessEqual(len(times), 8)
        self.assertEqual(times, sorted(times))
        self.assertGreater(times[-1] - times[0], 90)

    def test_scene_transitions_compare_every_decoded_frame(self):
        result = type("Result", (), {"stderr": "pts_time:5.000", "returncode": 0})()
        with patch("app.mimo_vision.subprocess.run", return_value=result) as runner:
            times = mimo_vision._scene_transitions(Path("synthetic.mp4"), 10)
        self.assertEqual(times, [5.0])
        self.assertIn(r"select=gt(scene\,0.3),showinfo", runner.call_args.args[0])

    def test_opencode_review_attaches_only_eight_reduced_frames(self):
        import numpy as np
        import cv2

        class Capture:
            def __init__(self, _path): self.index = 0
            def isOpened(self): return True
            def set(self, *_args): return True
            def read(self): self.index += 1; return True, np.zeros((900, 1600, 3), dtype=np.uint8)
            def release(self): pass

        captured = []
        response = json.dumps({"frames": [{"index": i, "layout": "camera" if i == 1 else "slides", "confidence": "high", "reason": "fixture"} for i in range(1, 9)]})
        with patch.object(cv2, "VideoCapture", Capture), patch("app.ai_providers.run_prompt", side_effect=lambda provider, prompt, files, **kwargs: captured.extend((prompt, files)) or response), patch("app.mimo_vision._scene_transitions", return_value=[]):
            result = mimo_vision.review_scenes(Path("synthetic.mp4"), 70)
        self.assertEqual(len(captured[1]), 1)
        self.assertTrue(all(path.suffix == ".jpg" for path in captured[1]))
        self.assertEqual(result["model"], "opencode/mimo-v2.6-flash-free")
        self.assertEqual([frame["layout"] for frame in result["frames"]][0], "camera")
        self.assertEqual([frame["layout"] for frame in result["frames"]][-1], "slides")
        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["classified_count"], 8)

    def test_missing_or_duplicate_frame_classifications_remain_unknown(self):
        import cv2
        import numpy as np
        class Capture:
            def __init__(self, _path): pass
            def isOpened(self): return True
            def set(self, *_args): return True
            def read(self): return True, np.zeros((108, 192, 3), dtype=np.uint8)
            def release(self): pass
        response = json.dumps({"frames": [
            {"index": 1, "layout": "camera", "confidence": "high", "reason": "ok"},
            {"index": 2, "layout": "camera", "confidence": "high", "reason": "duplicate"},
            {"index": 2, "layout": "slides", "confidence": "high", "reason": "conflict"},
        ]})
        with patch.object(cv2, "VideoCapture", Capture), patch("app.ai_providers.run_prompt", return_value=response), patch("app.mimo_vision._scene_transitions", return_value=[]):
            result = mimo_vision.review_scenes(Path("synthetic.mp4"), 20, max_frames=3)
        self.assertEqual(result["status"], "partial")
        self.assertEqual(result["classified_count"], 1)
        self.assertEqual([frame["layout"] for frame in result["frames"]], ["camera", "unknown", "unknown"])
        self.assertTrue(any(scene["layout"] == "unknown" for scene in result["scene_segments"]))

    def test_unreadable_sample_stays_unknown_and_is_not_charged_as_sent(self):
        import cv2
        import numpy as np
        class Capture:
            def __init__(self, _path): self.index = 0
            def isOpened(self): return True
            def set(self, *_args): return True
            def read(self):
                self.index += 1
                return (False, None) if self.index == 2 else (True, np.zeros((108, 192, 3), dtype=np.uint8))
            def release(self): pass
        response = json.dumps({"frames": [{"index": i, "layout": "camera", "confidence": "high", "reason": "ok"} for i in (1, 2)]})
        with patch.object(cv2, "VideoCapture", Capture), patch("app.ai_providers.run_prompt", return_value=response), patch("app.mimo_vision._scene_transitions", return_value=[]):
            result = mimo_vision.review_scenes(Path("synthetic.mp4"), 20, max_frames=3)
        self.assertEqual(result["status"], "partial")
        self.assertEqual((result["sample_count"], result["classified_count"], result["requested_sample_count"]), (2, 2, 3))
        self.assertEqual([frame["layout"] for frame in result["frames"]], ["camera", "unknown", "camera"])

    def test_single_visual_sample_does_not_cover_an_entire_long_scene(self):
        import cv2
        import numpy as np
        class Capture:
            def __init__(self, _path): pass
            def isOpened(self): return True
            def set(self, *_args): return True
            def read(self): return True, np.zeros((108, 192, 3), dtype=np.uint8)
            def release(self): pass
        response = json.dumps({"frames": [{"index": 1, "layout": "camera", "confidence": "high", "reason": "ok"}]})
        with patch.object(cv2, "VideoCapture", Capture), patch("app.ai_providers.run_prompt", return_value=response), patch("app.mimo_vision._scene_transitions", return_value=[]):
            result = mimo_vision.review_scenes(Path("synthetic.mp4"), 50, max_frames=1)
        self.assertEqual([scene["layout"] for scene in result["scene_segments"]], ["unknown", "camera", "unknown"])

    def test_renderer_does_not_apply_grade_when_policy_is_preserve(self):
        calls = []
        project = {
            "source": str(self.root / "source.mp4"), "metadata": {"duration": 5}, "edits": [],
            "color_grade": {"enabled": True, "intensity": 1},
            "visual_analysis": {"grade_policy": {"mode": "preserve"}, "grade_suggestion": {"brightness": 0.05, "contrast": 1.08, "saturation": 1.08}},
        }
        with patch.object(media.subprocess, "run", side_effect=lambda args, **kwargs: calls.append(args) or type("Result", (), {"returncode": 0, "stderr": ""})()):
            media.render_video(project, self.root / "out.mp4")
        self.assertTrue(calls)
        self.assertNotIn("eq=", calls[-1][calls[-1].index("-filter_complex") + 1])

    def test_renderer_grades_only_approved_camera_interval(self):
        calls = []
        project = {
            "source": str(self.root / "source.mp4"), "metadata": {"duration": 10}, "edits": [],
            "visual_analysis": {"grade_segments": [
                {"id": "cam", "start": 0, "end": 5, "layout": "camera", "status": "reviewable", "suggestion": {"brightness": 0.02, "contrast": 1.02, "saturation": 1}},
                {"id": "slides", "start": 5, "end": 10, "layout": "slides", "suggestion": {"brightness": 0, "contrast": 1, "saturation": 1}},
            ]},
            "color_grade": {"segments": {"cam": {"enabled": True, "intensity": 1}, "slides": {"enabled": False, "intensity": 1}}},
        }
        with patch.object(media.subprocess, "run", side_effect=lambda args, **kwargs: calls.append(args) or type("Result", (), {"returncode": 0, "stderr": ""})()):
            media.render_video(project, self.root / "scene-out.mp4")
        filter_graph = calls[-1][calls[-1].index("-filter_complex") + 1]
        self.assertEqual(filter_graph.count("eq="), 1)
        self.assertIn("eq=brightness=0.0200", filter_graph)
        self.assertIn("concat=n=2", filter_graph)

    def test_renderer_keeps_short_scene_boundary_and_rejects_uncertain_camera(self):
        calls = []
        project = {"source": str(self.root / "source.mp4"), "metadata": {"duration": 2}, "edits": [],
            "visual_analysis": {"grade_segments": [
                {"id": "uncertain", "start": 0, "end": 0.1, "layout": "camera", "status": "preserve", "suggestion": {"brightness": .05}},
                {"id": "camera", "start": .1, "end": 2, "layout": "camera", "status": "reviewable", "suggestion": {"brightness": .02}}]},
            "color_grade": {"segments": {"uncertain": {"enabled": True, "intensity": 1}, "camera": {"enabled": True, "intensity": 1}}}}
        with patch.object(media.subprocess, "run", side_effect=lambda args, **kwargs: calls.append(args) or type("Result", (), {"returncode": 0, "stderr": ""})()):
            media.render_video(project, self.root / "out.mp4")
        graph = calls[-1][calls[-1].index("-filter_complex") + 1]
        self.assertIn("atrim=start=0.000:end=0.100", graph)
        self.assertIn("concat=n=2", graph)
        self.assertEqual(graph.count("eq="), 1)
        self.assertIn("eq=brightness=0.0200", graph)

    def test_preserved_scene_boundaries_do_not_fragment_export(self):
        calls = []
        project = {"source": str(self.root / "source.mp4"), "metadata": {"duration": 2}, "edits": [],
            "visual_analysis": {"grade_segments": [
                {"id": "a", "start": 0, "end": .1, "layout": "camera", "status": "preserve"},
                {"id": "b", "start": .1, "end": 2, "layout": "slides", "status": "preserve"}]},
            "color_grade": {"segments": {"a": {"enabled": True}}}}
        with patch.object(media.subprocess, "run", side_effect=lambda args, **kwargs: calls.append(args) or type("Result", (), {"returncode": 0, "stderr": ""})()):
            media.render_video(project, self.root / "out.mp4")
        graph = calls[-1][calls[-1].index("-filter_complex") + 1]
        self.assertIn("concat=n=1", graph)
        self.assertNotIn("eq=", graph)


if __name__ == "__main__":
    unittest.main()
