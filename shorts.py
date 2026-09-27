"""16-second shorts: review the actual portrait cut, never reuse episode titles blindly."""
import json
import os
import subprocess
from pathlib import Path

from autoeditor import gaseste_ffmpeg, citeste_cheie_gemini, clasifica_sunet, FOLDERE_MELE, calibreaza_lufs, EXT_AUDIO
from editorial import sound_catalogue, validate_review, validate_sounds, sound_filter
from idei_ai import verifica_idee_cu_video
from performance import file_digest


def candidates(plan, maximum):
    chosen = []
    for episode in sorted(plan, key=lambda e: -float(e.get('scor') or 0)):
        if episode.get('ai_verified') is not True:
            continue
        scene = episode.get('scene') or []
        if not scene:
            continue
        # FIX: episoadele-POVESTEA au 4 scene (acte) — fereastra shortului se
        # calculeaza pe INTREG episodul in timp live, nu doar pe o scena unica
        # (inainte le saria pe toate => 0 shorturi in modul poveste).
        start = float(scene[0][0])
        duration = (float(scene[0][1]) if len(scene) == 1
                    else sum(float(d) for _, d in scene))
        peak = float(episode['varf'])
        if duration < 16 or not start <= peak < start + duration:
            continue
        if any(abs(peak - other['peak']) < 300 for other in chosen):
            continue
        cut = max(start, min(peak - 11, start + duration - 16))
        chosen.append({'inceput': cut, 'sfarsit': cut + 16, 'peak': peak,
                       'titlu': episode.get('titlu', ''), 'de_ce': 'Candidat short; verifica povestea separat'})
        if len(chosen) >= maximum:
            break
    return chosen


def gaseste_intro_sting():
    """INTRO stil youtuber pe shorturi (cerinta creatorului): fisierul
    'Awkward Moment/Pause' din sunete_mele/ = sunetul de aparitie la inceput."""
    d = Path(__file__).resolve().parent / 'sunete_mele'
    if not d.is_dir():
        return None
    for f in sorted(d.iterdir()):
        nf = f.stem.lower()
        if ('awkward' in nf or 'intro' in nf) and f.suffix.lower() in EXT_AUDIO:
            return str(f)
    return None


def render_command(ff, source, start, out, sounds, intro=None, badge=None, ass_file=None):
    cmd = [ff, '-y', '-ss', str(start), '-t', '16', '-i', source]
    for sound in sounds:
        cmd += ['-i', sound['path']]
    if intro:
        cmd += ['-i', intro]
    chain = 'crop=ih*9/16:ih,scale=1080:1920:flags=lanczos'
    if ass_file:
        chain += f",subtitles={ass_file}"
    filters = [f'[0:v]{chain}[v]',
               '[0:a]atrim=duration=16,asetpts=PTS-STARTPTS,loudnorm=I=-16:TP=-1.5:LRA=11[a]']
    for n, sound in enumerate(sounds, 1):
        filters.append(sound_filter(n, sound['sec'], f's{n}'))
    # sting-ul de intro la 0.3s, usor dat in spate sub voice, cu fade scurt
    if intro:
        k = len(sounds) + 1
        filters.append(f'[{k}:a]atrim=duration=2.2,asetpts=PTS-STARTPTS,volume=0.55,'
                       f'afade=t=out:st=1.6:d=0.6,adelay=300:all=1[i{k}]')
    n_extra = len(sounds) + (1 if intro else 0)
    v_label = '[v]'
    if badge:
        k = n_extra + 1                      # badge e ULTIMUL input
        cmd += ['-i', badge]
        filters.append(f'[{k}:v]scale=-2:300,format=rgba[bdg]')
        filters.append('[v][bdg]overlay=W-w-28:30:alpha=0.94[vf]')
        v_label = '[vf]'
    inputs = '[a]' + ''.join(f'[s{n}]' for n in range(1, len(sounds) + 1))
    if intro:
        inputs += f'[i{len(sounds) + 1}]'
    total = len(sounds) + (1 if intro else 0) + 1
    filters.append(f'{inputs}amix=inputs={total}:duration=first:normalize=0,'
                   'loudnorm=I=-14:TP=-1.5:LRA=11[aout]')
    return cmd + ['-filter_complex', ';'.join(filters), '-map', v_label, '-map', '[aout]',
                  '-t', '16', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20',
                  '-c:a', 'aac', '-b:a', '160k', '-movflags', '+faststart', str(out)]


def _ts(t):
    ms = int(round((t - int(t)) * 1000))
    s = int(t) % 60
    m = int(t) // 60
    return f"{m:02d}:{s:02d},{ms:03d}"


def _scrie_ass(cale, linii, offset):
    """ASS stil POP pt short: galben mare, contur negru gros, jos-centrat."""
    out = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1080", "PlayResY: 1920", "",
           "[V4+ Styles]",
           "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
           "Style: POP,DejaVu Sans,88,&H0000FFFF,&H00000000,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,10,3,2,60,60,180,1",
           "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    for a2, b2, t2 in linii:
        r1 = max(0.0, a2 - offset)
        r2 = min(16.0, b2 - offset)
        if r2 - r1 < 0.6:
            continue
        txt = str(t2).replace("\n", " ").strip()
        fmt = lambda x: f"{int(x)//3600}:{int(x)%3600//60:02d}:{int(x)%60:02d}.{int(round((x-int(x))*100)):02d}"
        out.append(f"Dialogue: 0,{fmt(r1)},{fmt(r2)},POP,,0,0,0,,{txt}")
    Path(cale).write_text("\n".join(out), encoding="utf-8")


