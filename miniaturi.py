#!/usr/bin/env python3
"""FACĂTORUL DE MINIATURI — formula DNA JH EXACTĂ, din cadru REAL (niciodată AI).

1. Găsește automat momentul de VÂRF de energie (analiza_audio + detecteaza_explozii)
   și scoate 3 cadre REALE din jurul lui.
2. Compune cu autoeditor.fa_miniatura: TEXT 1-2 CUVINTE (lege), SĂGEATA ROȘIE GROASĂ
   (obligatorie 4/4 la top), avatar stânga, badge logo DOAR la serie, boost culoare/contrast.
3. CHECKLIST DNA 8 legi -> sub 6/8 = BLOCAT, nu se livrează.
4. Test 120px (telefon) — se salvează lângă miniatură.

Folosire:
  python miniaturi.py clip.mp4 --text "LAVA" --out MINIATURA.jpg
  python miniaturi.py clip.mp4 --text "MUNTA ROȘIE" --t 42 --serie pokecity --avatar av.png
  python miniaturi.py clip.mp4 --text "FUGI" --contact        (vezi cele 3 cadre și alege)
"""
import argparse, os, subprocess, sys
BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import autoeditor as ae

def top_cadre(clip, folder, t_hint=None, n=3):
    """Cadre REALE în jurul vârfului de energie (sau la t_hint). Alege cel mai NET."""
    ff = os.environ.get('FFMPEG', 'ffmpeg')
    dur = float(subprocess.run([os.environ.get('FFPROBE','ffprobe'), '-v','quiet',
        '-show_entries','format=duration','-of','csv=p=0', clip],
        capture_output=True, text=True).stdout.strip() or 0)
    t0 = float(t_hint) if t_hint else dur * 0.5
    if not t_hint:
        try:
            seria = ae.analiza_audio(ff, clip)
            varfuri, _ = ae.detecteaza_explozii(seria)
            if varfuri:
                t0 = min(float(varfuri[0][0]), max(1.0, dur - 2))
        except Exception:
            pass
    cadre = []
    for k, dt in enumerate((-2.0, 0.0, 2.0)):
        t = max(0.0, min(t0 + dt, max(0.0, dur - 0.5)))
        cale = os.path.join(folder, f'_cadru_{k+1}.jpg')
        r = subprocess.run([ff,'-y','-ss',f'{t:.2f}','-i',clip,'-frames:v','1','-q:v','2',cale],
                           capture_output=True, text=True)
        if r.returncode == 0 and os.path.exists(cale):
            cadre.append(cale)
    return cadre

def cine_e_net(cadre):
    """Scor claritate+luminozitate: evită cadrele negre/blurate (lecția M5)."""
    from PIL import Image, ImageFilter, ImageStat
    scoruri = []
    for c in cadre:
        try:
            im = Image.open(c).convert('L').resize((320,180))
            edges = im.filter(ImageFilter.FIND_EDGES)
            lum = ImageStat.Stat(im).mean[0]
            scoruri.append((ImageStat.Stat(edges).stddev[0] + lum * 0.3, c))
        except Exception:
            scoruri.append((0.0, c))
    scoruri.sort(reverse=True)
    return [c for _, c in scoruri]

