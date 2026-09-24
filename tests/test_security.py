import contextlib
import io
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import autoeditor
import auto_upload_yt
from preflight import check
from tools.check_secrets import scan_paths


class SecurityTests(unittest.TestCase):
    def test_upload_disabled_even_when_credentials_exist(self):
        environment = dict(YT_CLIENT_ID='fixture', YT_CLIENT_SECRET='fixture',
                           YT_REFRESH_TOKEN='fixture')
        output = io.StringIO()
        with patch.dict(os.environ, environment, clear=True), contextlib.redirect_stdout(output):
            auto_upload_yt.principal()
        self.assertIn('dezactivat', output.getvalue())
        self.assertNotIn('fixture', output.getvalue())

    def test_upload_opt_in_without_secrets_skips_safely(self):
        output = io.StringIO()
        with patch.dict(os.environ, {'YT_UPLOAD_ENABLED': 'true'}, clear=True), \
             contextlib.redirect_stdout(output):
            auto_upload_yt.principal()
        self.assertIn('skip', output.getvalue())

    def test_preflight_distinguishes_disabled_from_missing_credentials(self):
        environment = dict(GEMINI_API_KEY='fixture', GEMINI_MODEL='model')
        _, warnings = check(environment, '.')
        self.assertTrue(any('dezactivat explicit' in line for line in warnings))
        environment['YT_UPLOAD_ENABLED'] = 'true'
        _, warnings = check(environment, '.')
        self.assertTrue(any('lipsesc setari OAuth' in line for line in warnings))

    def test_guard_returns_only_path_and_label(self):
        # Artificial fixture generated at runtime, not a real credential.
        dummy = ''.join(['GO', 'CSPX', '-', 'a' * 24])
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'settings.txt'
            path.write_text('credential=' + dummy)
            findings = scan_paths([path])
            self.assertEqual(findings, [(str(path), 'oauth-client-secret')])
            self.assertNotIn(dummy, repr(findings))

    def test_guard_detects_refresh_token_fixture(self):
        dummy = ''.join(['1', '/', '/', 'a' * 40])
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'settings.txt'
            path.write_text(dummy)
            self.assertEqual(scan_paths([path]), [(str(path), 'google-refresh-token')])

    def test_legacy_sound_organizer_no_longer_mutates_originals(self):
        with patch('autoeditor.os.remove') as delete, patch('autoeditor.subprocess.run') as render:
            autoeditor.aranjeaza_sunete_mele()
        delete.assert_not_called()
        render.assert_not_called()

    def test_credential_exports_ignored_but_example_retained(self):
        root = Path(__file__).resolve().parents[1]
        names = ['.env', '.env.local', 'nested/.env.production', 'client_secret_new.json',
                 'cookies_yt_fresh.txt', 'cookies.b64', 'old_refresh_token.json',
                 'generated.ass', 'generated_upload.txt', '.env.example']
        result = subprocess.run(['git', 'check-ignore', '--no-index', '--stdin'],
                                input='\n'.join(names), text=True, capture_output=True, cwd=root)
        self.assertEqual(result.returncode, 0)
        ignored = set(result.stdout.splitlines())
        self.assertEqual(ignored, set(names[:-1]))


if __name__ == '__main__':
    unittest.main()
