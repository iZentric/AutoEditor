#!/usr/bin/env python3
"""Coace thumbnailul exact cum l-a așezat creatorul în editorul din browser.

CITEȘTE:  /home/user/preview/pozitii.json  (scris de editor.html prin POST /salveaza)
SCRIE:    refs/THUMB_EP1_CORECT.jpg  (+ varianta _120px.jpg, testul „arată bine mic?”)

Regula: NU reface, NU regenerează nimic — doar lipește elementele deja extrase
(din elemente_brand/) la coordonatele date de om. Zero AI, zero guess.

Folosire:
    python3 tools/coace_din_editor.py                     # din pozitii.json
    python3 tools/coace_din_editor.py --json ALT.json
    python3 tools/coace_din_editor.py --out refs/ALTA.jpg
"""
import argparse
import json
import os
import sys

from PIL import Image

RADACINA = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PREVIEW = os.path.join(os.path.dirname(RADACINA), "preview")
POZITII_DEFAULT = os.path.join(PREVIEW, "pozitii.json")
SPATIU = (1280, 720)


def _cale(src):
    """Căile din editor sunt relative la /preview (ex. 'el/BULA_FUGI.png')."""
    if os.path.isabs(src):
        return src
    for baza in (PREVIEW, RADACINA):
        p = os.path.join(baza, src)
        if os.path.exists(p):
            return p
    return os.path.join(PREVIEW, src)


def lipeste(scena, el):
    """Lipește UN element: redimensionează la lățimea dată, rotește, întoarce,
    apoi îl centrează în punctul (x, y) din spațiul 1280x720."""
    cale = _cale(el["src"])
    if not os.path.exists(cale):
        print(f"  !! lipsește {cale} — sar peste {el.get('tip', el.get('id'))}")
        return scena
    img = Image.open(cale).convert("RGBA")

    w = int(round(float(el.get("w", 200))))
    if w <= 0:
        return scena
    h = max(1, int(round(img.height * w / img.width)))
    img = img.resize((w, h), Image.LANCZOS)

    rot = float(el.get("rot", 0))
    if rot:
        # CSS rotate(e.rot) e în sensul acelor de ceas; PIL rotate() e invers.
        img = img.rotate(-rot, expand=True, resample=Image.BICUBIC)
    if el.get("flip"):
        img = img.transpose(Image.FLIP_LEFT_RIGHT)

    x = int(round(float(el.get("x", 0))))
    y = int(round(float(el.get("y", 0))))
    st = x - img.width // 2
    sus = y - img.height // 2
    scena.alpha_composite(img, dest=(st, sus))
    print(f"  + {el.get('tip', el.get('id', '?')):22s} {os.path.basename(cale):22s} "
          f"x={x} y={y} w={w} rot={rot:g}°{' FLIP' if el.get('flip') else ''}")
    return scena


def coace(json_path, out_path, baza=None):
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    sursa = baza or data.get("imagine") or "BASE.jpg"
    cale_baza = _cale(sursa)
    if not os.path.exists(cale_baza):
        sys.exit(f"Baza nu există: {cale_baza}")

    fundal = Image.open(cale_baza).convert("RGBA").resize(SPATIU, Image.LANCZOS)
    print(f"BAZA {cale_baza} -> {SPATIU[0]}x{SPATIU[1]}")

    for el in data.get("elemente", []):
        fundal = lipeste(fundal, el)

    fundal.convert("RGB").save(out_path, quality=94)
    print(f"\nSCRIS {out_path}")

    mic = out_path.rsplit(".", 1)[0] + "_120px.jpg"
    Image.open(out_path).resize((120, 68), Image.LANCZOS).save(mic, quality=88)
    print(f"SCRIS {mic}  (testul de 120px — dacă se citește mic, e bun)")

    if data.get("cap1"):
        print(f"\nCapul personajului: {data['cap1']}")
    if data.get("cap2"):
        print(f"Al doilea cap:      {data['cap2']}")
    return out_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=POZITII_DEFAULT, help="fișierul cu pozițiile salvate")
    ap.add_argument("--out", default=None, help="unde scrie thumbnailul")
    ap.add_argument("--baza", default=None, help="imaginea de fundal (default: ce zice json-ul)")
    args = ap.parse_args()

    out = args.out or os.path.join(RADACINA, "refs", "THUMB_EP1_CORECT.jpg")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    coace(args.json, out, args.baza)


if __name__ == "__main__":
    main()
