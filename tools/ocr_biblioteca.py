#!/usr/bin/env python3
"""Caută TEXT în biblioteca 1:1 (refs/brand_1la1) — „am nevoie de balonul cu CE?".

Agentul NU vede imaginile, deci citește textul din ele cu OCR. Așa se găsește
elementul REAL de copiat 1:1, fără să-l regenerezi și fără să ghicești din nume.

Utilizare:
  python3 tools/ocr_biblioteca.py CE          # toate aparițiile lui „CE" + coordonatele
  python3 tools/ocr_biblioteca.py             # tot textul din toată biblioteca
  python3 tools/ocr_biblioteca.py FUGI --canal JocuriHorrorSky

Apoi extragi elementul:
  python3 tools/crop_balon.py refs/brand_1la1/FISIER.jpg --box x0,y0,x1,y1 --out elemente_brand/NUME.png --verifica-ocr

Dependență: pip install --break-system-packages rapidocr-onnxruntime opencv-python-headless
(headless: sandbox-ul n-are libGL).
"""
import argparse
import os
import sys

import numpy as np
from PIL import Image


def scaneaza(cale, ocr, filtru=None):
    img = Image.open(cale).convert('RGB')
    mare = img.resize((img.width * 2, img.height * 2), Image.LANCZOS)
    rezultat, _ = ocr(np.asarray(mare))
    gasite = []
    for box, text, scor in (rezultat or []):
        xs = [p[0] for p in box]
        ys = [p[1] for p in box]
        caseta = (int(min(xs) / 2), int(min(ys) / 2), int(max(xs) / 2), int(max(ys) / 2))
        if filtru and filtru.lower() not in text.lower():
            continue
        gasite.append((text, caseta, round(float(scor), 2)))
    return gasite


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('text', nargs='?', default='')
    ap.add_argument('--canal', default=None)
    ap.add_argument('--baza', default='refs/brand_1la1')
    a = ap.parse_args()
    try:
        from rapidocr_onnxruntime import RapidOCR
    except ImportError:
        print('Lipsește OCR: pip install --break-system-packages rapidocr-onnxruntime '
              'opencv-python-headless', file=sys.stderr)
        return 1
    ocr = RapidOCR()
    for nume in sorted(os.listdir(a.baza)):
        if not nume.endswith(('.jpg', '.png')):
            continue
        if a.canal and not nume.lower().startswith(a.canal.lower()):
            continue
        for text, caseta, scor in scaneaza(os.path.join(a.baza, nume), ocr, a.text or None):
            x0, y0, x1, y1 = caseta
            print(f'{nume:38s} "{text}" scor {scor}  box {x0},{y0},{x1},{y1}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