_scrie_ass_short = _scrie_ass


def main():
    root = Path(__file__).resolve().parent
    folder = root / 'episodes'
    maximum = (os.environ.get('MAX_SH', 'auto') or 'auto').strip().lower()
    limit = 6 if maximum in ('auto', 'ai') else max(0, int(maximum))
    if not limit:
        print('MAX_SH=0: fara shorts')
        return
    key = citeste_cheie_gemini(str(root))
    if not key:
        raise SystemExit('Shorts oprite: nu se livreaza fara verificare video.')
    with (folder / 'plan.json').open(encoding='utf-8') as f:
        plan = json.load(f)
    catalogue = sound_catalogue([root / 'sunete_mele', root / 'assets' / 'efecte'],
                               lambda p: FOLDERE_MELE.get(Path(p).parent.name.upper()) or clasifica_sunet(p))
    ff = gaseste_ffmpeg()
    source = str(root / 'live_curent.mp4')
    source_sha = file_digest(source)
    model = os.environ.get('GEMINI_MODEL', 'gemini-3.6-flash')
    audit, completed = [], 0
    for idea in candidates(plan, limit):
        entry = {'idee': idea}
        audit.append(entry)
        try:
            review = verifica_idee_cu_video(ff, key, model, source, idea,
                                            catalogue=catalogue, vertical=True, source_fingerprint=source_sha)
            entry['verificare'] = review
            _, title, _ = validate_review(review, 16)
            sounds, skipped = validate_sounds(review.get('sunete', []), catalogue, 16)
            entry.update(status='aprobat', sunete=sounds, sunete_respinse=skipped)
        except Exception as ex:
            entry.update(status='respins', motiv=f'Verificare nereusita: {type(ex).__name__}')
            continue
        number = completed + 1
        out = folder / f'SHORT{number:02d}.mp4'
        # SUBTITRARI pe short (creator 25.09: "subtitrari cat mai multe si pe short"):
        # replicile REALE din transcript, in fereastra celor 16s, stil POP galben jos
        ass_file, srt_file = None, None
        try:
            tj = folder / 'transcript.json'
            if tj.exists():
                linii = [(float(a2), float(b2), str(t2).strip())
                         for a2, b2, t2 in json.load(tj.open(encoding='utf-8'))
                         if idea['inceput'] - 0.5 <= float(a2) < idea['sfarsit'] - 0.4 and str(t2).strip()]
                if linii:
                    ass_file = folder / f'SHORT{number:02d}.ass'
                    _scrie_ass_short(ass_file, linii, idea['inceput'])
                    srt_file = folder / f'SHORT{number:02d}.srt'
                    with srt_file.open('w', encoding='utf-8') as fh:
                        for idx, (a2, b2, t2) in enumerate(linii, 1):
                            r1, r2 = max(0.0, a2 - idea['inceput']), max(0.1, min(16.0, b2 - idea['inceput']))
                            if r2 <= r1:
                                continue
                            fh.write(f"{idx}\n{_ts(r1)} --> {_ts(r2)}\n{t2}\n\n")
                    print(f'SHORT{number:02d}: {len(linii)} replici subtitrate')
        except Exception as _ex:
            print('subtitrari short sarite:', _ex)
            ass_file = None
        badge_serie = None
        try:
            _ctx = (root / 'context_sursa.txt')
            _semnatura = (_ctx.read_text(encoding='utf-8') if _ctx.exists() else '') + os.environ.get('AE_SERIE', '')
            if any(k in _semnatura.lower() for k in ('pokecity', 'pokemon', 'pixelmon')):
                _lg = root / 'assets' / 'logo_pokecity_clear.png'
                badge_serie = str(_lg) if _lg.exists() else None
        except Exception:
            badge_serie = None
        subprocess.run(render_command(ff, source, idea['inceput'], out, sounds,
                          intro=gaseste_intro_sting(), badge=badge_serie,
                          ass_file=str(ass_file) if ass_file else None), check=True)
        if not calibreaza_lufs(ff, str(out)):
            # FIX (oglinda fixului de la episoade): o masuratoare esuata NU
            # arunca shortul — YouTube re-normalizeaza oricum la upload.
            print('ATENTIE: NU am putut verifica LUFS pentru short — pleaca asa (non-fatal).')
        (folder / f'SHORT{number:02d}_upload.txt').write_text(
            f'TITLU: {title}\n\nDESCRIERE:\n{review["ce_se_intampla"]}\n\n#shorts #gaming #romania\n',
            encoding='utf-8')
        from upload_release import incarca_pe_release, slug_nume
        incarca_pe_release(str(out), nume=slug_nume(title + " SHORT", nr=number))
        completed += 1
    with (folder / 'DECIZII_SHORTS.json').open('w', encoding='utf-8') as f:
        json.dump(audit, f, ensure_ascii=False, indent=2)
    print(f'SHORTS GATA: {completed} verificate individual; zero e un rezultat acceptabil.')


if __name__ == '__main__':
    main()
