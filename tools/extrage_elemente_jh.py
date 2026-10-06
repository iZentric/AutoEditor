#!/usr/bin/env python3
"""Extrage 1:1 elementele de brand din thumbnail-urile REALE ( legea: iei, nu refaci ).

Pentru fiecare thumbnail (implicit toate JocuriHorrorSky din refs/brand_1la1/) scoate:
  * BULA  = balonul/textul cu contur (crop cu alpha, păstrând EXACT cuvântul din original)
  * CERC  = cercul roșu de highlight (regiuni roșii, formă de inel)
  * SAGEATA = săgeata/„linia" roșie care arată spre acțiune (regiuni roșii alungite)

Scrie elemente_brand/JH/*.png + un INDEX.csv (fișier sursă, tip, cuvânt, coordonate).

Utilizare:
  python3 tools/extrage_elemente_jh.py                      # toate JocuriHorrorSky
  python3 tools/extrage_elemente_jh.py --canal dagar        # alt canal din bibliotecă
  python3 tools/extrage_elemente_jh.py --fisier NUME.jpg    # unul singur
"""
import argparse
import csv
import os
import re
from collections import deque

import numpy as np
from PIL import Image


def dilata(m, pasi=1):
    for _ in range(pasi):
        n = m.copy()
        n[1:, :] |= m[:-1, :]
        n[:-1, :] |= m[1:, :]
        n[:, 1:] |= m[:, :-1]
        n[:, :-1] |= m[:, 1:]
        m = n
    return m


def componente(masca, minim=60):
    """Lista de (arie, x0, y0, x1, y1, masca_componentei)."""
    h, w = masca.shape
    vazut = np.zeros_like(masca)
    gasite = []
    for y in range(h):
        for x in range(w):
            if not masca[y, x] or vazut[y, x]:
                continue
            q = deque([(y, x)]); vazut[y, x] = True; cel = []
            while q:
                cy, cx = q.popleft(); cel.append((cy, cx))
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and masca[ny, nx] and not vazut[ny, nx]:
                            vazut[ny, nx] = True; q.append((ny, nx))
            if len(cel) >= minim:
                ys = [c[0] for c in cel]; xs = [c[1] for c in cel]
                m = np.zeros_like(masca)
                for cy, cx in cel:
                    m[cy, cx] = True
                gasite.append((len(cel), min(xs), min(ys), max(xs) + 1, max(ys) + 1, m))
    return sorted(gasite, reverse=True)


def umple_gauri(masca):
    h, w = masca.shape
    afara = np.zeros_like(masca)
    afara[0, :] = afara[-1, :] = afara[:, 0] = afara[:, -1] = True
    liber = ~masca
    schimbat = True
    while schimbat:
        schimbat = False
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nou = afara | (np.roll(afara, (dy, dx), axis=(0, 1)) & liber)
            if nou.sum() != afara.sum():
                schimbat = True
            afara = nou
    return ~afara


def salveaza_png(imagine, masca, out):
    alpha = (masca * 255).astype(np.uint8)
    img = imagine.convert('RGBA')
    img.putalpha(Image.fromarray(alpha))
    img = img.crop(Image.fromarray(alpha).getbbox())
    img.save(out)
    return img.size


