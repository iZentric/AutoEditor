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


def render_command(ff, source, start, out, sounds, intro=None):
    cmd = [ff, '-y', '-ss', str(start), '-t', '16', '-i', source]
    for sound in sounds:
        cmd += ['-i', sound['path']]
    if intro:
        cmd += ['-i', intro]
    filters = ['[0:v]crop=ih*9/16:ih,scale=1080:1920:flags=lanczos[v]',
               '[0:a]atrim=duration=16,asetpts=PTS-STARTPTS,loudnorm=I=-16:TP=-1.5:LRA=11[a]']
    for n, sound in enumerate(sounds, 1):
        filters.append(sound_filter(n, sound['sec'], f's{n}'))
    # sting-ul de intro la 0.3s, usor dat in spate sub voice, cu fade scurt
    if intro:
        k = len(sounds) + 1
        filters.append(f'[{k}:a]atrim=duration=2.2,asetpts=PTS-STARTPTS,volume=0.55,'
                       f'afade=t=out:st=1.6:d=0.6,adelay=300:all=1[i{k}]')
    inputs = '[a]' + ''.join(f'[s{n}]' for n in range(1, len(sounds) + 1))
    if intro:
        inputs += f'[i{len(sounds) + 1}]'
    total = len(sounds) + (1 if intro else 0) + 1
    filters.append(f'{inputs}amix=inputs={total}:duration=first:normalize=0,'
                   'loudnorm=I=-14:TP=-1.5:LRA=11[aout]')
    return cmd + ['-filter_complex', ';'.join(filters), '-map', '[v]', '-map', '[aout]',
                  '-t', '16', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20',
                  '-c:a', 'aac', '-b:a', '160k', '-movflags', '+faststart', str(out)]


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
        subprocess.run(render_command(ff, source, idea['inceput'], out, sounds,
                          intro=gaseste_intro_sting()), check=True)
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
