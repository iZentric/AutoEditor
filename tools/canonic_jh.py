#!/usr/bin/env python3
"""Alege elementele CANONICE ale lui JocuriHorrorSky + golește bula (fără s-o refaci).

Regula bossului: de la JH luăm DOAR semnele (bula, cercul, săgeata), exact cum sunt la el.
Baza (layoutul) vine de la dagar / Nacho. Așa că avem nevoie de:
  1. BULA_GOLA_JH.png  = bula LUI, vidă (textul șters din interior, nu redesemnată)
                         → punem în ea orice cuvânt (FUGI, CE?, AJUTOR…) cu fontul lui.
  2. CERC_1..3.png     = cele mai curate inele roșii găsite pe toate thumbnail-urile lui.
  3. SAGEATA_1..3.png  = cele mai curate săgeți („alea de arată").

Nimic nu e generat: sunt decupaje; la bula vidă se șterg doar pixelii textului și se
umple cu culoarea reală a bulei (alb/gradientul ei), păstrând conturul lui gros.

Utilizare:
  python3 tools/canonic_jh.py
"""
import os
from collections import deque

import numpy as np
from PIL import Image


def componente(masca, minim=1200):
    h, w = masca.shape
    vazut = np.zeros_like(masca)
    out = []
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
                out.append((len(cel), min(xs), min(ys), max(xs) + 1, max(ys) + 1, m))
    return sorted(out, reverse=True)


def salveaza(img, masca, cale):
    a = (masca * 255).astype(np.uint8)
    im = img.convert('RGBA'); im.putalpha(Image.fromarray(a))
    im.crop(Image.fromarray(a).getbbox()).save(cale)
    return Image.open(cale).size


def goleste_bula(cale_bula, cale_out):
    """Șterge TEXTUL din interiorul bulei, păstrând conturul și fundalul bulei."""
    im = Image.open(cale_bula).convert('RGBA')
    arr = np.asarray(im).astype(int)
    alpha = arr[..., 3] > 40
    rgb = arr[..., :3]
    interior = alpha.copy()
    for _ in range(9):  # erodare: scoatem conturul gros ca să nu-l ștergem
        n = interior.copy()
        n[1:, :] &= interior[:-1, :]
        n[:-1, :] &= interior[1:, :]
        n[:, 1:] &= interior[:, :-1]
        n[:, :-1] &= interior[:, 1:]
        interior = n
    text = interior & ((rgb.min(axis=2) < 150) | ((rgb.max(axis=2) - rgb.min(axis=2)) > 70))
    if text.sum() < 50:
        return None
    for _ in range(3):  # umflăm puțin ca să prindem și marginea literelor
        t = text.copy()
        t[1:, :] |= text[:-1, :]
        t[:-1, :] |= text[1:, :]
        t[:, 1:] |= text[:, :-1]
        t[:, :-1] |= text[:, 1:]
        text = t
    umplere = rgb[interior & ~text]
    culoare = tuple(int(v) for v in np.median(umplere, axis=0)) if len(umplere) else (255, 255, 255)
    nou = arr.copy()
    for c in range(3):
        canal = nou[..., c]
        canal[text] = culoare[c]
        nou[..., c] = canal
    Image.fromarray(nou.astype('uint8'), 'RGBA').save(cale_out)
    return text.sum()


def main():
    baza = 'refs/brand_1la1'
    iesire = 'elemente_brand/JH/CANONIC'
    os.makedirs(iesire, exist_ok=True)

    # ---------- 1. cercul și săgeata canonice ----------
    cercuri, sageti = [], []
    for nume in sorted(os.listdir(baza)):
        if not nume.startswith('JocuriHorrorSky') or not nume.endswith('.jpg'):
            continue
        img = Image.open(os.path.join(baza, nume)).convert('RGB').resize((1280, 720))
        arr = np.asarray(img).astype(int)
        R, G, B = arr[..., 0], arr[..., 1], arr[..., 2]
        rosu = (R - G > 65) & (R - B > 65) & (R > 140)
        for arie, x0, y0, x1, y1, m in componente(rosu):
            w, h = x1 - x0, y1 - y0
            if w < 70 or h < 70:
                continue
            raport = w / h
            umplere = m.sum() / (w * h)
            cy0, cy1 = y0 + int(h * .3), y1 - int(h * .3)
            cx0, cx1 = x0 + int(w * .3), x1 - int(w * .3)
            miez = float(m[cy0:cy1, cx0:cx1].mean()) if cy1 > cy0 and cx1 > cx0 else 1.0
            if 0.75 < raport < 1.35 and umplere < 0.55 and miez < 0.3 and arie > 8000:
                # inel: scor = cât de rotund + cât de gol în centru + cât de mare
                cercuri.append(((1 - abs(1 - raport)) * 2 + (1 - miez) + min(arie / 40000, 1),
                                nume, x0, y0, x1, y1, m))
            elif (raport >= 1.7 or raport <= 0.58) and arie > 4000:
                solid = m[y0 + int(h * .2):y1 - int(h * .2), x0 + int(w * .2):x1 - int(w * .2)].mean()
                sageti.append((min(arie / 25000, 1) + float(solid) + (raport if raport > 1 else 1 / raport) / 4,
                               nume, x0, y0, x1, y1, m))
    for sursa, lista, prefix in (('cerc', cercuri, 'CERC'), ('săgeți', sageti, 'SAGEATA')):
        for i, (scor, nume, x0, y0, x1, y1, m) in enumerate(sorted(lista, reverse=True)[:3], 1):
            img = Image.open(os.path.join(baza, nume)).convert('RGB').resize((1280, 720))
            pad = 8
            sub = img.crop((max(0, x0 - pad), max(0, y0 - pad), min(1280, x1 + pad), min(720, y1 + pad)))
            mm = m[max(0, y0 - pad):min(720, y1 + pad), max(0, x0 - pad):min(1280, x1 + pad)]
            marime = salveaza(sub, mm, os.path.join(iesire, f'{prefix}_{i}.png'))
            print(f'{prefix}_{i}.png  scor {scor:.2f}  din {nume}  {marime}')

    # ---------- 2. bula lui, vidă ----------
    dosare = sorted(d for d in os.listdir('elemente_brand/JH')
                    if os.path.isdir(os.path.join('elemente_brand/JH', d)))
    for dosar in dosare:
        for fisier in sorted(os.listdir(os.path.join('elemente_brand/JH', dosar))):
            if fisier.startswith('BULA_') and 'GOLA' not in fisier:
                cale = os.path.join('elemente_brand/JH', dosar, fisier)
                out = os.path.join(iesire, 'BULA_GOLA_JH_' + fisier.replace('BULA_', ''))
                sterse = goleste_bula(cale, out)
                if sterse:
                    print(f'BULA GOLITA: {out}  ({sterse} pixeli de text stersi) din {dosar}/{fisier}')
    print('CANONIC GATA ->', iesire)


if __name__ == '__main__':
    main()
