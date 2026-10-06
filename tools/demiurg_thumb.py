#!/usr/bin/env python3
"""DEMIURG THUMB — AI-ul de brand automat (o comanda, thumbnail gata).

  1) CAUTA (alegerea inteligenta):
     python tools/demiurg_thumb.py cauta "bebe dragon in minecraft" --joc minecraft
     -> scaneaza canalele campionilor, alege viralul cel mai potrivit temei,
        descarca thumbnail-ul de referinta si scrie PROMPT_GENERARE.txt (gata de swap).

  2) FINALIZEAZA (stratul uman de brand):
     python tools/demiurg_thumb.py finalizeaza scena.png --out THUMB.jpg \
        --bula "FUGI!" --bula_xy 640:120 --ntag "Mocivanu:330:40" --ntag "iZentric:950:40" \
        --cerc 640:420:150 --sageata 60:60:600:340 --inimi 640:200 --logo pokecity --test120
     -> aplica elementele_brand (PNG oficiale) + finisaj "editat de om" + test 120px.
"""
import argparse, csv, json, math, os, subprocess, sys, time
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
ELEM = os.path.join(BASE, 'elemente_brand')
KB   = os.path.join(BASE, 'cunostinte', 'scan_canale_Minecraft.csv')
ANTON = os.path.join(BASE, 'assets', 'Anton.ttf')
MONO = os.environ.get('MONOCRAFT', '/home/user/autoeditor/assets/Monocraft.ttc')

CANALE_MC = {
    '@dagar-minecraft':  'https://www.youtube.com/@dagar-minecraft/videos',
    '@nacho-minecraft':  'https://www.youtube.com/@nacho-minecraft/videos',
    '@CadresPlayer':     'https://www.youtube.com/@CadresPlayer/videos',
    '@PlayzKnoxy':       'https://www.youtube.com/@PlayzKnoxy/videos',
}
STOP = {'in','the','a','si','de','la','cu','pe','un','o','ce','sa','mi','meu','ma','am','for','of'}

def scan_sau_refresh():
    os.makedirs(os.path.dirname(KB), exist_ok=True)
    if os.path.exists(KB) and (time.time() - os.path.getmtime(KB)) < 7*86400:
        return KB
    randuri = []
    for ch, url in CANALE_MC.items():
        r = subprocess.run(['yt-dlp','--flat-playlist','--print','%(id)s|%(view_count)s|%(title)s', url],
                           capture_output=True, text=True)
        for lin in (r.stdout or '').splitlines():
            p = lin.split('|', 2)
            if len(p) == 3 and p[1].isdigit():
                randuri.append({'canal': ch, 'id': p[0], 'views': int(p[1]), 'titlu': p[2]})
    with open(KB, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['canal','id','views','titlu'])
        w.writeheader(); w.writerows(randuri)
    print(f'  [SCAN] {len(randuri)} video in baza de cunostinte')
    return KB

def cauta(tema, joc):
    import time
    cale = scan_sau_refresh()
    tema_c = [c for c in tema.lower().split()
              if c not in STOP and len(c) > 2 and c not in (a.joc if False else ('minecraft','roblox','gta','joc','jocul'))]
    best = None
    with open(cale, encoding='utf-8') as f:
        for row in csv.DictReader(f):
            row['views'] = int(row['views'])
            t = row['titlu'].lower()
            cuv_t = t.replace('!','.').replace('?','.').replace(',','.').split()
            scor = 0
            for c in tema_c:
                rad = c[:4]
                if c in t or any(w.startswith(rad) for w in cuv_t):
                    scor += 1
            punctaj = row['views'] * (1 + scor * 3)
            if best is None or punctaj > best[0]:
                best = (punctaj, row)
    if not best: sys.exit('baza goala — ruleaza iar')
    row = best[1]
    print(f"  [MATCH] {row['canal']} | {row['views']:,} views | potrivire tema | {row['titlu'][:60]}")
    ref = os.path.join(BASE, 'refs', f'REF_ales_{row["id"]}.jpg')
    for cal in ('maxresdefault', 'hqdefault'):
        r = subprocess.run(['curl','-s','-o',ref,f'https://i.ytimg.com/vi/{row["id"]}/{cal}.jpg'])
        if os.path.exists(ref) and os.path.getsize(ref) > 8000: break
    prompt = f"""[SWAP PE REFERINTA VIRALA — metoda validata]
Image A (referinta): refs/REF_ales_{row['id']}.jpg  ({row['views']:,} views, {row['canal']})
Image B (personajele noastre): refs/BRAND_THUMB_MASTER.png
Prompt: "Edit image 1. Replace the main characters with the two characters from image 2
(bear-like MC character with pink-white cap + boy with half black/white hair, red horns,
white yin-yang hoodie), redrawn in image 1's exact art style, same positions/sizes/poses.
Keep EVERYTHING else EXACTLY identical (background, lighting, composition, effects).
NO text, NO letters, NO bubbles, NO circles, NO arrows, NO nametags, NO logos."
TEMA bossului: {tema} (joc: {joc})"""
    with open(os.path.join(BASE, 'PROMPT_GENERARE.txt'), 'w', encoding='utf-8') as f:
        f.write(prompt)
    print('  [PROMPT] scris in PROMPT_GENERARE.txt — genereaza scena, apoi: finalizeaza')
    return ref

