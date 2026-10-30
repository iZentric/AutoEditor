import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import autoeditor
import idei_ai
import performance
from editorial import sound_catalogue, validate_sounds, public_catalogue
from preflight import check
from test_editorial import good_review, idea


class CacheTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.environment = patch.dict(os.environ, {
            'AE_CACHE_DIR': str(self.root / 'cache'), 'AE_CACHE': '1',
            'AE_REANALYZE': '0', 'AE_PERFORMANCE_REPORT': ''})
        self.environment.start()
        self.compute = Mock(return_value=[1, 2, 3])

    def tearDown(self):
        self.environment.stop()
        self.directory.cleanup()

    def cached(self, identity=None, **kwargs):
        return performance.cached_json('test', identity or {'model': 'small'},
                                       self.compute, lambda value: isinstance(value, list), **kwargs)

    def test_same_inputs_compute_once(self):
        self.assertEqual(self.cached(), self.cached())
        self.compute.assert_called_once()

    def test_settings_change_is_a_miss(self):
        self.cached({'model': 'base'})
        self.cached({'model': 'small'})
        self.assertEqual(self.compute.call_count, 2)

    def test_corrupt_cache_recomputes(self):
        self.cached()
        path = next((self.root / 'cache').rglob('*.json'))
        path.write_text('{partial')
        self.assertEqual(self.cached(), [1, 2, 3])
        self.assertEqual(self.compute.call_count, 2)

    def test_invalid_values_not_saved(self):
        self.compute.return_value = None
        self.cached()
        self.cached()
        self.assertEqual(self.compute.call_count, 2)
        self.assertEqual(list((self.root / 'cache').rglob('*.json')), [])

    def test_exceptions_not_saved(self):
        self.compute.side_effect = RuntimeError('outage')
        for _ in range(2):
            with self.assertRaises(RuntimeError):
                self.cached()
        self.assertEqual(self.compute.call_count, 2)

    def test_expired_ai_review_recomputes(self):
        with patch('performance.time.time', return_value=100):
            self.cached(ttl=60)
        with patch('performance.time.time', return_value=200):
            self.cached(ttl=60)
        self.assertEqual(self.compute.call_count, 2)

    def test_explicit_refresh_and_disabled_cache(self):
        self.cached()
        with patch.dict(os.environ, {'AE_REANALYZE': '1'}):
            self.cached()
        with patch.dict(os.environ, {'AE_CACHE': '0'}):
            self.cached()
        self.assertEqual(self.compute.call_count, 3)

    def test_same_name_different_bytes_invalidates_source(self):
        path = self.root / 'source.fixture'
        path.write_bytes(b'first')
        first = performance.file_digest(path)
        path.write_bytes(b'other')
        self.assertNotEqual(first, performance.file_digest(path))

    def test_passed_source_fingerprint_is_not_rehashed_for_each_review(self):
        with patch('subprocess.run'), \
             patch('idei_ai.file_digest') as digest, \
             patch('idei_ai.ia_gemini_video', return_value=good_review()):
            idei_ai.verifica_idee_cu_video('fake', 'key', 'model', 'fixture', idea(),
                                         source_fingerprint='already-hashed-immutable-vod')
        digest.assert_not_called()

    def test_failure_writing_cache_does_not_fail_valid_result(self):
        with patch('performance.atomic_json', side_effect=OSError('read only')):
            self.assertEqual(self.cached(), [1, 2, 3])

    def test_cached_review_skips_proxy_render_and_api_call(self):
        source = self.root / 'source.fixture'
        source.write_bytes(b'not real media; subprocess is mocked')
        with patch('subprocess.run') as render, \
             patch('idei_ai.ia_gemini_video', return_value=good_review()) as api:
            first = idei_ai.verifica_idee_cu_video('fake', 'key', 'model', str(source), idea())
            second = idei_ai.verifica_idee_cu_video('fake', 'key', 'model', str(source), idea())
        self.assertEqual(first, second)
        render.assert_called_once()
        api.assert_called_once()

    def test_review_rejection_not_cached(self):
        source = self.root / 'source.fixture'
        source.write_bytes(b'fixture')
        with patch('subprocess.run'), \
             patch('idei_ai.ia_gemini_video', return_value=good_review(un_joc=False)) as api:
            for _ in range(2):
                idei_ai.verifica_idee_cu_video('fake', 'key', 'model', str(source), idea())
        self.assertEqual(api.call_count, 2)

    def test_transcript_reused_without_reloading_whisper(self):
        import types
        source = self.root / 'source.fixture'
        source.write_bytes(b'fixture')
        segment = types.SimpleNamespace(start=1, end=2, text=' Buna! ')
        model = Mock()
        model.transcribe.return_value = ([segment], None)
        constructor = Mock(return_value=model)
        fake = types.SimpleNamespace(WhisperModel=constructor)
        with patch.dict('sys.modules', {'faster_whisper': fake}), \
             patch('importlib.metadata.version', return_value='fixture-version'):
            first = autoeditor.transcrie_live(str(source), 'small')
            second = autoeditor.transcrie_live(str(source), 'small')
        self.assertEqual([list(row) for row in first], second)
        constructor.assert_called_once()
        self.assertEqual(model.transcribe.call_args.kwargs['beam_size'], 5)

    def test_sound_rules_change_invalidates_review(self):
        source = self.root / 'source.fixture'
        source.write_bytes(b'fixture')
        catalogue = {'S001': {'path': 'sound', 'name': 'pumm', 'category': 'cadere',
                             'events': ['cadere'], 'description': 'Old rule'}}
        with patch('subprocess.run'), \
             patch('idei_ai.ia_gemini_video', return_value=good_review()) as api:
            idei_ai.verifica_idee_cu_video('fake', 'key', 'model', str(source), idea(), catalogue=catalogue)
            catalogue['S001']['description'] = 'New rule'
            idei_ai.verifica_idee_cu_video('fake', 'key', 'model', str(source), idea(), catalogue=catalogue)
        self.assertEqual(api.call_count, 2)


