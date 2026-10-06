#!/usr/bin/env python3
# EDITOR PRO v2 — shorturi verticale stil trending, automatizate.
# Captions KARAOKE pe vocea reala (whisper) + SFX (whoosh/boom/pop/riser) + shake
# + muzica ducked + logo + hook/CTA. Depende: PIL, numpy, ffmpeg, faster-whisper.
import json, os, subprocess, math, wave, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BASE = os.path.dirname(os.path.abspath(__file__))
def _find_font():
    cands = [
        os.path.join(BASE, 'assets', 'Anton.ttf'),
        '/home/user/autoeditor/assets/Anton.ttf',
        os.environ.get('FONT_GROS', ''),
    ]
    import autoeditor  # convenție repo: font_gros() știe unde e fontul gros
    try:
        cands.append(autoeditor.font_gros(48).path)
    except Exception:
        pass
    for c in cands:
        if c and os.path.exists(c): return c
    raise FileNotFoundError('Anton.ttf negasit — pune-l in assets/')
FONT = _find_font()
PRO  = os.path.join(BASE, 'sunete_virale') if os.path.isdir(os.path.join(BASE,'sunete_virale')) else os.path.join(BASE, 'pro')
def _find_ff():
    import os as _os, shutil as _sh
    p = _os.environ.get('FFMPEG')     # conventia repo-ului (AGENTS/creier)
    if p and _sh.which(p.split()[0]) or (p and _os.path.exists(p)): return p
    p = _sh.which('ffmpeg')
    if p: return p
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return 'ffmpeg'
FF = _find_ff()
W, H = 1080, 1920


# ---------- SUNET INTELIGENT: fiecare efect are un context semantic ----------
SFX_RULES = {
    'boom':       'cuvant-putere / revelatie (energie max)',
    'riser':      'inainte de un moment mare (build-up)',
    'whoosh':     'start + schimbari de scena',
    'metal_pipe': 'cadere / lovire / fail in joc',
    'heheheha':   'moment comic (ras boss)',
    'boowomp':    'dezamagire / ceva ciudat',
    'bass_drop':  'dupa o pauza de tensiune',
}



def autocut_autoeditor(src, t0, t1, out='/tmp/_cut.mp4', margin='0.12sec'):
    """auto-editor (WyattBlue, 5.4K stars): taie liniistea inteligent (VAD real).
    Intoarce (cale_clip, durata). Fallback: segmentul brut daca unelta lipseste."""
    import shutil as _sh
    ae = _sh.which('auto-editor')
    seg = f'/tmp/_seg_src.mp4'
    subprocess.run([FF,'-y','-loglevel','error','-ss',str(t0),'-t',str(t1-t0),'-i',src,
                    '-c:v','libx264','-preset','veryfast','-c:a','aac',seg])
    if ae:
        for thr in ('5%','8%','12%'):
            r = subprocess.run([ae, seg, '--edit', f'(audio:threshold={thr})', '--margin','0.25sec',
                                '--no-open','-o',out], capture_output=True, text=True, timeout=300)
            if r.returncode == 0 and os.path.exists(out):
                dur = clip_duration(out)
                if dur and 1.0 < dur < (t1-t0)-0.3:
                    print(f'  [AUTO-EDITOR] OK (thr {thr})')
                    return out, dur
        print('  [AUTO-EDITOR] n-a taiat -> fallback brut')
    return seg, clip_duration(seg) or (t1-t0)

def clip_duration(p):
    raw = subprocess.run([FF,'-y','-loglevel','error','-i',p,'-ar','44100','-ac','1','-f','f32le','-'], capture_output=True)
    n = len(raw.stdout) // 4
    return n/44100 if n > 0 else None

_WH = None
def release_whisper():
    import gc; gc.collect()


