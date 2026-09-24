import contextlib
import io
import json
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import Mock, patch

import oauth_setup as setup


def fixture_client():
    return {'installed': {'client_id': 'fixture.apps.googleusercontent.com',
                          'client_secret': 'fixture-only-secret',
                          'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
                          'token_uri': 'https://oauth2.googleapis.com/token'}}


class OAuthSetupTests(unittest.TestCase):
    def test_desktop_client_with_official_endpoints(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'fixture.json'
            path.write_text(json.dumps(fixture_client()))
            self.assertEqual(setup.load_client(path), fixture_client())

    def test_external_token_endpoint_rejected(self):
        configuration = fixture_client()
        configuration['installed']['token_uri'] = 'https://example.test/collect'
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'fixture.json'
            path.write_text(json.dumps(configuration))
            with self.assertRaises(setup.SetupError):
                setup.load_client(path)

    def test_web_client_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'fixture.json'
            path.write_text(json.dumps({'web': fixture_client()['installed']}))
            with self.assertRaises(setup.SetupError):
                setup.load_client(path)

    def test_secret_is_sent_over_stdin_not_argv(self):
        token = 'fixture-refresh-value'
        with patch('oauth_setup.subprocess.run', return_value=Mock(returncode=0, stdout='')) as run:
            setup.gh_call(['secret', 'set', 'YT_REFRESH_TOKEN', '--repo', 'owner/repo'], token)
        self.assertEqual(run.call_args.kwargs['input'], token)
        self.assertNotIn(token, ' '.join(run.call_args.args[0]))
        self.assertTrue(run.call_args.kwargs['capture_output'])

    def test_upload_enabled_only_after_all_three_secrets(self):
        with patch('oauth_setup.gh_call') as gh:
            setup.store_secrets('owner/repo', fixture_client(), 'fixture-refresh-value', True)
        calls = gh.call_args_list
        self.assertEqual(calls[0].args[0][-1], 'false')
        self.assertEqual([c.args[0][2] for c in calls[1:4]],
                         ['YT_CLIENT_ID', 'YT_CLIENT_SECRET', 'YT_REFRESH_TOKEN'])
        self.assertEqual(calls[-1].args[0][-1], 'true')
        for call in calls:
            self.assertNotIn('fixture-refresh-value', ' '.join(call.args[0]))

    def test_partial_save_does_not_enable_upload(self):
        with patch('oauth_setup.gh_call', side_effect=[None, None, setup.SetupError('refused')]) as gh:
            with self.assertRaises(setup.SetupError):
                setup.store_secrets('owner/repo', fixture_client(), 'fixture-refresh-value', True)
        self.assertFalse(any(call.args[0][-1] == 'true' for call in gh.call_args_list))

    def test_no_refresh_token_no_github_changes(self):
        with patch('oauth_setup.gh_call') as gh:
            with self.assertRaises(setup.SetupError):
                setup.store_secrets('owner/repo', fixture_client(), None, True)
        gh.assert_not_called()

    def test_oauth_uses_pkce_and_loopback_with_timeout(self):
        flow = Mock()
        installed = Mock()
        installed.from_client_config.return_value = flow
        fake_module = types.ModuleType('google_auth_oauthlib.flow')
        fake_module.InstalledAppFlow = installed
        with patch.dict('sys.modules', {'google_auth_oauthlib.flow': fake_module}):
            setup.authorize(fixture_client())
        self.assertTrue(installed.from_client_config.call_args.kwargs['autogenerate_code_verifier'])
        options = flow.run_local_server.call_args.kwargs
        self.assertEqual(options['host'], '127.0.0.1')
        self.assertEqual(options['port'], 0)
        self.assertEqual(options['timeout_seconds'], 300)
        self.assertEqual(options['access_type'], 'offline')

    def test_failure_messages_never_echo_provider_secrets(self):
        output = io.StringIO()
        with patch.dict('os.environ', {'GITHUB_ACTIONS': 'false'}), \
             patch('oauth_setup.load_client', side_effect=RuntimeError('fixture-confidential')), \
             contextlib.redirect_stderr(output):
            self.assertEqual(setup.main(['auth']), 1)
        self.assertNotIn('fixture-confidential', output.getvalue())

    def test_declining_channel_confirmation_leaves_github_untouched(self):
        credentials = types.SimpleNamespace(token='fixture-access', refresh_token='fixture-refresh')
        with patch.dict('os.environ', {'GITHUB_ACTIONS': 'false'}), \
             patch('oauth_setup.load_client', return_value=fixture_client()), \
             patch('oauth_setup.check_github'), patch('oauth_setup.authorize', return_value=credentials), \
             patch('oauth_setup.channel_info', return_value=('channel-fixture', 'Canal test')), \
             patch('builtins.input', return_value='NU'), patch('oauth_setup.store_secrets') as store, \
             contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(setup.main(['auth']), 1)
        store.assert_not_called()


if __name__ == '__main__':
    unittest.main()
