#!/usr/bin/env python3
"""Taie elementele lui JocuriHorrorSky EXACT — ÎNTREGI, la pixel, fundal scos.

De ce există: extracția vechei (extrage_elemente_jh.py) tăia prea strâns
(marginea = 55% din înălțimea TEXTULUI, nu a bulei) ⇒ toate elementele ieșeau
CIUNTITE, cu fundalul scenei lipit de ele. Boss: „e urat, nu e întreg".

CE FACE AICI, și păstrează pixelii 1:1:
  • aceeași mască pe care o folosea extracția veche (alb + contur + saturat pentru
    bule; culoare vie pentru cerc și săgeată) — deci aceeași „vedere" asupra elementului;
  • DAR lărgește cadrul din 40 în 40 px până când masca NU MAI ATINGE MARGINEA
    ⇒ elementul e ÎNTREG, cu tot cu contur și codiță;
  • păstrează doar componentele care se lipesc de caseta elementului (nu fură
    vecinii din poză);
  • cercul rămâne INEL (gol în mijloc) ca să poată fi pus pe o față;
  • fundalul = alpha 0, elementul = alpha 255, la rezoluția sursei (1280x720),
    fără redimensionare, fără refacere, fără AI.

Folosire:
    python3 tools/taie_exact.py                     # re-taie TOATE din INDEX.csv
    python3 tools/taie_exact.py --sursa X.jpg --box 100,20,400,180 --tip BULA --out e.png
"""
import argparse
import csv
import os
import sys

import numpy as np
from PIL import Image

RADACINA = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JH = os.path.join(RADACINA, "elemente_brand", "JH")
INDEX = os.path.join(JH, "INDEX.csv")
SURSE = [os.path.join(RADACINA, "refs", "surse_jh"),
         os.path.join(RADACINA, "refs", "brand_1la1")]

PAD0 = 40        # prima lărgire
PAS = 40         # cu cât lărgește la fiecare încercare
INCERCARI = 6
PAD_FINAL = 4    # margine lăsată la salvare


def _importa_ajutoare():
    """Folosim aceleași funcții ca extracția veche (dilata / componente / umple_gauri)."""
    sys.path.insert(0, os.path.join(RADACINA, "tools"))
    import extrage_elemente_jh as vechi
    return vechi.dilata, vechi.componente, vechi.umple_gauri


dilata, componente, umple_gauri = _importa_ajutoare()


def culoare_dominanta(im, box):
    """Culoarea elementului însuși — NU „orice e viu", că așa mănâncă toată scena."""
    arr = np.asarray(im.crop(box).convert("RGB")).astype(int)
    mx = arr.max(axis=2)
    mn = arr.min(axis=2)
    viu = ((mx - mn) > 60) & (mx > 110)
    if viu.sum() < 40:
        return None
    return np.median(arr[viu], axis=0)


def masca_dupa_tip(arr, tip, culoare=None, tol=70):
    """Masca brută (True = element) după tipul elementului."""
    mx = arr.max(axis=2)
    mn = arr.min(axis=2)
    if tip in ("BULA", "SEMN/LOGO_JH"):
        alb = mn > 190                       # corpul bulei (alb/crem)
        corp = dilata(alb, 3)
        contur = (mx < 110) & dilata(corp, 12)          # conturul negru
        saturat = ((mx - mn) > 70) & (mx > 120)         # textul colorat
        m = corp | contur | (saturat & dilata(corp, 8) if corp.any() else saturat)
        return umple_gauri(m)
    # CERC / SAGEATA: NU „orice culoare vie" (mănâncă scena), ci exact culoarea
    # elementului, oricare ar fi ea — bossul: „dacă-i cer cu roșu, verde, ce
    # culoare o fi". Culoarea se citește din caseta elementului, nu se presupune.
    if culoare is None:
        viu = ((mx - mn) > 60) & (mx > 110)
        m = dilata(viu, 2)
    else:
        d = np.abs(arr - culoare).max(axis=2)
        m = dilata(d <= tol, 2)
    return umple_gauri(m) if tip == "SAGEATA" else m   # CERC rămâne inel


