import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import sunete_referinta as sounds


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, *args):
        return json.dumps(self.payload).encode()


class SoundReferenceTests(unittest.TestCase):
    def test_parses_youtube_video_url_shapes_and_rejects_lookalikes(self):
        video_id = 'AbCdEfGhI_1'
        self.assertEqual(sounds.youtube_video_id(f'https://www.youtube.com/watch?v={video_id}&list=PL123'), video_id)
        self.assertEqual(sounds.youtube_video_id(f'https://youtu.be/{video_id}?t=12'), video_id)
        self.assertEqual(sounds.youtube_video_id(f'https://youtube.com/shorts/{video_id}'), video_id)
        self.assertEqual(sounds.youtube_video_id(f'https://youtube.com/live/{video_id}'), video_id)
        self.assertIsNone(sounds.youtube_video_id(f'https://youtube.com.evil.example/watch?v={video_id}'))
        self.assertIsNone(sounds.youtube_video_id(f'https://notyoutube.com/watch?v={video_id}'))
        self.assertIsNone(sounds.youtube_video_id('file:///tmp/video.mp4'))

    def test_video_id_is_validated_before_canonical_url(self):
        self.assertEqual(sounds.youtube_url('AbCdEfGhI_1'), 'https://www.youtube.com/watch?v=AbCdEfGhI_1')
        with self.assertRaises(ValueError):
            sounds.youtube_url('not-an-id')

    def test_youtube_download_requests_audio_only_and_canonical_video_url(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            def fake_run(command, **kwargs):
                self.assertIn('bestaudio', command)
                self.assertIn('--no-playlist', command)
                self.assertEqual(command[-1], 'https://www.youtube.com/watch?v=AbCdEfGhI_1')
                output_template = Path(command[command.index('--output') + 1])
                output_template.with_name('source.webm').write_bytes(b'fixture')
                return Mock(returncode=0)
            with patch('sunete_referinta.subprocess.run', side_effect=fake_run) as process:
                result = sounds.download_youtube_audio(
                    'https://youtu.be/AbCdEfGhI_1?feature=share', folder)
        self.assertEqual(result.name, 'source.webm')
        process.assert_called_once()

    def test_local_env_secret_reader_ignores_example_placeholders(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / '.env').write_text(chr(10).join(['GEMINI_API_KEY=cheia_ta_aici', 'AUDD_API_TOKEN=fixture-token', '']))
            self.assertIsNone(sounds.read_secret('GEMINI_API_KEY', root))
            self.assertEqual(sounds.read_secret('AUDD_API_TOKEN', root), 'fixture-token')

    def test_gemini_receives_only_a_bounded_audio_chunk_and_returns_json(self):
        with tempfile.TemporaryDirectory() as directory:
            segment = Path(directory) / 'chunk.wav'
            segment.write_bytes(b'RIFF-small-audio')
            response = FakeResponse({'candidates': [{'content': {'parts': [{'text':
                '{"events":[{"start_sec":0,"end_sec":1,"type":"sfx","label":"pop","confidence":0.8}]}'}]}}]})
            with patch('sunete_referinta.urllib.request.urlopen', return_value=response) as request:
                model, result = sounds.analyze_audio_with_gemini('fixture-key', ['model-a'],
                                                                  segment, 10, 20)
        self.assertEqual(model, 'model-a')
        self.assertEqual(result['events'][0]['label'], 'pop')
        sent = request.call_args.args[0]
        self.assertNotIn('fixture-key', sent.full_url)
        body = json.loads(sent.data)
        self.assertEqual(body['contents'][0]['parts'][0]['inline_data']['mime_type'], 'audio/wav')
        self.assertIn('între 0 și 20.00', body['contents'][0]['parts'][1]['text'])

    def test_windows_cover_full_video_and_cap_is_spread_across_it(self):
        windows = sounds.make_windows(120, window_seconds=60, stride_seconds=50, maximum=20)
        self.assertEqual(windows, [(0, 60), (50, 60), (100, 20)])
        self.assertEqual(sounds.coverage_fraction(windows, 120), 1.0)
        sampled = sounds.make_windows(1000, window_seconds=60, stride_seconds=50, maximum=4)
        self.assertEqual(len(sampled), 4)
        self.assertEqual(sampled[0][0], 0)
        self.assertGreater(sampled[-1][0], 900)
        self.assertLess(sounds.coverage_fraction(sampled, 1000), 0.3)

    def test_invalid_window_limits_are_rejected(self):
        with self.assertRaises(ValueError):
            sounds.make_windows(10, 0, 5, 2)
        with self.assertRaises(ValueError):
            sounds.make_windows(10, 5, 2, 0)

    def test_audio_events_are_sanitized_and_timestamps_are_shifted(self):
        document = {'events': [
            {'start_sec': 2, 'end_sec': 3, 'type': 'meme_sfx', 'label': 'Vine boom',
             'description': 'A bass hit', 'confidence': 0.9, 'background': True},
            {'start_sec': 3, 'end_sec': 4, 'type': 'speech', 'label': 'talking'},
            {'start_sec': 99, 'end_sec': 100, 'type': 'sfx', 'label': 'outside chunk'},
            {'start_sec': 'bad', 'end_sec': 1, 'type': 'sfx', 'label': 'bad time'},
        ]}
        events = sounds.parse_audio_events(document, offset=50, duration=60)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]['type'], 'meme')
        self.assertEqual(events[0]['start_sec'], 52)
        self.assertEqual(events[0]['end_sec'], 53)
        self.assertTrue(events[0]['background'])
        self.assertEqual(events[0]['local_matches'], [])

    def test_duplicate_observations_merge_but_repeated_effects_remain_separate(self):
        def event(start, end):
            return {'start_sec': start, 'end_sec': end, 'type': 'meme', 'label': 'Vine boom',
                    'description': '', 'confidence': 0.6, 'background': False, 'local_matches': []}
        merged = sounds.merge_audio_events([event(12.3, 13.2), event(10, 11), event(10.2, 11.2)])
        self.assertEqual(len(merged), 2)
        self.assertEqual(merged[0]['start_sec'], 10)
        self.assertEqual(merged[0]['end_sec'], 11.2)
        self.assertAlmostEqual(merged[0]['confidence'], 0.6)

    def test_music_hits_are_grouped_into_occurrences(self):
        tracks = sounds.group_music_hits([
            {'start_sec': 0, 'end_sec': 20, 'artist': 'Artist', 'title': 'Song'},
            {'start_sec': 15, 'end_sec': 35, 'artist': 'Artist', 'title': 'Song'},
            {'start_sec': 75, 'end_sec': 95, 'artist': 'Artist', 'title': 'Song'},
            {'start_sec': 30, 'end_sec': 50, 'artist': 'Other', 'title': 'Track'},
        ])
        self.assertEqual(len(tracks), 2)
        song = next(track for track in tracks if track['title'] == 'Song')
        self.assertEqual(song['appearances'], [{'start_sec': 0, 'end_sec': 35},
                                                {'start_sec': 75, 'end_sec': 95}])

    def test_audd_multipart_request_does_not_return_or_log_the_token(self):
        with tempfile.TemporaryDirectory() as directory:
            audio = Path(directory) / 'clip.wav'
            audio.write_bytes(b'RIFF-fixture')
            response = FakeResponse({'status': 'success', 'result': {
                'title': 'A song', 'artist': 'An artist', 'song_link': 'https://example.test/private'}})
            with patch('sunete_referinta.urllib.request.urlopen', return_value=response) as request:
                result = sounds.audd_identify('fixture-api-token', audio)
        self.assertEqual(result, {'title': 'A song', 'artist': 'An artist'})
        sent = request.call_args.args[0]
        self.assertIn(b'fixture-api-token', sent.data)
        self.assertNotIn('fixture-api-token', repr(result))
        self.assertEqual(sent.full_url, sounds.AUDD_URL)

    def test_audd_provider_error_is_not_exposed_verbatim(self):
        with tempfile.TemporaryDirectory() as directory:
            audio = Path(directory) / 'clip.wav'
            audio.write_bytes(b'RIFF-fixture')
            response = FakeResponse({'status': 'error', 'error': {'message': 'sensitive provider text'}})
            with patch('sunete_referinta.urllib.request.urlopen', return_value=response):
                result = sounds.audd_identify('fixture-token', audio)
        self.assertEqual(result, {'_error': 'provider_error'})
        self.assertNotIn('sensitive provider text', repr(result))

    def test_youtube_search_is_metadata_only_and_builds_safe_video_urls(self):
        payload = {'entries': [
            {'id': 'AbCdEfGhI_1', 'title': 'Sound effect', 'uploader': 'Channel'},
            {'id': 'short', 'title': 'bad ID'},
        ]}
        process = Mock(return_value=Mock(returncode=0, stdout=json.dumps(payload)))
        with patch('sunete_referinta.subprocess.run', process):
            results = sounds.search_youtube('vine boom sound effect', limit=8)
        self.assertEqual(results, [{'title': 'Sound effect', 'channel': 'Channel',
                                   'url': 'https://www.youtube.com/watch?v=AbCdEfGhI_1'}])
        command = process.call_args.args[0]
        self.assertIn('ytsearch5:vine boom sound effect', command)
        self.assertIn('--flat-playlist', command)
        self.assertNotIn('--format', command)

    def test_builds_deduplicated_search_queries_for_tracks_and_effects(self):
        events = [
            {'type': 'meme', 'label': 'Vine boom', 'confidence': 0.9},
            {'type': 'meme', 'label': 'Vine boom', 'confidence': 0.8},
            {'type': 'music', 'label': 'quiet music', 'confidence': 0.7},
        ]
        tracks = [{'artist': 'Artist', 'title': 'Track'}]
        queries = sounds.build_search_queries(events, tracks, maximum=8)
        self.assertEqual(len(queries), 2)
        self.assertIn('official audio', queries[0]['query'])
        self.assertIn('meme sound effect', queries[1]['query'])

    def test_report_is_honest_about_missing_music_token_and_licenses(self):
        report = sounds.render_report(
            'https://www.youtube.com/watch?v=AbCdEfGhI_1',
            'https://www.youtube.com/watch?v=AbCdEfGhI_1', 60, [], [], [],
            [(0, 60)], 0, [(0, 20)], 0, False, False, 0, [])
        self.assertIn('lipsește tokenul opțional', report)
        self.assertIn('nu verificări de licență', report)
        self.assertIn('fragmente audio', report)
        self.assertNotIn('api_token=', report)

    def test_local_audio_index_ignores_non_audio_and_symlinks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'hit.mp3').write_bytes(b'fixture')
            (root / 'notes.txt').write_text('not audio')
            hidden = root / '.hidden.mp3'
            hidden.write_bytes(b'ignored')
            files = sounds.local_audio_files([root])
        self.assertEqual([path.name for path, _ in files], ['hit.mp3'])

    def test_audio_fingerprint_matches_same_signal_after_gain_and_offset(self):
        try:
            import numpy as np
        except ImportError:
            self.skipTest('NumPy is installed from requirements.txt in the runtime environment')
        rate = 11025
        rng = np.random.default_rng(15)
        reference = rng.normal(0, 0.1, rate * 2).astype(np.float32)
        prefix_samples = 43 * 128
        target = np.concatenate([np.zeros(prefix_samples, dtype=np.float32), reference * 0.4])
        ref_hashes = sounds.audio_fingerprints(reference, rate)
        target_hashes = sounds.audio_fingerprints(target, rate)
        result = sounds.compare_fingerprints(ref_hashes, target_hashes, rate)
        self.assertIsNotNone(result)
        self.assertGreater(result['score'], 0.5)
        self.assertAlmostEqual(result['offset_sec'], 0.5, delta=0.1)


if __name__ == '__main__':
    unittest.main()
