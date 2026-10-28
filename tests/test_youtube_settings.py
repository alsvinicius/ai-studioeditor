"""Global YouTube settings use isolated storage and never contact Google."""
import json
import stat
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from app import main, state


class YouTubeSettingsTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.projects = self.root / 'projects'
        self.projects.mkdir()
        self.patches = [
            patch.object(state, 'DATA_DIR', self.root),
            patch.object(state, 'PROJECTS_DIR', self.projects),
            patch.object(main, '_oauth_state', self.root / 'oauth-state.json'),
            patch.dict('os.environ', {'YOUTUBE_CLIENT_SECRETS': str(self.root / 'absent.json'), 'YOUTUBE_REDIRECT_URI': 'http://localhost:8000/api/youtube/callback'}),
        ]
        for item in self.patches:
            item.start()
        self.client = TestClient(main.app)
        self.credential = {'web': {
            'client_id': 'test-client.apps.googleusercontent.com',
            'client_secret': 'synthetic-test-secret',
            'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
            'token_uri': 'https://oauth2.googleapis.com/token',
            'redirect_uris': ['http://localhost:8000/api/youtube/callback'],
        }}

    def tearDown(self):
        self.client.close()
        for item in reversed(self.patches):
            item.stop()
        self.directory.cleanup()

    def test_global_settings_without_project_and_private_storage(self):
        self.assertEqual(self.client.get('/settings').status_code, 200)
        self.assertFalse(self.client.get('/api/settings/youtube').json()['configured'])
        result = self.client.put('/api/settings/youtube/client', json=self.credential)
        self.assertEqual(result.status_code, 200)
        self.assertTrue(result.json()['configured'])
        self.assertNotIn('synthetic-test-secret', result.text)
        self.assertNotIn('client_id', result.text)
        path = self.root / 'youtube-client-secret.json'
        self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
        self.assertEqual(main._oauth_secrets(), path)
        self.assertEqual(json.loads(path.read_text()), self.credential)

    def test_invalid_credentials_preserve_existing_config(self):
        self.client.put('/api/settings/youtube/client', json=self.credential)
        path = main._oauth_secrets()
        before = path.read_bytes()
        for body in [b'not-json', b'\xff', b'[]', b'{"installed":{}}']:
            self.assertEqual(self.client.put('/api/settings/youtube/client', content=body).status_code, 422)
        wrong = json.loads(json.dumps(self.credential))
        wrong['web']['redirect_uris'] = []
        self.assertEqual(self.client.put('/api/settings/youtube/client', json=wrong).status_code, 422)
        wrong['web']['redirect_uris'] = self.credential['web']['redirect_uris'][0]
        self.assertEqual(self.client.put('/api/settings/youtube/client', json=wrong).status_code, 422)
        wrong['web']['redirect_uris'] = self.credential['web']['redirect_uris']
        wrong['web']['token_uri'] = 'https://example.com/token'
        self.assertEqual(self.client.put('/api/settings/youtube/client', json=wrong).status_code, 422)
        self.assertEqual(self.client.put('/api/settings/youtube/client', content=b'x' * 65537).status_code, 413)
        self.assertEqual(path.read_bytes(), before)

    def test_connection_is_global_and_can_be_disconnected(self):
        main._token().write_text('synthetic-token')
        main._oauth_state.write_text('{}')
        self.assertTrue(self.client.get('/api/settings/youtube').json()['connected'])
        response = self.client.delete('/api/settings/youtube/connection')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['connected'])
        self.assertFalse(main._token().exists())
        self.assertFalse(main._oauth_state.exists())

    def test_credential_replacement_clears_previous_authorization(self):
        main._token().write_text('synthetic-token')
        main._oauth_state.write_text('{}')
        self.assertEqual(self.client.put('/api/settings/youtube/client', json=self.credential).status_code, 200)
        self.assertFalse(main._token().exists())
        self.assertFalse(main._oauth_state.exists())

    def test_active_upload_blocks_connection_changes(self):
        project = state.create_project('sample.mp4', self.root / 'sample.mp4', {'duration': 10})
        project['status'] = 'uploading'
        state.save(project)
        main._token().write_text('synthetic-token')
        self.assertEqual(self.client.delete('/api/settings/youtube/connection').status_code, 409)
        self.assertEqual(self.client.put('/api/settings/youtube/client', json=self.credential).status_code, 409)
        self.assertTrue(main._token().exists())


if __name__ == '__main__':
    unittest.main()