def taie(im, box, tip):
    """Întoarce (crop RGB, masca, complet:bool) sau None."""
    W, H = im.size
    culoare = culoare_dominanta(im, box) if tip in ('CERC', 'SAGEATA') else None
    ultim = None
    for inc in range(INCERCARI):
        p = PAD0 + PAS * inc
        cx0, cy0 = max(0, box[0] - p), max(0, box[1] - p)
        cx1, cy1 = min(W, box[2] + p), min(H, box[3] + p)
        crop = im.crop((cx0, cy0, cx1, cy1))
        arr = np.asarray(crop.convert("RGB")).astype(int)
        if arr.size == 0:
            continue
        m = masca_dupa_tip(arr, tip, culoare)
        # păstrăm doar componentele lipite de caseta elementului
        sx0, sy0 = box[0] - cx0, box[1] - cy0
        sx1, sy1 = box[2] - cx0, box[3] - cy0
        alese = []
        for arie, x0, y0, x1, y1, mc in componente(m, minim=120):
            if not (x1 < sx0 or x0 > sx1 or y1 < sy0 or y0 > sy1):
                alese.append((arie, mc))
        if not alese:
            continue
        mm = np.zeros_like(m)
        for _, mc in alese:
            mm |= mc
        if tip in ("BULA", "SEMN/LOGO_JH", "SAGEATA"):
            mm = umple_gauri(mm)
        atinge = bool(mm[0, :].any() or mm[-1, :].any() or mm[:, 0].any() or mm[:, -1].any())
        la_marginea_pozei = (cx0 == 0 and cy0 == 0 and cx1 == W and cy1 == H)
        if mm.sum() < 400:
            continue
        ultim = (crop, mm, (not atinge) or la_marginea_pozei)
        if not atinge or la_marginea_pozei:
            return ultim
    return ultim


def salveaza(crop, mm, out):
    alpha = (mm * 255).astype(np.uint8)
    img = crop.convert("RGBA")
    img.putalpha(Image.fromarray(alpha))
    bbox = Image.fromarray(alpha).getbbox()
    if not bbox:
        return None
    x0, y0, x1, y1 = bbox
    w, h = img.size
    img = img.crop((max(0, x0 - PAD_FINAL), max(0, y0 - PAD_FINAL),
                    min(w, x1 + PAD_FINAL), min(h, y1 + PAD_FINAL)))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    img.save(out)
    return img.size


def gaseste_sursa(nume):
    for d in SURSE:
        p = os.path.join(d, nume)
        if os.path.exists(p):
            return p
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sursa")
    ap.add_argument("--box")
    ap.add_argument("--tip", default="BULA")
    ap.add_argument("--out")
    ap.add_argument("--iesire", default=os.path.join(JH, "EXACT"))
    args = ap.parse_args()

    if args.sursa and args.box and args.out:
        box = [int(v) for v in args.box.split(",")]
        r = taie(Image.open(args.sursa).convert("RGB"), box, args.tip)
        if not r:
            sys.exit("nimic găsit")
        crop, mm, complet = r
        s = salveaza(crop, mm, args.out)
        print(f"{args.out} {s[0]}x{s[1]} {'COMPLET' if complet else 'VERIFICA'}")
        return

    if not os.path.exists(INDEX):
        sys.exit(f"lipsește {INDEX}")
    with open(INDEX, newline="", encoding="utf-8") as f:
        randuri = list(csv.DictReader(f))

    raport = []
    for r in randuri:
        cale = gaseste_sursa(r["sursa"])
        if not cale:
            print(f"  !! sursă lipsă {r['sursa']}")
            continue
        box = [int(v) for v in r["coordonate"].strip('"').split(",")]
        im = Image.open(cale).convert("RGB").resize((1280, 720))
        rez = taie(im, box, r["tip"])
        if not rez:
            print(f"  !! nimic {r['fisier']}")
            continue
        crop, mm, complet = rez
        dest = os.path.join(args.iesire, r["fisier"])
        s = salveaza(crop, mm, dest)
        if not s:
            print(f"  !! vid {r['fisier']}")
            continue
        st = "COMPLET" if complet else "VERIFICA"
        print(f"  {r['tip']:14s} {r['fisier']:50s} {s[0]:4d}x{s[1]:<4d} {st}")
        raport.append([r["tip"], r["fisier"], r.get("cuvant", ""), r["sursa"],
                       ",".join(str(v) for v in box), f"{s[0]}x{s[1]}", st])

    with open(os.path.join(args.iesire, "RAPORT.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["tip", "fisier", "cuvant", "sursa", "box_sursa", "marime", "stare"])
        w.writerows(raport)
    comp = sum(1 for x in raport if x[6] == "COMPLET")
    print(f"\n{comp}/{len(raport)} ÎNTREGI · restul VERIFICA\nîn {args.iesire}")


if __name__ == "__main__":
    main()
