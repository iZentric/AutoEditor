#!/usr/bin/env python3
# SHORT REAL pe GitHub Actions: fereastra de energie maxima din video-ul canalului ->
# auto-editor (taie golurile) -> whisper pe VOCEA REALA (captions karaoke umane) ->
# SFX inteligent + shake + logo POKECITY -> LUFS -14 -> out/SHORT_REAL.mp4 + kit.
import os, sys, subprocess, argparse, re
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)

ap = argparse.ArgumentParser()
ap.add_argument('src')
ap.add_argument('--window', default='')
ap.add_argument('--tag', default='short-real')
ap.add_argument('--titlu', default='')
ap.add_argument('--subs', default='', help='json3 oficial YouTube (captions Google, calitate > whisper)')
ap.add_argument('--hook', default='')
ap.add_argument('--big', default='', help='cuvantul pt pop-out mare (gol = auto)')
ap.add_argument('--punch', default='', help='cuvinte-putere separate prin virgula')
a = ap.parse_args()

def _ff():
    p = os.environ.get('FFMPEG')
    if p: return p
    try:
        import imageio_ffmpeg; return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return 'ffmpeg'
FF = _ff(); os.environ['FFMPEG'] = FF
import editor_pro as ep
import autoeditor

if not os.path.exists(os.path.join(ep.PRO, 'boom.wav')):
    alt = os.path.join(REPO, 'workspace_migrat', 'pro')
    if os.path.exists(os.path.join(alt, 'boom.wav')):
        ep.PRO = alt
print('[PRO SFX]', ep.PRO)

# fereastra se decide pe sursa originala (audio), apoi upscale DOAR pe bucati
def _src_dims():
    ei = subprocess.run([FF, '-i', a.src], capture_output=True, text=True).stderr
    return re.search(r'Stream #0:0.*?(\d{3,5})x(\d{2,5})', ei)

logo = os.path.join(REPO, 'assets', 'logo_pokecity.png')
if not os.path.exists(logo):
    logo = None
print('[LOGO]', 'OK' if logo else 'fara logo')

def _sec(s):
    s = s.strip().replace(',', '.')
    if ':' in s:
        m, _, r = s.partition(':')
        return int(m) * 60 + float(r)
    return float(s)

if a.window:
    p0, _, p1 = a.window.partition('-')
    t0, t1 = _sec(p0), _sec(p1)
    if t1 - t0 < 8 or t1 - t0 > 20:
        t1 = t0 + 16
else:
    t0, t1 = ep.find_best_window(a.src, win=16.0)
print('[FEREASTRA] %.1fs -> %.1fs' % (t0, t1))

# upscale inteligent DOAR pe fereastra (360p -> 720p lanczos + sharpen)
W0 = t0   # inceputul ferestrei in timpul SURSEI (subs se parseeaza pe sursa)
hm = _src_dims()
if hm and int(hm.group(2)) < 720:
    print('[SURA]', hm.group(1), 'x', hm.group(2), '-> 720p + sharpen (doar fereastra)')
    subprocess.run([FF, '-y', '-loglevel', 'error', '-ss', str(t0), '-t', str(t1 - t0 + 1), '-i', a.src,
        '-vf', 'scale=1280:720:flags=lanczos,unsharp=5:5:0.8:5:5:0.4',
        '-c:v', 'libx264', '-crf', '18', '-preset', 'fast', '-c:a', 'aac', '-b:a', '192k',
        '/tmp/src_hd.mp4'], check=True)
    a.src = '/tmp/src_hd.mp4'
    t1 = t1 - t0
    t0 = 0.0

DIAC = str.maketrans({'ă':'a','â':'a','î':'i','ș':'s','ț':'t','Ă':'A','Â':'A','Î':'I','Ș':'S','Ț':'T','ş':'s','ţ':'t','Ş':'S','Ţ':'T'})
def _fara_diac(x):
    return x.translate(DIAC)

words_sub = []
if a.subs and os.path.exists(a.subs):
    import json as _json
    dd = _json.load(open(a.subs))
    for ev in dd.get('events', []):
        if 'segs' not in ev: continue
        tt = ev.get('tStartMs', 0) / 1000.0
        for sg in ev['segs']:
            ww = (sg.get('utf8') or '').strip()
            ww = ww.replace('>>', ' ').strip(' ,.!?…').strip()
            if not ww or len(ww) < 2: continue
            st = tt + (sg.get('tOffsetMs') or 0) / 1000.0
            if W0 - 0.2 <= st <= W0 + 16.5:
                words_sub.append({'w': _fara_diac(ww), 's': round(st - W0, 2),
                                  'e': round(st - W0 + 0.45, 2)})
    # merge secvente identice consecutive
    merged = []
    for w in words_sub:
        if merged and merged[-1]['w'] == w['w'] and w['s'] - merged[-1]['e'] < 0.5:
            merged[-1]['e'] = w['e']; continue
        merged.append(w)
    words_sub = merged
    print('[SUBS OFICIALE] %d cuvinte in fereastra (calitate Google ASR)' % len(words_sub))

