#!/usr/bin/env python3
"""THUMB BRAND COMPOSITOR — stratul UMAN peste scena (protocolul de brand).
Pune: nametag-uri Minecraft (PNG oficiale), bula cu text scurt, cercul rosu, sageata,
inimioarele, logo-ul seriei, finisaj "editat de om".
"""
import argparse, math, os, sys
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ELEM = os.path.join(BASE, 'elemente_brand')
ANTON = os.path.join(BASE, 'assets', 'Anton.ttf')
ROSU = (237, 28, 36)
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('scena'); ap.add_argument('--out', required=True)
    ap.add_argument('--ntag', action='append', default=[], help='Nume:x:y (PNG oficial)')
    ap.add_argument('--bula', default=None, help='TEXT:x:y (bula desenata cu fontul Anton)')
    ap.add_argument('--balon', default=None,
                    help='CALE:x:y:latime (PNG REAL 1:1 din biblioteca, ex. elemente_brand/BALON_JH_real_CE.png)')
    ap.add_argument('--cerc', default=None, help='x:y:r')
    ap.add_argument('--sageata', default=None, help='x0:y0:x1:y1')
    ap.add_argument('--inimi', default=None, help='x:y')
    ap.add_argument('--cerc-pe', default=None,
                    help='x0,y0,x1,y1[:CALE] — cercul lui se AUTO-CENTREAZA pe ce e de '
                         'aratat (fata/obiect). Nu-l mai pui la ochi, iese perfect.')
    ap.add_argument('--sageata-spre', default=None,
                    help='CALE:tx,ty:latime:colt(:stanga) — sageata LUI, din colt '
                         '(sj/dj/ss/ds) spre tinta; se roteste singura.')
    ap.add_argument('--pune', action='append', default=[],
                    help='CALE:x:y:latime — lipeste ORICE element 1:1 extras '
                         '(săgeată/cerc/semn din elemente_brand/JH/). Se poate repeta.')
    ap.add_argument('--logo', default=None, help='pokecity sau cale')
    ap.add_argument('--test120', action='store_true')
    a = ap.parse_args()
    img = Image.open(a.scena).convert('RGB')
    if img.size != (1280, 720): img = img.resize((1280, 720), Image.LANCZOS)
    im = img.convert('RGBA'); d = ImageDraw.Draw(im)
    if a.cerc:
        p = a.cerc.split(':'); cx, cy = int(p[0]), int(p[1]); r = int(p[2]) if len(p) > 2 else 150
        cp = Image.open(os.path.join(ELEM, 'cerc_rosu.png')).resize((2*r, 2*r), Image.LANCZOS)
        im.paste(cp, (cx-r, cy-r), cp)
    for spec in a.ntag or []:
        nume = spec.rsplit(':', 2)[0]; xc, yt = int(spec.split(':')[1]), int(spec.split(':')[2])
        png = Image.open(os.path.join(ELEM, f'nametag_{nume}.png'))
        png = png.resize((int(png.width*0.55), int(png.height*0.55)), Image.LANCZOS)
        im.paste(png, (xc - png.width//2, yt - png.height//2), png)
    if a.balon:
        # Element REAL 1:1 (legea bossului: copiaza, nu redesena) — ex. balonul JH cu „CE?".
        b = a.balon.rsplit(':', 3)
        cale, bx, by, lat = b[0], int(b[1]), int(b[2]), int(b[3])
        bp = Image.open(cale).convert('RGBA')
        # regula bossului: bula stă LÂNGĂ caracter (nu pe față), cu coada întoarsă spre el
        if len(b) > 4 and b[4] == 'stanga':
            bp = bp.transpose(Image.FLIP_LEFT_RIGHT)
        bp = bp.resize((lat, int(bp.height * lat / bp.width)), Image.LANCZOS)
        im.paste(bp, (int(bx) - bp.width // 2, int(by) - bp.height // 2), bp)
        d = ImageDraw.Draw(im)
    if a.bula:
        parts = a.bula.rsplit(':', 2); txt = parts[0]; bx, by = int(parts[1]), int(parts[2])
        bp = Image.open(os.path.join(ELEM, 'bula_GOLA.png')).resize((430, 239), Image.LANCZOS)
        im.paste(bp, (bx - 215, by - 140), bp)
        d = ImageDraw.Draw(im)
        ft = ImageFont.truetype(ANTON, 88)
        tb = d.textbbox((0, 0), txt, font=ft, stroke_width=6)
        d.text((bx-(tb[2]-tb[0])//2-tb[0], by-15-(tb[3]-tb[1])//2-tb[1]), txt, font=ft,
               fill=(229, 32, 38, 255), stroke_width=6, stroke_fill=(120, 8, 10, 255))
    if a.sageata:
        x0, y0, x1, y1 = [int(v) for v in a.sageata.split(':')]
        d.ellipse([x0-24, y0-24, x0+24, y0+24], fill=ROSU)
        d.line([x0, y0, x1, y1], fill=ROSU, width=48)
        ang = math.atan2(y1-y0, x1-x0)
        for da in (ang+2.45, ang-2.45):
            d.line([x1, y1, x1+int(170*math.cos(da)), y1+int(170*math.sin(da))], fill=ROSU, width=48)
    if a.inimi:
        ix, iy = int(a.inimi.split(':')[0]), int(a.inimi.split(':')[1])
        hq = Image.open(os.path.join(ELEM, 'inimi_rosii.png'))
        hq = hq.resize((int(hq.width*0.85), int(hq.height*0.85)), Image.LANCZOS)
        im.paste(hq, (ix - hq.width//2, iy - hq.height//2), hq)
    if a.cerc_pe:
        # Cercul lui, fix pe obiect: se calculeaza centrul si diametrul din caseta tintei.
        b = a.cerc_pe.split(':')
        x0, y0, x1, y1 = [int(v) for v in b[0].split(',')]
        cale = b[1] if len(b) > 1 else os.path.join(BASE, 'elemente_brand', 'JH',
                                                    'CANONIC', 'CERC_2.png')
        cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
        diam = int(max(x1 - x0, y1 - y0) * 1.3)
        cp = Image.open(cale).convert('RGBA')
        cp = cp.resize((diam, int(cp.height * diam / cp.width)), Image.LANCZOS)
        im.paste(cp, (cx - cp.width // 2, cy - cp.height // 2), cp)
        d = ImageDraw.Draw(im)

    if a.sageata_spre:
        # Sageata lui, orientata din coltul ales spre tinta (rotita, nu desenata).
        b = a.sageata_spre.split(':')
        cale, tx, ty, latime, colt = b[0], int(b[1]), int(b[2]), int(b[3]), b[4]
        colturi = {'sj': (0.12 * 1280, 0.88 * 720), 'dj': (0.88 * 1280, 0.88 * 720),
                   'ss': (0.12 * 1280, 0.12 * 720), 'ds': (0.88 * 1280, 0.12 * 720)}
        sx, sy = colturi.get(colt, colturi['sj'])
        sa = Image.open(cale).convert('RGBA')
        sa = sa.resize((latime, int(sa.height * latime / sa.width)), Image.LANCZOS)
        if len(b) > 5 and b[5] == 'stanga':
            sa = sa.transpose(Image.FLIP_LEFT_RIGHT)
        unghi = math.degrees(math.atan2(ty - sy, tx - sx))
        rot = sa.rotate(-unghi, expand=True, resample=Image.BICUBIC)
        px = int(sx + (tx - sx) * 0.42 - rot.width / 2)
        py = int(sy + (ty - sy) * 0.42 - rot.height / 2)
        im.paste(rot, (px, py), rot)
        d = ImageDraw.Draw(im)

    for element in a.pune or []:
        # Element 1:1 din biblioteca (săgeata/cercul/semnul LUAT din original, nu desenat).
        cale, ex, ey, elat = element.rsplit(':', 3)
        ep = Image.open(cale).convert('RGBA')
        ep = ep.resize((int(elat), int(ep.height * int(elat) / ep.width)), Image.LANCZOS)
        im.paste(ep, (int(ex) - ep.width // 2, int(ey) - ep.height // 2), ep)
        d = ImageDraw.Draw(im)
    if a.logo:
        cale = os.path.join(BASE, 'assets', 'logo_pokecity_clear.png') if a.logo == 'pokecity' else a.logo
        if os.path.exists(cale):
            lg = Image.open(cale).convert('RGBA'); lg.thumbnail((150, 150), Image.LANCZOS)
            im.paste(lg, (22, 720 - lg.height - 18), lg)
    fin = im.convert('RGB')
    fin = ImageEnhance.Color(fin).enhance(1.08)
    fin = ImageEnhance.Contrast(fin).enhance(1.05)
    fin = ImageEnhance.Sharpness(fin).enhance(1.22)
    fin.save(a.out, quality=93)
    if a.test120:
        fin.resize((120, 68), Image.LANCZOS).save(a.out.replace('.jpg', '_120px.jpg'), quality=88)
    print('BRAND OK:', a.out)
if __name__ == '__main__':
    main()
