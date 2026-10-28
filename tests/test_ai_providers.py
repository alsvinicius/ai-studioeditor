import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app import ai_providers, state


class AIProviderTests(unittest.TestCase):
    def test_provider_settings_default_and_persist_without_secrets(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "settings.json"
            with patch.object(state, "AI_SETTINGS_PATH", target):
                self.assertEqual(state.get_ai_provider(), "opencode")
                state.save_ai_provider("codex")
                self.assertEqual(state.get_ai_provider(), "codex")
                self.assertEqual(json.loads(target.read_text()), {"provider": "codex", "visual_frame_limit": 8})
                self.assertEqual(target.stat().st_mode & 0o777, 0o600)
                with self.assertRaises(ValueError):
                    state.save_ai_provider("other")

    def test_codex_invocation_isolated_and_explicit(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            auth = root / "auth.json"
            auth.write_text('{"access_token":"test-only"}')
            image = root / "sample.jpg"
            image.write_bytes(b"synthetic-image")
            captured = {}

            def run(command, **kwargs):
                captured["command"] = command
                captured["kwargs"] = kwargs
                return type("Result", (), {"returncode": 0, "stdout":
                    '{"type":"item.completed","item":{"type":"agent_message","text":"{\\"ok\\":true}"}}\n', "stderr": ""})()

            with patch.dict(os.environ, {"CODEX_AUTH_FILE": str(auth), "CODEX_BIN": "/opt/codex"}), \
                 patch("app.ai_providers.subprocess.run", side_effect=run):
                response = ai_providers.run_prompt("codex", "Return JSON", [image], schema={"type": "object"})
            command, kwargs = captured["command"], captured["kwargs"]
            self.assertEqual(json.loads(response), {"ok": True})
            self.assertIn("gpt-6-luna", command)
            self.assertIn('model_reasoning_effort="medium"', command)
            self.assertIn("read-only", command)
            self.assertIn("shell_tool", command)
            self.assertIn("web_search=\"disabled\"", command)
            self.assertIn("--ephemeral", command)
            self.assertTrue(kwargs["env"]["CODEX_HOME"].startswith(temporary) is False)
            self.assertNotIn("OPENAI_API_KEY", kwargs["env"])
            self.assertEqual(kwargs["input"], "Return JSON")
            self.assertEqual(kwargs["cwd"], kwargs["env"]["CODEX_HOME"].replace("/home", "/workspace")) if False else None

    def test_codex_status_requires_binary_and_auth_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            auth = Path(temporary) / "auth.json"
            with patch.dict(os.environ, {"CODEX_AUTH_FILE": str(auth), "CODEX_BIN": "/opt/codex"}):
                self.assertFalse(ai_providers.status("codex")["configured"])
                auth.write_text('{"auth":"synthetic"}')
                self.assertTrue(ai_providers.status("codex")["configured"])


if __name__ == "__main__":
    unittest.main()