def whisper_words(clip, lang='ro'):
    """Re-transcrie pe clipul TAiat de auto-editor -> timpii deja in timeline."""
    from faster_whisper import WhisperModel
    raw = subprocess.run([FF,'-y','-loglevel','error','-i',clip,'-ar','16000','-ac','1','-f','f32le','-'], capture_output=True)
    a = np.frombuffer(raw.stdout, dtype=np.float32)
    global _WH
    if _WH is None:
        import os as _os
                try:
            _tot = _os.sysconf('SC_PAGE_SIZE') * _os.sysconf('SC_PHYS_PAGES') / 1e9
            _def = 'small' if _tot > 5 else 'tiny'
        except Exception:
            _def = 'tiny'
        _WH = WhisperModel(_os.environ.get('WHISPER_MODEL', _def), device='cpu', compute_type='int8')
    segs, info = _WH.transcribe(a, language=lang, word_timestamps=True, beam_size=5)
    FIX = {'reu':'cred','reu,':'cred','li-e':'nu-i'}
    out = []
    for sgm in segs:
        for w in sgm.words:
            t = w.word.strip().strip(',.!?…')
            if t in FIX: t = FIX[t]
            if not t: continue
            if t.startswith('-') and out:
                out[-1]['w'] += t; out[-1]['e'] = round(w.end,2); continue
            if len(t) == 1 and t.lower() not in 'aeiouăîâ': continue
            out.append({'w': t, 's': round(w.start,2), 'e': round(w.end,2)})
    return out

def detect_fail(src, segs):
    """Timpi (timeline) cu CADERE brusca de energie = fail/oh nu! in joc -> metal_pipe/boowomp."""
    chunks = []
    for sg,e in segs:
        raw = subprocess.run([FF,'-y','-loglevel','error','-ss',str(sg),'-t',str(e-sg),'-i',src,
                              '-ar','8000','-ac','1','-f','f32le','-'], capture_output=True)
        chunks.append(np.frombuffer(raw.stdout, dtype=np.float32))
    a = np.concatenate(chunks) if chunks else np.zeros(1, dtype=np.float32)
    wl = int(0.1*8000); m = len(a)//wl
    if m < 10: return []
    rms = np.array([np.sqrt((a[i*wl:(i+1)*wl]**2).mean()) for i in range(m)])
    fails = []
    for i in range(3, m-2):
        before = rms[max(0,i-3):i].mean()
        after  = rms[i:i+2].mean()
        if before > 0.08 and after < before*0.35:
            t = i*0.1
            if not fails or t - fails[-1] > 1.5: fails.append(t)
    return fails[:2]

# ---------- cuvinte ----------
def load_words(jsfile, key, fixes=None, drop=()):
    ws = json.load(open(jsfile))[key]['words']
    out = []
    for w in ws:
        t = w['w'].strip()
        if fixes and t in fixes: t = fixes[t]
        if not t or t in drop or set(t) == {'.'}: continue
        out.append({'w': t, 's': w['s'], 'e': w['e']})
    merged = []
    for w in out:
        if w['w'].startswith('-') and merged:
            merged[-1]['w'] += w['w']; merged[-1]['e'] = w['e']
        else: merged.append(w)
    for w in merged: w['w'] = w['w'].rstrip(',.').strip()
    return [w for w in merged if w['w']]


def word_energies(src, words, sr=8000):
    """RMS-ul vocii pe intervalul fiecarui cuvant -> inteligenta: ghiceste cuvintele-putere."""
    raw = subprocess.run([FF,'-y','-loglevel','error','-i',src,'-ar',str(sr),'-ac','1','-f','f32le','-'],
                         capture_output=True)
    a = np.frombuffer(raw.stdout, dtype=np.float32)
    def rms(t0, t1):
        i0, i1 = int(t0*sr), max(int(t1*sr), int(t0*sr)+1)
        seg = a[min(i0,len(a)-1):min(i1,len(a))]
        return float(np.sqrt((seg**2).mean())) if len(seg) else 0.0
    return {w['w']: rms(w['s'], w['e']) for w in words}


def find_best_window(src, win=12.0, hop=0.5):
    """Gaseste fereastra cu cea mai mare energie (actiune/reactie) intr-un clip lung."""
    sr = 8000
    raw = subprocess.run([FF,'-y','-loglevel','error','-i',src,'-ar',str(sr),'-ac','1','-f','f32le','-'], capture_output=True)
    a = np.frombuffer(raw.stdout, dtype=np.float32)
    dur = len(a)/sr
    if dur <= win: return (0.0, dur)
    w = int(win*sr); best, bi = 0.0, 0
    for i in range(0, len(a)-w, int(hop*sr)):
        e = float(np.sqrt((a[i:i+w]**2).mean()))
        if e > best: best, bi = e, i
    return (bi/sr, bi/sr+win)