def _sah(w, h):
    img = Image.new('RGB', (w, h), (235,235,235)); d = ImageDraw.Draw(img)
    for y in range(0, h, 24):
        for x in range(0, w, 24):
            if (x//24+y//24) % 2: d.rectangle([x,y,x+23,y+23], fill=(208,208,208))
    return img

def finalizeaza(scena, out, bula, bula_xy, ntag, cerc, sageata, inimi, logo, test120):
    img = Image.open(scena).convert('RGB')
    if img.size != (1280, 720): img = img.resize((1280, 720), Image.LANCZOS)
    im = img.convert('RGBA'); d = ImageDraw.Draw(im)
    # nametag-uri (PNG oficiale)
    for spec in ntag or []:
        nume, xc, yt = spec.rsplit(':', 2)[0], int(spec.split(':')[1]), int(spec.split(':')[2])
        png = Image.open(os.path.join(ELEM, f'nametag_{nume}.png'))
        sc = 0.55; png = png.resize((int(png.width*sc), int(png.height*sc)), Image.LANCZOS)
        im.paste(png, (xc - png.width//2, yt - png.height//2), png)
    # cercul (PNG, scalat la raza ceruta)
    if cerc:
        p = cerc.split(':'); cx, cy = int(p[0]), int(p[1]); r = int(p[2]) if len(p) > 2 else 150
        cp = Image.open(os.path.join(ELEM, 'cerc_rosu.png'))
        cp = cp.resize((2*r, 2*r), Image.LANCZOS)
        im.paste(cp, (cx-r, cy-r), cp)
    # bula (PNG gol + text Anton rosu)
    if bula:
        txt = bula; bx, by = bula_xy
        bp = Image.open(os.path.join(ELEM, 'bula_GOLA.png')).resize((430, 239), Image.LANCZOS)
        im.paste(bp, (bx - 215, by - 140), bp)
        d = ImageDraw.Draw(im)
        ft = ImageFont.truetype(ANTON, 88)
        tb = d.textbbox((0,0), txt, font=ft, stroke_width=6)
        d.text((bx-(tb[2]-tb[0])//2-tb[0], by-15-(tb[3]-tb[1])//2-tb[1]), txt, font=ft,
               fill=(229,32,38,255), stroke_width=6, stroke_fill=(120,8,10,255))
    # sageata (procedural — directie libera)
    if sageata:
        p = [int(v) for v in sageata.split(':')]
        x0, y0, x1, y1 = p
        ROSU = (237, 28, 36)
        d.ellipse([x0-24, y0-24, x0+24, y0+24], fill=ROSU)
        d.line([x0, y0, x1, y1], fill=ROSU, width=48)
        ang = math.atan2(y1-y0, x1-x0)
        for da in (ang+2.45, ang-2.45):
            d.line([x1, y1, x1+int(170*math.cos(da)), y1+int(170*math.sin(da))], fill=ROSU, width=48)
    # inimioarele (PNG)
    if inimi:
        p = inimi.split(':'); ix, iy = int(p[0]), int(p[1])
        hq = Image.open(os.path.join(ELEM, 'inimi_rosii.png'))
        sc = 0.85; hq = hq.resize((int(hq.width*sc), int(hq.height*sc)), Image.LANCZOS)
        im.paste(hq, (ix - hq.width//2, iy - hq.height//2), hq)
    # logo de serie
    if logo:
        cale_logo = os.path.join(BASE, 'assets', 'logo_pokecity_clear.png') if logo == 'pokecity' else logo
        if os.path.exists(cale_logo):
            lg = Image.open(cale_logo).convert('RGBA'); lg.thumbnail((150, 150), Image.LANCZOS)
            im.paste(lg, (22, 720 - lg.height - 18), lg)
    fin = im.convert('RGB')
    fin = ImageEnhance.Color(fin).enhance(1.08)
    fin = ImageEnhance.Contrast(fin).enhance(1.05)
    fin = ImageEnhance.Sharpness(fin).enhance(1.22)
    fin.save(out, quality=93)
    if test120:
        fin.resize((120, 68), Image.LANCZOS).save(out.replace('.jpg', '_120px.jpg'), quality=88)
    print('BRAND APLICAT:', out)

def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    c = sub.add_parser('cauta'); c.add_argument('tema'); c.add_argument('--joc', default='minecraft')
    f = sub.add_parser('finalizeaza'); f.add_argument('scena'); f.add_argument('--out', required=True)
    f.add_argument('--bula', default=None); f.add_argument('--bula_xy', default='640:120')
    f.add_argument('--ntag', action='append', default=[])
    f.add_argument('--cerc', default=None); f.add_argument('--sageata', default=None)
    f.add_argument('--inimi', default=None); f.add_argument('--logo', default=None)
    f.add_argument('--test120', action='store_true')
    a = ap.parse_args()
    if a.cmd == 'cauta':
        cauta(a.tema, a.joc)
    else:
        bxy = tuple(int(v) for v in a.bula_xy.split(':'))
        finalizeaza(a.scena, a.out, a.bula, bxy, a.ntag, a.cerc, a.sageata, a.inimi, a.logo, a.test120)

if __name__ == '__main__':
    main()