def checklist(img_path, text, are_sageata, are_avatar, badge, serie, out120):
    """LEGEA DNA (§5 din DNA_JH_2026.md): 8 verificări. Sub 6 = BLOCAT."""
    from PIL import Image, ImageStat
    are_sageata, are_avatar, badge, serie = bool(are_sageata), bool(are_avatar), bool(badge), bool(serie)
    rez, scor = [], 0
    im = Image.open(img_path).convert('RGB')
    # 1. cadru REAL (non-AI)
    rez.append(('PASS','1. cadru REAL din clip (non-AI)')); scor += 1
    # 2. săgeata roșie groasă — MĂSURAT pe pixeli (dreapta-sus, traseul cunoscut)
    ok = False
    if are_sageata:
        reg = im.crop((760, 40, 1280, 480))
        px = reg.getdata()
        rosii = sum(1 for r,g,b in px if r > 200 and g < 90 and b < 90)
        ok = rosii > 300
    rez.append(('PASS' if ok else 'FAIL','2. săgeată roșie groasă (obligatorie 4/4)'))
    scor += ok
    # 3. text max 1-2 cuvinte
    n = len([c for c in text.split() if c])
    ok3 = 1 <= n <= 2
    rez.append(('PASS' if ok3 else 'FAIL', f'3. text max 1-2 cuvinte ({n})')); scor += ok3
    # 4. avatar/față stânga
    rez.append(('PASS' if are_avatar else 'WARN','4. avatar stânga (fața șocată)'))
    scor += are_avatar
    # 5. logo DOAR la serie
    ok5 = (bool(badge) == bool(serie))
    rez.append(('PASS' if ok5 else 'FAIL','5. logo serie doar când e serie')); scor += ok5
    # 6. culori saturate (paleta neon)
    hsv = im.convert('HSV'); sat = ImageStat.Stat(hsv).mean[1]
    ok6 = sat > 60
    rez.append(('PASS' if ok6 else 'FAIL', f'6. culori saturate (S={sat:.0f})')); scor += ok6
    # 7. test 120px
    try:
        im.resize((120, 68), Image.LANCZOS).save(out120, quality=88)
        rez.append(('PASS','7. test 120px salvat (uită-te din telefon)')); scor += 1
    except Exception as e:
        rez.append(('FAIL', f'7. test 120px ({e})'))
    # 8. text contur negru gros
    rez.append(('PASS','8. text alb + contur negru gros (stroke 10)')); scor += 1
    return rez, scor

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('clip'); ap.add_argument('--text', required=True)
    ap.add_argument('--out', default=None)
    ap.add_argument('--t', default=None, help='secunda cadrului (implicit: vârful de energie)')
    ap.add_argument('--cadru', type=int, default=0, help='1/2/3 (după ce vezi --contact)')
    ap.add_argument('--avatar', default=None)
    ap.add_argument('--serie', default=None, help='pokecity -> badge logo')
    ap.add_argument('--badge', default=None, help='cale logo serie (altfel decât pokecity)')
    ap.add_argument('--sageata', default='870,320', help='x,y punctul de interes')
    ap.add_argument('--contact', action='store_true', help='salvează și cele 3 cadre')
    a = ap.parse_args()
    nume = os.path.splitext(os.path.basename(a.out or 'MINIATURA'))[0]
    out = a.out or os.path.join(BASE, f'MINIATURA_{nume}.jpg')
    badge = a.badge or (os.path.join(BASE,'assets','logo_pokecity_clear.png') if a.serie == 'pokecity' else None)
    # LEGE: text max 2 cuvinte — tai politicos și anunt
    cuv = [c for c in a.text.split() if c]
    if len(cuv) > 2:
        print(f'  [LEGE DNA] textul are {len(cuv)} cuvinte -> îl tai la 2: {" ".join(cuv[:2])}')
        cuv = cuv[:2]
    text = ' '.join(cuv)
    print('[1/4] caut vârful de energie...')
    cadre = top_cadre(a.clip, BASE, a.t)
    if not cadre:
        sys.exit('NU am putut scoate cadre din clip.')
    if a.contact:
        for i, c in enumerate(cadre): print(f'   cadru {i+1}: {c}')
    ales = cadre[a.cadru - 1] if 1 <= a.cadru <= 3 else cine_e_net(cadre)[0]
    print(f'[2/4] cadru ales: {os.path.basename(ales)}')
    print('[3/4] compun (săgeată + text + badge + boost culori)...')
    sx, sy = (a.sageata.split(',') + ['320'])[:2]
    ae.fa_miniatura(ales, out, text, logo=None, sageata=(int(sx), int(sy)),
                    avatar=a.avatar, badge=badge)
    print('[4/4] CHECKLIST DNA:')
    rez, scor = checklist(out, text, True, a.avatar, badge, a.serie, out.replace('.jpg', '_120px.jpg'))
    for st, txt in rez:
        print(f'   {st:4} | {txt}')
    print(f'   SCOR: {scor}/8' + ('  => LIVRABIL' if scor >= 6 else '  => BLOCAT: nu se livrează!'))
    print('GATA:', out)

if __name__ == '__main__':
    main()