def auto_segments(src, t0, t1, min_gap=0.30, pad=0.09, thresh_frac=0.16):
    """Tunde liniile/golurile: intoarce intervalele pastrate [(s,e)] in timp absolut.
    Ritmul 'ca la ei': zero secunde moarte."""
    sr = 8000
    raw = subprocess.run([FF,'-y','-loglevel','error','-ss',str(t0),'-t',str(t1-t0),'-i',src,
                          '-ar',str(sr),'-ac','1','-f','f32le','-'], capture_output=True)
    a = np.frombuffer(raw.stdout, dtype=np.float32)
    n = len(a); wl = int(0.05*sr)
    if n < wl*4: return [(t0, t1)]
    m = n//wl
    rms = np.array([np.sqrt((a[i*wl:(i+1)*wl]**2).mean()) for i in range(m)])
    p25 = float(np.percentile(rms, 25))
    thr = max(p25*1.5, 1e-5)   # prag calibrat: linistea = sub 1.5x p25
    quiet = rms < thr
    gaps = []
    i = 0
    while i < m:
        if quiet[i]:
            j = i
            while j < m and quiet[j]: j += 1
            if (j-i)*0.05 >= min_gap: gaps.append((i*0.05, j*0.05))
            i = j
        else: i += 1
    keeps = []; cur = 0.0
    for gs, ge in gaps:
        if gs - cur > 0.2: keeps.append((t0+cur, t0+min(gs+pad, gs)))
        cur = max(cur, ge-pad)
    if t1-t0-cur > 0.2: keeps.append((t0+cur, t1))
    keeps = [(s,e) for s,e in keeps if e-s > 0.25]
    total = sum(e-s for s,e in keeps)
    if len(keeps) > 12 or total < 0.5*(t1-t0):   # fallback: prea agresiv
        return auto_segments(src, t0, t1, min_gap=min_gap+0.25, thresh_frac=thresh_frac*0.7)
    return keeps or [(t0, t1)]

def map_time(t, segs):
    """timp in sursa -> timp in timeline comprimat."""
    acc = 0.0
    for s,e in segs:
        if t <= s: return acc
        if t <= e: return acc + (t-s)
        acc += e-s
    return acc

def group_lines(words, maxw=3, gap=0.55):
    lines, cur = [], []
    for w in words:
        if cur and (len(cur) >= maxw or w['s'] - cur[-1]['e'] > gap):
            lines.append(cur); cur = []
        cur.append(w)
    if cur: lines.append(cur)
    return lines

def shift_words(lines, dt):
    for line in lines:
        for w in line: w['s'] -= dt; w['e'] -= dt
    return lines

# ---------- randare text PNG ----------
def _font(sz): return ImageFont.truetype(FONT, sz)

def line_img(tokens, active_i=-1, base_sz=64):
    """tokens: [(text, role)]. -> PNG 1080x240. Layout pe SLOTURI: fiecare cuvant
    primeste un slot de latime fixa (latimea lui scalata), desenat centrat in slot."""
    img = Image.new('RGBA', (W, 240), (0,0,0,0))
    d = ImageDraw.Draw(img)
    sp = 18
    metas = []
    for t, role in tokens:
        # STIL JH (ordonat, zero miscare): marime FIXA, doar culoarea + grosimea conturului vorbesc
        if role == 'punch':      col, sw = (255,45,35,255), 11   # rosu viu = cuvant-putere
        elif role == 'active':   col, sw = (255,255,255,255), 12  # alb = cuvantul vorbit ACUM
        else:                    col, sw = (255,230,0,255), 9     # galben saturat = restul
        metas.append((t, col, sw))
    fb = _font(base_sz)
    slot_w = [d.textlength(t, font=fb) for t,_,_ in metas]   # sloturi FIXE
    tw = sum(slot_w) + sp*(len(metas)-1)
    x = max(10,(W - tw)/2)
    for (t, col, sw), wslot in zip(metas, slot_w):
        d.text((x + wslot/2, 120), t, font=fb, fill=col, anchor='mm',
               stroke_width=sw, stroke_fill=(0,0,0,255))
        x += wslot + sp
    return img

def render_caption_pngs(lines, outdir, punch_set=()):
    os.makedirs(outdir, exist_ok=True)
    pngs = []  # (path, line)
    n = 0
    for line in lines:
        for wi in range(len(line)):
            def role(k, w):
                if k == wi: return 'active'
                if w['w'].lower() in punch_set: return 'punch'
                return 'past' if k < wi else 'future'
            tokens = [role(k, w) and (w['w'].upper(), role(k, w)) for k, w in enumerate(line)]
            p = f'{outdir}/cap_{n:02d}.png'; n += 1
            line_img(tokens, wi).save(p)
            pngs.append((p, line, wi))
    return pngs

