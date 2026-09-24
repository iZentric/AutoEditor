import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, Mock
import urllib.error

import autoeditor as ae
import idei_ai
from editorial import (approved_episodes, sound_catalogue, validate_review, validate_sounds,
                       transcript_pages, quote_catalogue, selected_pops, sound_filter)
from nume_public import rename_deliverables
from shorts import candidates, render_command


_cache_patch = patch.dict(os.environ, {'AE_CACHE': '0'})


def setUpModule():
    _cache_patch.start()


def tearDownModule():
    _cache_patch.stop()


def good_review(**changes):
    result = dict(ok=True, un_joc=True, poveste_completa=True, titlu_sustinut=True,
                  scor=8.5, hook_sec=110, titlu_corectat='Am CASTIGAT lupta!',
                  ce_se_intampla='Jucatorul castiga lupta din arena.',
                  poveste=dict(inceput='0s: intra in arena', desfasurare='40s: lupta',
                               final='110s: castiga'), sunete=[])
    return dict(result, **changes)


def idea(start=0):
    return dict(inceput=start, sfarsit=start + 160, titlu='Lupta in arena', scor=8)


class EditorialTests(unittest.TestCase):
    def setUp(self):
        self.catalogue = {
            'S001': dict(path='/sounds/pumm.mp3', name='pumm.mp3', category='cadere'),
            'S002': dict(path='/sounds/bonk.mp3', name='bonk.mp3', category='hit'),
            'S003': dict(path='/sounds/bamboo.mp3', name='bamboo.mp3', category='hit')}

    def test_good_review_and_absolute_hook(self):
        approved, audit = approved_episodes([idea(100)], lambda _: good_review(), {}, 500, 1)
        self.assertEqual(approved[0]['varf'], 210)
        self.assertEqual(approved[0]['scene'], [(100, 160)])
        self.assertEqual(approved[0]['ai_scor'], 8.5)
        self.assertEqual(audit[0]['status'], 'aprobat')

    def test_fail_closed_verdicts(self):
        for change in [dict(ok=False), dict(ok='true'), dict(un_joc=False),
                       dict(poveste_completa=False), dict(titlu_sustinut=False),
                       dict(scor=6.99), dict(scor=float('nan')), dict(scor=True),
                       dict(hook_sec=160), dict(hook_sec=-1), dict(hook_sec='12'),
                       dict(titlu_corectat='Ep. 1'), dict(poveste={}), dict(ce_se_intampla='')]:
            with self.subTest(change=change):
                approved, _ = approved_episodes([idea()], lambda _: good_review(**change), {}, 500, 1)
                self.assertEqual(approved, [])

    def test_api_outage_no_fallback_no_secret(self):
        def fail(_):
            raise RuntimeError('secret-in-url')
        approved, audit = approved_episodes([idea()], fail, {}, 500, 1)
        self.assertEqual(approved, [])
        self.assertEqual(audit[0]['status'], 'neverificat')
        self.assertNotIn('secret-in-url', json.dumps(audit))

    def test_overlap_and_maximum(self):
        verify = Mock(return_value=good_review())
        approved, _ = approved_episodes([idea(0), idea(50), idea(200), idea(400)], verify, {}, 1000, 2)
        self.assertEqual(len(approved), 2)
        self.assertEqual(verify.call_count, 2)
        self.assertEqual(approved[1]['scene'], [(200, 160)])

    def test_invalid_intervals_never_sent_to_model(self):
        verify = Mock()
        bad = [dict(inceput=0, sfarsit=20), dict(inceput=-5, sfarsit=155),
               dict(inceput=900, sfarsit=1060), dict(inceput=float('nan'), sfarsit=160)]
        self.assertEqual(approved_episodes(bad, verify, {}, 1000, 5)[0], [])
        verify.assert_not_called()

    def test_sound_safety_and_no_random_fill(self):
        proposal = dict(id='S001', sec=20, incredere=.95, motiv='Cade de pe bloc la 20s')
        proposals = [proposal, dict(proposal, id='../../secret', sec=50),
                     dict(proposal, id='S002', sec=23), dict(proposal, sec=70),
                     dict(proposal, id='S002', sec=40), dict(proposal, id='S003', sec=80),
                     dict(proposal, id='S003', sec=float('nan'))]
        sounds, rejected = validate_sounds(proposals, self.catalogue, 160)
        self.assertEqual([s['id'] for s in sounds], ['S001', 'S002'])
        self.assertEqual(len(rejected), 5)
        self.assertEqual(validate_sounds([], self.catalogue, 160), ([], []))
        for change in [dict(incredere=.2), dict(sec=159), dict(sec=-1), dict(motiv=''),
                       dict(incredere=True), dict(sec='15')]:
            self.assertEqual(validate_sounds([dict(proposal, **change)], self.catalogue, 160)[0], [])

    def test_catalogue_only_existing_assets_and_originals_untouched(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'bonk.mp3').write_bytes(b'original')
            (root / 'notes.txt').write_text('not audio')
            (root / '.hidden.mp3').write_bytes(b'not indexed')
            catalogue = sound_catalogue([root], ae.clasifica_sunet)
            self.assertEqual(list(catalogue), ['S001'])
            self.assertEqual(catalogue['S001']['category'], 'hit')
            self.assertEqual((root / 'bonk.mp3').read_bytes(), b'original')

    def test_transcript_tail_is_not_lost(self):
        transcript = [(i * 10, i * 10 + 2, f'REPLICA_{i}_' + 'x' * 200) for i in range(1000)]
        pages = list(transcript_pages(transcript))
        self.assertGreater(len(pages), 2)
        for i in range(1000):
            self.assertTrue(any(f'REPLICA_{i}_' in page for page in pages))
        self.assertIn('REPLICA_999_', pages[-1])

    def test_ideas_scan_all_pages_including_late_story(self):
        transcript = [(i * 10, i * 10 + 2, 'vorba ' * 40) for i in range(500)]
        calls = []
        def fake(_key, _model, prompt, _frames):
            calls.append(prompt)
            return {'idei': [idea(4700)] if '4990.00' in prompt else []}
        with tempfile.TemporaryDirectory() as tmp:
            result = idei_ai.idei_cu_ai(fake, 'key', 'model', transcript, 5000, tmp)
        self.assertGreater(len(calls), 1)
        self.assertEqual(result[0]['inceput'], 4700)

    def test_empty_ideas_are_valid_no_forced_episode(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(idei_ai.idei_cu_ai(lambda *a: {'idei': []}, 'k', 'm',
                                              [(0, 10, 'Nu se intampla nimic')], 500, tmp), [])

    def test_page_failure_is_not_silently_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                idei_ai.idei_cu_ai(lambda *a: {}, 'k', 'm', [(0, 10, 'text')], 500, tmp)

    def test_pop_quotes_are_verbatim_no_invention_or_ass_injection(self):
        transcript = [(110, 112, 'L-am prins chiar acum!'), (114, 117, 'O alta replica!'),
                      (140, 142, '{\\pos(1,1)}injected'), (145, 147, 'Bravo, am reusit!')]
        quotes = quote_catalogue(transcript, 100, 260)
        self.assertEqual(len(quotes), 3)
        pops = selected_pops(['R001', 'fake', 'R002', 'R003', 'R001'], quotes)
        self.assertEqual(pops, [(10, 'L-am prins chiar acum!'), (45, 'Bravo, am reusit!')])

    def test_review_cuts_exact_interval_without_extra_padding(self):
        with patch('subprocess.run') as run, \
             patch('idei_ai.ia_gemini_video', return_value=good_review()) as api, \
             patch('idei_ai.file_digest', return_value='fixture-hash'):
            idei_ai.verifica_idee_cu_video('ff', 'key', 'model', 'vod.mp4', idea(100),
                                          catalogue=self.catalogue, vertical=True)
        command = run.call_args.args[0]
        self.assertEqual(float(command[command.index('-ss') + 1]), 100)
        self.assertEqual(float(command[command.index('-t') + 1]), 160)
        self.assertIn('crop=ih*9/16:ih', command[command.index('-vf') + 1])
        self.assertIn('S001', api.call_args.args[2])
        self.assertFalse(Path(api.call_args.args[3]).exists())

    def test_sound_filter_is_brief_and_quieter_than_voice(self):
        filt = sound_filter(2, 12.5, 's2')
        self.assertIn('atrim=duration=2', filt)
        self.assertIn('loudnorm=I=-24', filt)
        self.assertIn('adelay=12500', filt)

    def test_model_list_is_split_not_used_as_single_model(self):
        response = Mock()
        response.__enter__ = Mock(return_value=io.StringIO(json.dumps(
            {'candidates': [{'content': {'parts': [{'text': '{"idei": []}'}]}}]})))
        response.__exit__ = Mock(return_value=False)
        error = urllib.error.HTTPError('url', 404, 'missing', {}, None)
        with patch('autoeditor.urllib.request.urlopen', side_effect=[error, response]) as request:
            result = ae.ia_gemini('key', 'old-model, valid-model', 'prompt', [])
        self.assertEqual(result, {'idei': []})
        self.assertIn('/models/valid-model:', request.call_args.args[0].full_url)

    def test_shorts_only_verified_and_within_episode(self):
        plan = [dict(ai_verified=True, scene=[(100, 160)], varf=258, scor=8, titlu='Titlu')]
        result = candidates(plan, 3)
        self.assertEqual((result[0]['inceput'], result[0]['sfarsit']), (244, 260))
        plan[0]['ai_verified'] = False
        self.assertEqual(candidates(plan, 3), [])

    def test_short_render_has_crop_and_normalized_sounds(self):
        command = render_command('ff', 'source', 100, 'out', [dict(path='bonk.mp3', sec=10)])
        filters = command[command.index('-filter_complex') + 1]
        self.assertIn('crop=ih*9/16:ih', filters)
        self.assertIn('loudnorm=I=-24', filters)
        self.assertIn('amix=inputs=2', filters)

    def test_rename_keeps_files_in_delivery_directory_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / 'episodes'
            folder.mkdir()
            for name in ('EP01.mp4', 'EP01.srt', 'EP01_miniatura.jpg'):
                (folder / name).write_bytes(b'test')
            (folder / 'EP01_upload.txt').write_text('TITLU: Am prins ceva!\n')
            rename_deliverables(folder)
            names = sorted(p.name for p in folder.iterdir())
            self.assertEqual(len(names), 4)
            self.assertTrue(all(n.startswith('AM_PRINS_CEVA_1') for n in names))
            self.assertEqual(list(Path(tmp).iterdir()), [folder])
            rename_deliverables(folder)
            self.assertEqual(names, sorted(p.name for p in folder.iterdir()))

    def test_per_piece_upload_uses_public_name_without_moving_original(self):
        from upload_release import incarca_pe_release
        with tempfile.TemporaryDirectory() as tmp:
            original = Path(tmp) / 'EP01.mp4'
            original.write_bytes(b'fixture')
            def fake_run(command, **kwargs):
                uploaded = Path(command[4])
                self.assertEqual(uploaded.name, 'POVESTE_1.mp4')
                self.assertEqual(uploaded.read_bytes(), b'fixture')
            with patch.dict(os.environ, {'RELEASE_TOKEN': 'fake', 'GITHUB_REPOSITORY': 'owner/repo',
                                         'RELEASE_TAG': 'fixture'}), \
                 patch('upload_release.subprocess.run', side_effect=fake_run):
                self.assertTrue(incarca_pe_release(str(original), 'POVESTE_1.mp4'))
            self.assertEqual(original.read_bytes(), b'fixture')

    def test_audio_silence_or_nan_does_not_pass_mastering(self):
        with patch.object(ae, 'masoara_lufs', return_value=(float('-inf'), float('nan'))):
            self.assertIsNone(ae.calibreaza_lufs('fake', 'fake.mp4'))

    def test_loudness_in_target_but_clipping_requires_mastering(self):
        with patch.object(ae, 'masoara_lufs', return_value=(-14, 2)), \
             patch.object(ae, 'masoara_lufs_json', return_value=None) as measure:
            self.assertIsNone(ae.calibreaza_lufs('fake', 'fake.mp4'))
            measure.assert_called_once()


class MainIntegrationTests(unittest.TestCase):
    def exercise(self, review, render_mode=False):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'cunoastere').mkdir()
            with patch.object(ae, '__file__', str(root / 'autoeditor.py')), \
                 patch('sys.argv', ['autoeditor.py', 'fake.mp4', '--ai'] +
                       ([] if render_mode else ['--doar-analiza'])), \
                 patch.dict(os.environ, {'GEMINI_API_KEY': 'fake'}), \
                 patch.object(ae, 'gaseste_ffmpeg', return_value='fake'), \
                 patch.object(ae, 'rezolutie_sursa', return_value=(1920, 1080)), \
                 patch.object(ae, 'fps_sursa', return_value=30), \
                 patch.object(ae, 'durata_sursa', return_value=500), \
                 patch.object(ae, 'file_digest', return_value='fixture-sha'), \
                 patch.object(ae, 'analiza_audio', return_value=[(i, -20) for i in range(501)]), \
                 patch.object(ae, 'detecteaza_explozii', return_value=([], [])), \
                 patch.object(ae, 'transcrie_live', return_value=[(5, 7, 'Intram in arena')]), \
                 patch.object(ae, 'idei_cu_ai', return_value=[idea()]), \
                 patch.object(ae, 'verifica_idee_cu_video', return_value=review), \
                 patch.object(ae, 'comanda_randare', return_value=None) as render, \
                 patch.object(ae, 'profil_retentie', return_value=(90, 100, 90)), \
                 patch.object(ae, 'comprima_zone_moarte') as compress, \
                 patch.object(ae, 'aranjeaza_sunete_mele') as mutate:
                error = None
                try:
                    ae.main()
                except SystemExit as ex:
                    error = ex
                if render_mode:
                    render.assert_called_once()
                    self.assertEqual(render.call_args.args[2]['scene'], [(0, 160)])
                    self.assertEqual(render.call_args.args[3], 160)
                    self.assertEqual(render.call_args.args[8], {})  # No fixed sound slots.
                    self.assertEqual(render.call_args.args[10], [])  # No random padding.
                    compress.assert_not_called()
                else:
                    render.assert_not_called()
                mutate.assert_not_called()
            plan = json.loads((root / 'episodes' / 'plan.json').read_text())
            audit = json.loads((root / 'episodes' / 'DECIZII_AI.json').read_text())
            return error, plan, audit

    def test_quiet_story_can_pass_without_audio_peaks(self):
        error, plan, audit = self.exercise(good_review())
        self.assertIsNone(error)
        self.assertTrue(plan[0]['ai_verified'])
        self.assertEqual(plan[0]['varf'], 110)
        self.assertEqual(audit[0]['status'], 'aprobat')

    def test_approved_timeline_is_not_changed_by_quiet_audio(self):
        error, plan, audit = self.exercise(good_review(), render_mode=True)
        self.assertIsNotNone(error)  # Mock renderer fails; no downstream upload is allowed.
        self.assertEqual(plan[0]['scene'], [[0, 160]])

    def test_all_rejected_writes_empty_plan_and_stops(self):
        error, plan, audit = self.exercise(good_review(un_joc=False))
        self.assertIsNotNone(error)
        self.assertEqual(plan, [])
        self.assertEqual(audit[0]['status'], 'respins')


if __name__ == '__main__':
    unittest.main()
