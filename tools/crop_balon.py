#!/usr/bin/env python3
"""Extrage UN element de brand 1:1 dintr-un thumbnail REAL (fara regenerare).

Legea bossului: „copiaza 1:1, nu redesena". Asta scoate balonul/bula/sageata direct
din thumbnail-ul original, cu FUNDAL TRANSPARENT, exact cum a facut agentul precedent
cu BALON_JH_real_CE (care s-a pierdut la migrare).

Cum functioneaza (fara ochi, fara AI):
  1. primeste caseta textului gasita de OCR (x0,y0,x1,y1);
  2. o largeste cu o margine;
  3. masca = pixelii ALBI (corpul balonului) dilatati, + pixelii NEGRI lipiti de ea
     (conturul gros);
  4. umple gaurile si sterge ce e legat de marginea cadrului (= fundalul scenei);
  5. salveaza PNG RGBA cu alpha.

Utilizare:
  python3 tools/crop_balon.py IMG.jpg --box 530,41,752,165 --out elemente_brand/BALON.png
  python3 tools/crop_balon.py IMG.jpg --box ... --out ... --margine 40 --alb 195
"""
import argparse

import numpy as np
from PIL import Image


def dilata(masca, pasi):
    m = masca.copy()
    for _ in range(pasi):
        n = m.copy()
        n[1:, :] |= m[:-1, :]
        n[:-1, :] |= m[1:, :]
        n[:, 1:] |= m[:, :-1]
        n[:, :-1] |= m[:, 1:]
        m = n
    return m


def umple_gauri(masca):
    """Tine doar regiunea care NU e legata de marginea cadrului, apoi umple interiorul."""
    h, w = masca.shape
    afara = np.zeros_like(masca)
    afara[0, :] = afara[-1, :] = afara[:, 0] = afara[:, -1] = True
    liber = ~masca
    schimbat = True
    while schimbat:
        schimbat = False
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            mutat = np.roll(afara, (dy, dx), axis=(0, 1))
            nou = afara | (mutat & liber)
            if nou.sum() != afara.sum():
                schimbat = True
            afara = nou
    return ~afara


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('imagine')
    ap.add_argument('--box', required=True, help='x0,y0,x1,y1 (caseta textului din OCR)')
    ap.add_argument('--out', required=True)
    ap.add_argument('--margine', type=int, default=45)
    ap.add_argument('--alb', type=int, default=195, help='prag pixel alb (0-255)')
    ap.add_argument('--contur', type=int, default=14, help='grosimea conturului de capturat')
    ap.add_argument('--verifica-ocr', action='store_true')
    a = ap.parse_args()

    img = Image.open(a.imagine).convert('RGB')
    x0, y0, x1, y1 = [int(v) for v in a.box.split(',')]
    m = a.margine
    cut = (max(0, x0 - m), max(0, y0 - m), min(img.width, x1 + m), min(img.height, y1 + m))
    crop = img.crop(cut)
    arr = np.asarray(crop).astype(int)

    alb = arr.min(axis=2) > a.alb
    corp = dilata(alb, 3)
    contur = (arr.max(axis=2) < 105) & dilata(corp, a.contur)
    masca = umple_gauri(corp | contur)
    masca = dilata(masca, 1)

    # alpha moale pe 1 pixel ca sa nu taie ca un decupaj
    alpha = (masca * 255).astype(np.uint8)
    sus, jos = alpha[:-1, :].astype(int), alpha[1:, :].astype(int)
    st, dr = alpha[:, :-1].astype(int), alpha[:, 1:].astype(int)
    muchie = (np.abs(sus - jos) > 0)
    alpha[:-1, :][muchie] = 190
    muchie2 = (np.abs(st - dr) > 0)
    alpha[:, :-1][muchie2] = 190

    out = crop.convert('RGBA')
    out.putalpha(Image.fromarray(alpha))
    bbox = out.getbbox()
    out.save(a.out)
    acoperire = masca.sum() / masca.size
    print(f'CROP OK: {a.out}  taietura {cut}  marime {out.size}  acoperire {acoperire:.0%}')

    if a.verifica_ocr:
        from rapidocr_onnxruntime import RapidOCR
        fundal = Image.new('RGB', out.size, (255, 255, 255))
        fundal.paste(out, (0, 0), out)
        mare = fundal.resize((fundal.width * 3, fundal.height * 3), Image.LANCZOS)
        rez, _ = RapidOCR()(np.asarray(mare))
        print('   text ramas in element:', ' / '.join(r[1] for r in (rez or [])) or '(nimic)')


if __name__ == '__main__':
    main()