def render_text_png(text, color, sz, out, popout=False):
    if not popout:
        img = Image.new('RGBA', (W, 260), (0,0,0,0))
        d = ImageDraw.Draw(img)
        f = _font(sz)
        d.text((W/2, 130), text.upper(), font=f, fill=color, anchor='mm',
               stroke_width=10, stroke_fill=(0,0,0,255))
        img.save(out)
        return
    # POP-OUT JH: badge ALB rotit cu text VIU, umbra dura (ca elementele care ies din video la el)
    f = _font(sz)
    tmp = Image.new('RGBA', (W, 320), (0,0,0,0))
    d = ImageDraw.Draw(tmp)
    tw = d.textlength(text.upper(), font=f)
    pad = 34
    bw, bh = int(tw+pad*2), int(sz+70)
    badge = Image.new('RGBA', (bw, bh), (0,0,0,0))
    bd = ImageDraw.Draw(badge)
    bd.rounded_rectangle([0,0,bw-1,bh-1], 26, fill=(255,255,255,255), outline=(0,0,0,255), width=8)
    bd.text((bw/2, bh/2), text.upper(), font=f, fill=color, anchor='mm')
    badge = badge.rotate(-4, expand=True)
    # umbra dura offset
    sh = Image.new('RGBA', badge.size, (0,0,0,0))
    alpha = badge.split()[3].point(lambda a: 140 if a>0 else 0)
    black = Image.new('RGBA', badge.size, (0,0,0,255)); black.putalpha(alpha)
    tmp.paste(black, (W//2-badge.width//2+10, 160-badge.height//2+12), black)
    tmp.paste(badge, (W//2-badge.width//2, 160-badge.height//2), badge)
    tmp.save(out)

def render_cta_png(text, out):
    img = Image.new('RGBA', (W, 120), (0,0,0,0))
    d = ImageDraw.Draw(img)
    f = _font(46)
    tw = d.textlength(text.upper(), font=f)
    d.rounded_rectangle([(W-tw)/2-24, 8, (W+tw)/2+24, 112], 18, fill=(200,20,20,235))
    d.text((W/2, 60), text.upper(), font=f, fill=(255,255,255,255), anchor='mm')
    img.save(out)

def make_logo_overlay(logo_path, out, maxw=280, maxh=160):
    logo = Image.open(logo_path).convert('RGBA')
    logo.thumbnail((maxw, maxh), Image.LANCZOS)
    sh = Image.new('RGBA', (logo.width+24, logo.height+24), (0,0,0,0))
    mask = logo.split()[3].point(lambda a: min(a,190))
    black = Image.new('RGBA', logo.size, (0,0,0,255)); black.putalpha(mask)
    sh.paste(black, (12,12), black)
    sh = sh.filter(ImageFilter.GaussianBlur(5))
    sh.paste(logo, (12,12), logo)
    sh.save(out)

# ---------- audio ----------
def _read_wav(p):
    with wave.open(p,'rb') as w:
        a = np.frombuffer(w.readframes(w.getnframes()), dtype='<i2').astype(np.float32)/32767
        if w.getnchannels()==2: a = a[0::2]+a[1::2]
    return a

def mix_audio(src, segs, dur, out, pops=(), booms=(), whooshes=(), riser_at=None,
              drone_gain=0.10, pop_gain=0.20):
    chunks = []
    for sg,e in segs:
        raw = subprocess.run([FF,'-y','-loglevel','error','-ss',str(sg),'-t',str(e-sg),'-i',src,
                              '-ar','44100','-ac','1','-f','f32le','-'], capture_output=True)
        chunks.append(np.frombuffer(raw.stdout, dtype=np.float32))
    voice = np.concatenate(chunks) if chunks else np.zeros(1, dtype=np.float32)
    n = int(dur*44100)
    voice = np.pad(voice, (0, max(0, n-len(voice))))[:n]
    mix = voice.copy()
    def put(name, t, gain):
        sig = _read_wav(f'{PRO}/{name}.wav')
        i = int(t*44100); m = min(len(sig), n-i)
        if m > 0: mix[i:i+m] += sig[:m]*gain
    drone = _read_wav(f'{PRO}/drone.wav')
    dr = np.tile(drone, int(math.ceil(n/len(drone))))[:n]
    cenv = np.convolve(np.abs(voice), np.ones(2205)/2205, 'same')
    duck = 1.0 - np.clip(cenv/max(cenv.max(),1e-9)*0.8, 0, 0.8)
    mix += dr*drone_gain*duck
    for t in whooshes: put('whoosh', t, 0.55)
    for t,g in booms:  put('boom', t, g)
    for t in pops:     put('pop', t, pop_gain)
    if riser_at is not None: put('riser', riser_at, 0.5)
    peak = np.abs(mix).max()
    if peak > 0.98: mix *= 0.98/peak
    with wave.open(out,'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(44100)
        w.writeframes((np.clip(mix,-1,1)*32767).astype('<i2').tobytes())

# ---------- video ----------
def make_bg(src, t=1.0, out='/tmp/_bg.jpg', blur=22, dim=0.82):
    subprocess.run([FF,'-y','-loglevel','error','-ss',str(t),'-i',src,'-frames:v','1',out])
    im = Image.open(out).convert('RGB')
    r = 1936/im.height
    im = im.resize((int(im.width*r),1936), Image.LANCZOS)
    x = (im.width-1108)//2
    im = im.crop((x,0,x+1108,1936)).filter(ImageFilter.GaussianBlur(blur))
    from PIL import ImageEnhance
    im = ImageEnhance.Brightness(im).enhance(dim)
    im.save(out, quality=85)

def render_body(src, out, segs, fg_y=600):
    parts = []
    for i,(sg,e) in enumerate(segs):
        parts.append(f"[0:v]trim={sg}:{e},setpts=PTS-STARTPTS,fps=30,scale=1030:-2[p{i}]")
    conc = ''.join(f"[p{i}]" for i in range(len(segs)))
    fl = ';'.join(parts) + f";{conc}concat=n={len(segs)}:v=1:a=0[vc];[bgv][vc]overlay=(1108-w)/2:{fg_y}[p]"
    subprocess.run([FF,'-y','-loglevel','error','-i',src,'-loop','1','-t',f'{sum(e-s for s,e in segs)+0.5}','-i','/tmp/_bg.jpg',
        '-filter_complex', f"[1:v]scale=1108:1936[bgv];{fl}",
        '-map','[p]','-an','-c:v','libx264','-crf','19','-preset','veryfast','-pix_fmt','yuv420p','-r','30',out])
    return sum(e-s for s,e in segs)


def probe_dims(p):
    import re as _re
    r = subprocess.run([FF,'-y','-loglevel','info','-i',p], capture_output=True, text=True)
    m = _re.search(r'Stream #0:0.*?(\d{2,5})x(\d{2,5})', r.stderr)
    return (int(m.group(1)), int(m.group(2))) if m else (1108, 1936)

def render_overlays(body, out, total, overlays, logo_ov=None, shake_hits=(), cap_pngs=None, fps=30):
    """STREAMING: decodeaza body frame-cu-frame, aplica shake (crop mobil), paste overlay-uri
    active la timpul t, si encoda. Memorie constanta, fara zeci de input-uri ffmpeg."""
    Wf, Hf = 1080, 1920
    cmd_in = [FF,'-y','-loglevel','error','-i',body,'-f','rawvideo','-pix_fmt','rgb24','-']
    cmd_out = [FF,'-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{Wf}x{Hf}','-r',str(fps),'-i','-',
               '-an','-c:v','libx264','-crf','19','-preset','fast','-pix_fmt','yuv420p','-r',str(fps),out]
    p_in = subprocess.Popen(cmd_in, stdout=subprocess.PIPE)
    p_out = subprocess.Popen(cmd_out, stdin=subprocess.PIPE)
    ovl = [(Image.open(p).convert('RGBA'), y, t0, t1) for p,y,t0,t1 in overlays]
    if logo_ov:
        ovl.insert(0, (Image.open(logo_ov).convert('RGBA'), 30, 0.0, total))
    cap_pos = 1180   # JH-Sky style: JOS-centru (deasupra(actions)), mereu vizibil
    if cap_pngs:
        for p, line, wi in cap_pngs:
            t0 = max(0.0, line[wi]['s']-0.02); t1 = line[wi]['e']+0.02
            ovl.append((Image.open(p).convert('RGBA'), cap_pos, t0, t1))
    frame = 0
    fw, fh = probe_dims(body)          # dimensiunile REALE ale body-ului
    fsz = fw*fh*3
    while True:
        buf = p_in.stdout.read(fsz)
        if len(buf) < fsz: break
        t = frame/float(fps)
        dx = dy = 0.0
        for st, a in shake_hits:
            if t >= st:
                e = math.exp(-9*(t-st))
                dx += a*e*math.sin(55*(t-st)); dy += a*0.6*e*math.cos(47*(t-st))
        dx = int(max(0, min(fw-Wf-1, (fw-Wf)//2+dx))); dy = int(max(0, min(fh-Hf-1, (fh-Hf)//2+dy)))
        im = Image.frombuffer('RGB', (fw, fh), buf, 'raw', 'RGB', 0, 1).crop((dx,dy,dx+Wf,dy+Hf))
        for png, y, t0, t1 in ovl:
            if t0 <= t <= t1:
                im.paste(png, (0, y), png)
        p_out.stdin.write(im.tobytes())
        frame += 1
    p_in.stdout.close(); p_out.stdin.close()
    p_in.wait(); p_out.wait()

def mux(vid, wav, out):
    subprocess.run([FF,'-y','-loglevel','error','-i',vid,'-i',wav,'-c:v','copy','-c:a','aac','-b:a','160k',
                    '-movflags','+faststart','-shortest',out])

def build(src, out, words, hook_text=None, cta_text=None, logo_path=None, trim=None,
          fixes=None, drop=(), punch_words=None, big_finale=None,
          bg_t=1.0, outdir='/tmp/_pro', kit_out=None, title_hint='', compress=True, series=None):
    """v5 AUTOPILOT + AUTO-PACING: taie linistea, hook/punch/big auto din energia vocii.
    series='pokecity' -> pune logo-ul seriei; altfel FARA logo (niciodata degeaba)."""
    os.makedirs(outdir, exist_ok=True)
    if trim is None: trim = (0.0, 9.8)
    src_eff = src
    # ---------- 1) AUTO-EDITOR (5.4K stars): taie linistea inteligent ----------
    segs = None
    if compress:
        cut_path, cut_dur = autocut_autoeditor(src, trim[0], trim[1])
        try:
            words = whisper_words(cut_path)
            release_whisper()
            src_eff = cut_path
            segs = [(0.0, cut_dur)]
            print('  [AUTO-EDITOR] %.1fs -> %.1fs (motor WyattBlue)' % (trim[1]-trim[0], cut_dur))
        except Exception as ex:
            print('  [AUTO-EDITOR] whisper refacut a picat (%s) -> fallback RMS' % ex)
            segs = auto_segments(src, trim[0], trim[1])
            for w in words:
                w['s'] = map_time(w['s'], segs); w['e'] = map_time(w['e'], segs)
            words = [w for w in words if w['e'] > w['s']]
    else:
        segs = [trim]
    total = sum(e-s for s,e in segs)
    # ---------- 2) energie + punch (pe sursa efectiva) ----------
    en = word_energies(src_eff, words)
    vals = sorted(en.values()); med = vals[len(vals)//2] if vals else 0
    mx = max(en.values()) if en else 0
    auto = [w for w,v in en.items() if v > max(med*1.45, 1e-9)]
    auto.sort(key=lambda w: -en[w])
    pw = set(punch_words or []) | {w.lower() for w in auto[:3]}
    pw |= {w.lower() for w in sorted(en.keys(), key=lambda w: -en[w])[:2]}
    if hook_text is None:
        hook_text = ' '.join(w['w'] for w in words[:4]).upper() or 'PRIVESTE!'
    lines = shift_words(group_lines(words), 0.0)
    # ---------- 3) assets ----------
    make_bg(src_eff, bg_t)
    render_body(src_eff, '/tmp/_body.mp4', segs)
    logo_ov = None
    if logo_path and series:   # LOGO DOAR la seria adevarata!
        logo_ov = f'{outdir}/logo_ov.png'; make_logo_overlay(logo_path, logo_ov)
    hook_png = None
    if hook_text:
        hook_png = f'{outdir}/hook.png'
        render_text_png(hook_text, (255,230,0,255), 96, hook_png)
    # ---------- 4) BIG auto ----------
    punches = sorted([w for w in words if w['w'].lower() in pw], key=lambda w: w['s'])
    if big_finale is None and punches:
        cand = [w for w in punches if en.get(w['w'],0) >= mx*0.70 and (w['e']-w['s']) < 1.3]
        if cand:
            top = max(cand, key=lambda w: en[w['w']])
            big_finale = (top['w'].upper(), max(0,top['s']-0.05), min(total, top['e']+0.75))
    # ---------- 5) overlays ----------
    overlays = [(hook_png, 150, 0.0, 2.1)] if hook_png else []
    if cta_text:
        cta_png = f'{outdir}/cta.png'; render_cta_png(cta_text, cta_png)
        overlays.append((cta_png, 1700, max(0,total-2.2), total))
    if big_finale:
        bp = f'{outdir}/big.png'; render_text_png(big_finale[0], (255,45,35,255), 110, bp, popout=True)
        overlays.append((bp, 700, big_finale[1], big_finale[2]))
    like_png = f'{outdir}/like.png'; render_cta_png('DA UN LIKE!', like_png)
    overlays.append((like_png, 1690, 0.0, 2.0))
    # ---------- 6) captions ----------
    caps = render_caption_pngs(lines, outdir, punch_set=pw)
    if big_finale:
        caps = [c for c in caps if not (c[1][-1]['e'] > big_finale[1]-0.05 and c[1][0]['s'] < big_finale[2]+0.05)]
    # ---------- 7) sunet ----------
    pops = [w['s'] for w in words if w['s'] > 0.05]
    shake = [(0.12, 12)] + [(w['s'], 14) for w in punches]
    shake = [(t,a) for t,a in shake if 0 <= t < total]
    booms = [(0.12, 0.9)] + ([(punches[0]['s'], 1.0)] if punches else [])
    riser = (punches[0]['s']-1.3) if punches and punches[0]['s'] > 2 else None
    fails = detect_fail(src_eff, segs)
    for ft in fails:
        if not (punches and abs(ft-punches[0]['s']) < 0.8):
            mix_audio_extra = None  # placeholder semnificatie
    # sunet inteligent: metal_pipe pe failuri (caderi de energie = fail in joc)
    extra_booms = [(ft, 0.8) for ft in fails if not (punches and abs(ft-punches[0]['s']) < 0.8)]
    mix_audio(src_eff, segs, total, '/tmp/_mix.wav', pops=pops, booms=booms+extra_booms, whooshes=[0.0], riser_at=riser)
    print('  [SFX] fail-detect:', fails if fails else '-')
    # ---------- 8) randare + kit ----------
    print('  [AUTO] hook=%r punch=%s big=%s | pacing: %.1fs -> %.1fs (%d busteni)' % (
        hook_text, sorted(pw), big_finale[0] if big_finale else None, trim[1]-trim[0], total, len(segs)))
    render_overlays('/tmp/_body.mp4', '/tmp/_vid.mp4', total, overlays, logo_ov, shake, caps)
    mux('/tmp/_vid.mp4', '/tmp/_mix.wav', out)
    if kit_out:
        base = (title_hint or hook_text).title()
        kit = ('TITLU (formula cliffhanger ca la ei): ' + base + '...\n'
               '  alternativ: ' + base.upper() + ' ?! #shorts\n\n'
               'DESCRIERE:\n' + hook_text.capitalize() + '!\n'
               'Scrii in comentarii ce ar fi facut in locul meu!\n'
               '#shorts #gamingromania #romania\n\n'
               'POSTARE: 18:00-20:00 | 48h fara modificari')
        open(kit_out, 'w').write(kit)
        print('  [AUTO] kit salvat:', kit_out)
    return total

if __name__ == '__main__':
    # SHORT NOU: M2 - momentul "HAI N-O ROG CA N-AM ACCES!" (setup trolling -> disperare)
    words = load_words(os.path.join(BASE,'whisper_momente.json'), '2', drop=('...',))
    t = build('/home/user/momente/MOMENT_2.mp4', os.path.join(BASE,'SHORT_M2_ACCES.mp4'),
              words, trim=(3.0, 9.9), compress=True,
              hook_text='CA N-AM ACCES!',
              punch_words=('acces','rog'),
              kit_out=os.path.join(BASE,'KIT_M2.txt'), title_hint='N-AM ACCES LA JOC')
    print('GATA', t, 's')