def curata(text):
    return re.sub(r'[^A-Za-z0-9?!ăâîșțĂÂÎȘȚ]', '', text)[:18] or 'element'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--biblioteca', default='refs/brand_1la1')
    ap.add_argument('--canal', default='JocuriHorrorSky')
    ap.add_argument('--fisier', default=None)
    ap.add_argument('--iesire', default='elemente_brand/JH')
    a = ap.parse_args()

    os.makedirs(a.iesire, exist_ok=True)
    try:
        from rapidocr_onnxruntime import RapidOCR
        ocr = RapidOCR()
    except ImportError:
        print('Lipsește OCR: pip install --break-system-packages rapidocr-onnxruntime '
              'opencv-python-headless')
        return 1

    fisiere = ([a.fisier] if a.fisier
               else sorted(f for f in os.listdir(a.biblioteca)
                           if f.startswith(a.canal) and f.endswith('.jpg')))
    index = []
    for nume in fisiere:
        cale = os.path.join(a.biblioteca, nume)
        img = Image.open(cale).convert('RGB').resize((1280, 720))
        # fiecare thumbnail isi primeste propriul dosar: bula + cercul + sageata LUI,
        # exact cum apar in acel thumbnail (nu unul refacut, nu unul „destul de bun")
        dosar = os.path.join(a.iesire, nume[:-4])
        os.makedirs(dosar, exist_ok=True)
        Image.open(cale).convert('RGB').resize((1280, 720)).save(os.path.join(dosar, '_SURSA.jpg'))
        arr = np.asarray(img).astype(int)
        R, G, B = arr[..., 0], arr[..., 1], arr[..., 2]

        # --- TEXTE (OCR) -> BULE ---
        mare = img.resize((2560, 1440), Image.LANCZOS)
        rez, _ = ocr(np.asarray(mare))
        for box, text, scor in (rez or []):
            if scor < 0.5 or len(text.strip()) < 2:
                continue
            xs = [p[0] for p in box]; ys = [p[1] for p in box]
            x0, y0, x1, y1 = int(min(xs) / 2), int(min(ys) / 2), int(max(xs) / 2), int(max(ys) / 2)
            m = int(max(12, (y1 - y0) * 0.55))
            cut = arr[max(0, y0 - m):min(720, y1 + m), max(0, x0 - m):min(1280, x1 + m)]
            if cut.size == 0:
                continue
            cR, cG, cB = cut[..., 0], cut[..., 1], cut[..., 2]
            alb = cut.min(axis=2) > 190
            corp = dilata(alb, 3)
            contur = (cut.max(axis=2) < 110) & dilata(corp, 12)
            saturat = ((cut.max(axis=2) - cut.min(axis=2)) > 70) & (cut.max(axis=2) > 120)
            masca = corp | contur | (saturat & dilata(corp, 8) if corp.any() else saturat)
            masca = umple_gauri(masca)
            if masca.sum() < 900:
                continue
            sub = img.crop((max(0, x0 - m), max(0, y0 - m), min(1280, x1 + m), min(720, y1 + m)))
            # elementul e bun doar daca OCR recunoaste ACELASI cuvant si in PNG-ul decupat
            fundal = Image.new('RGB', sub.size, (255, 255, 255))
            fundal.paste(sub, (0, 0), (lambda i: (i.putalpha(Image.fromarray((masca*255).astype('uint8'))), i)[1])(sub.copy()))
            mare3 = fundal.resize((fundal.width * 3, fundal.height * 3), Image.LANCZOS)
            ok, _ = ocr(np.asarray(mare3))
            ramas = ' '.join(r[1] for r in (ok or []))
            confirmat = curata(text).lower()[:4] in curata(ramas).lower()
            semn = any(c in text.upper() for c in ('WELCOME', 'OHIO', 'TIKTOK', 'STRICT'))
            tip = 'SEMN/LOGO_JH' if semn else 'BULA'
            prefix = 'SEMN' if semn else 'BULA'
            fisier = f'{prefix}_{curata(text)}.png'
            marime = salveaza_png(sub, masca, os.path.join(dosar, fisier))
            index.append([tip, f'{nume[:-4]}/{fisier}', nume, text, f'{x0},{y0},{x1},{y1}',
                          f'{marime[0]}x{marime[1]}', round(float(scor), 2),
                          'DA' if confirmat else 'VERIFICA'])

        # --- ROȘU: CERC + SĂGEATĂ ---
        rosu = (R - G > 65) & (R - B > 65) & (R > 140)
        gasite_rosu = []
        for arie, x0, y0, x1, y1, m in componente(rosu, minim=2500):
            w, h = x1 - x0, y1 - y0
            if w < 60 or h < 60:
                continue
            raport = w / h
            umplere = m.sum() / (w * h)
            # inel = gol in centru (cercul de highlight e trasat, nu umplut)
            cy0, cy1 = y0 + int(h * 0.3), y1 - int(h * 0.3)
            cx0, cx1 = x0 + int(w * 0.3), x1 - int(w * 0.3)
            miez = m[cy0:cy1, cx0:cx1].mean() if cy1 > cy0 and cx1 > cx0 else 1.0
            if 0.7 < raport < 1.45 and umplere < 0.6 and miez < 0.35 and arie > 6000:
                tip = 'CERC'
            elif (raport >= 1.8 or raport <= 0.55) and arie > 3500:
                tip = 'SAGEATA'
            else:
                continue
            gasite_rosu.append((arie, tip, x0, y0, x1, y1, m, umplere))
        for arie, tip, x0, y0, x1, y1, m, umplere in sorted(gasite_rosu, reverse=True)[:3]:
            pad = 6
            sub = img.crop((max(0, x0 - pad), max(0, y0 - pad),
                            min(1280, x1 + pad), min(720, y1 + pad)))
            mm = m[max(0, y0 - pad):min(720, y1 + pad), max(0, x0 - pad):min(1280, x1 + pad)]
            fisier = f'{tip}_{x0}x{y0}.png'
            marime = salveaza_png(sub, dilata(mm, 1), os.path.join(dosar, fisier))
            index.append([tip, f'{nume[:-4]}/{fisier}', nume, '', f'{x0},{y0},{x1},{y1}',
                          f'{marime[0]}x{marime[1]}', round(umplere, 2), '-'])

    with open(os.path.join(a.iesire, 'INDEX.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['tip', 'fisier', 'sursa', 'cuvant', 'coordonate', 'marime', 'scor', 'ocr_ok'])
        w.writerows(index)
    print(f'GATA: {len(index)} elemente in {a.iesire}/ (vezi INDEX.csv)')
    for tip, fisier, nume, cuvant, coord, marime, scor, ok in index:
        print(f'  {tip:14s} {fisier:44s} {cuvant or "":12s} {marime:9s} OCR={ok}')


if __name__ == '__main__':
    raise SystemExit(main())