big_finale = None
if a.big and words_sub:
    for w in words_sub:
        if w['w'].lower() == a.big.lower():
            big_finale = (a.big.upper(), max(0.0, w['s'] - 0.05), min(16.0, w['e'] + 0.9))
            break
    print('[BIG]', big_finale)
punch_args = tuple(x.strip().lower() for x in a.punch.split(',') if x.strip())

if words_sub:
    total = ep.build(a.src, '/tmp/_short_raw.mp4', words_sub,
                     trim=(t0, t0 + 16.0), compress=False,
                     hook_text=(a.hook or None), punch_words=punch_args,
                     big_finale=big_finale, series='pokecity', logo_path=logo,
                     bg_t=1.0, outdir='/tmp/_pro_real')
else:
    dummy = [{'w': 'povestea', 's': 0.0, 'e': 0.2}]
    total = ep.build(a.src, '/tmp/_short_raw.mp4', dummy,
                     trim=(t0, min(t1, t0 + 16.0)), compress=True,
                     hook_text=(a.hook or None), punch_words=punch_args,
                     series='pokecity', logo_path=logo,
                     bg_t=1.0, outdir='/tmp/_pro_real')
print('[BUILD] %.2fs montate (auto-editor + whisper real)' % total)

subprocess.run([FF, '-y', '-loglevel', 'error', '-i', '/tmp/_short_raw.mp4', '-t', '16.0',
                '-c:v', 'libx264', '-crf', '19', '-preset', 'fast', '-pix_fmt', 'yuv420p',
                '-c:a', 'copy', '-movflags', '+faststart', '/tmp/_short_16.mp4'], check=True)
src_fin = '/tmp/_short_16.mp4'
try:
    r = autoeditor.calibreaza_lufs(FF, '/tmp/_short_16.mp4')
    print('[LUFS]', r)
    if r and os.path.exists('/tmp/_short_16_cal.mp4'):
        src_fin = '/tmp/_short_16_cal.mp4'
except Exception as ex:
    print('[LUFS] skip:', ex)

os.makedirs('out', exist_ok=True)
OUT = 'out/SHORT_REAL.mp4'
subprocess.run(['cp', src_fin, OUT], check=True)

e = subprocess.run([FF, '-i', OUT], capture_output=True, text=True).stderr
m = re.search(r'Duration: (\d+):(\d+):([\d.]+)', e)
d = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
mm = re.search(r'Stream #0:0.*?(\d{3,4})x(\d{3,4})', e)
lu = subprocess.run([FF, '-i', OUT, '-af', 'ebur128', '-f', 'null', '-'], capture_output=True, text=True).stderr
lm = re.search(r'I:\s+(-?[\d.]+) LUFS', lu)
rep = [('durata', '%.2f s' % d, abs(d - 16.0) <= 0.5),
       ('rezolutie', (mm.group(1) + 'x' + mm.group(2)) if mm else '?', bool(mm) and mm.group(1) == '1080'),
       ('LUFS', lm.group(1) if lm else '?', bool(lm) and -15.5 <= float(lm.group(1)) <= -12.5)]

titlu = a.titlu or ('MOMENTUL CEL MAI TARE ' + a.tag.upper() + ' ?!')
kit = ("SHORT REAL (%s) — montat pe GitHub Actions\n"
       "Fereastra: %.0fs-%.0fs din sursa (energie maxima; auto-editor a taiat golurile)\n"
       "Captions = pe VOCEA REALA (whisper, karaoke sloturi: galben/alb/rosu)\n"
       "TITLU (editeaza in Studio, formula JH: pers. I + verb de actiune + ?!):\n"
       "  %s\n"
       "DESCRIERE:\n"
       "  Momentul real din episod, la perfectie. Ce ai fi facut in locul meu? 👇\n"
       "  #shorts #minecraft #pokecity #pokemon #gamingromania\n"
       "POSTARE: 18:00-20:00 | 1/zi | DUPA 48h: viewed-vs-swiped <60%% -> schimbi primele 2s\n"
       ) % (a.tag, t0, t1, titlu)
open('out/KIT_SHORT_REAL.txt', 'w').write(kit)

sfile = os.environ.get('GITHUB_STEP_SUMMARY')
if sfile:
    with open(sfile, 'a') as s:
        s.write('## SHORT REAL (%s)\n- fereastra: %.1fs-%.1fs\n' % (a.tag, t0, t1))
        for k, v, ok in rep:
            s.write('- %s: **%s** %s\n' % (k, v, 'OK' if ok else 'VERIFICA'))
print('[GATA]', OUT, os.path.getsize(OUT) // 1024, 'KB')