class SoundAndPreflightTests(unittest.TestCase):
    def test_creator_bone_effect_only_matches_impact_events(self):
        root = Path(__file__).resolve().parents[1]
        catalogue = sound_catalogue([root / 'sunete_mele'], autoeditor.clasifica_sunet)
        identifier, sound = next((key, sound) for key, sound in catalogue.items() if sound['name'] == 'pumm.mp3')
        self.assertIn('cadere', sound['events'])
        self.assertEqual(sound['category'], 'cadere')
        proposal = dict(id=identifier, sec=20, incredere=.99, motiv='Personajul cade la 20s', eveniment='victorie')
        self.assertEqual(validate_sounds([proposal], catalogue, 160)[0], [])
        proposal['eveniment'] = 'cadere'
        self.assertEqual(len(validate_sounds([proposal], catalogue, 160)[0]), 1)
        self.assertNotIn('path', public_catalogue(catalogue)[identifier])

    def test_catalogue_covers_all_ten_creator_sounds(self):
        root = Path(__file__).resolve().parents[1]
        catalogue = sound_catalogue([root / 'sunete_mele'], autoeditor.clasifica_sunet)
        # 30.09: creatorul a extins biblioteca (18 sunete) -> testul cere ACELEASI 10 DE BAZA,
        # nu un numar fix (altfel orice sunet nou adaugat rupe CI-ul aiurea).
        baza = {'pumm.mp3', 'faaa.mp3', 'bonk', 'wow', 'boom', 'Awkward', 'pop_7e9Is8L', 'basina'}
        nume = {sound['name'] for sound in catalogue.values()}
        for piesa in baza:
            self.assertTrue(any(piesa in n for n in nume), f'lipsa {piesa} din catalog')
        self.assertTrue(all(sound['events'] and sound['sha256'] for sound in catalogue.values()))

    def test_missing_key_fails_before_processing(self):
        errors, warnings = check({'GEMINI_MODEL': 'model'}, '.')
        self.assertTrue(any('GEMINI_API_KEY' in error for error in errors))
        self.assertTrue(any('YouTube' in warning for warning in warnings))

    def test_config_check_does_not_echo_credentials(self):
        env = dict(GEMINI_MODEL='model-a,model-b', GEMINI_API_KEY='dont-log-me',
                   YT_CLIENT_ID='secret', YT_CLIENT_SECRET='secret', YT_REFRESH_TOKEN='secret')
        errors, warnings = check(env, '.')
        self.assertEqual(errors, [])
        self.assertNotIn('dont-log-me', str(errors) + str(warnings))

    def test_duration_uses_metadata_without_audio_decode(self):
        result = Mock(stderr='Duration: 02:18:02.50, start: 0.0, bitrate: 1200 kb/s')
        with patch('autoeditor.subprocess.run', return_value=result) as process:
            self.assertEqual(autoeditor.durata_sursa('ff', 'fixture'), 8282.5)
        self.assertEqual(process.call_args.args[0], ['ff', '-i', 'fixture'])

    def test_upload_metadata_keeps_paragraphs_and_not_tags(self):
        from auto_upload_yt import citeste_upload_txt
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'metadata.txt'
            path.write_text('TITLU:\nTitlu real\n\nDESCRIERE:\nParagraf unu\n\n'
                            'https://example.test/playlist\n\nTAG-URI:\ntag1, tag2\n', encoding='utf-8')
            title, description = citeste_upload_txt(path)
        self.assertEqual(title, 'Titlu real')
        self.assertIn('Paragraf unu\n\nhttps://example.test/playlist', description)
        self.assertNotIn('tag1', description)

    def test_unknown_duration_not_invented(self):
        with patch('autoeditor.subprocess.run', return_value=Mock(stderr='Duration: N/A')):
            with self.assertRaises(ValueError):
                autoeditor.durata_sursa('ff', 'fixture')


if __name__ == '__main__':
    unittest.main()
