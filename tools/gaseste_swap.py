#!/usr/bin/env python3
"""Găsește UNDE s-au schimbat personajele după un swap 1:1.

Truc: baza și rezultatul au ACEEAȘI compoziție (fundalul e înghețat), deci
diferența dintre ele = exact zonele cu personaje. Asta înlocuiește „ochiul"
agentului când nu poate vedea imaginea: coordonatele pentru nametag/bulă/cerc
se calculează, nu se ghicesc.

Utilizare:
  python3 tools/gaseste_swap.py BAZA.jpg REZULTAT.jpg [--prag 60]
Tipărește clusterele (x, y, w, h, arie, centru) sortate descrescător.
"""
import argparse
from collections import deque

import numpy as np
from PIL import Image

SCARA = 4  # analiza se face la 1/4 din rezoluție (rapid, suficient de precis)


def masca(baza, rezultat, prag):
    a = np.asarray(Image.open(baza).convert('RGB').resize((1280, 720))).astype(int)
    b = np.asarray(Image.open(rezultat).convert('RGB').resize((1280, 720))).astype(int)
    diff = np.abs(a - b).sum(axis=2)
    mic = diff.reshape(720 // SCARA, SCARA, 1280 // SCARA, SCARA).mean(axis=(1, 3))
    return mic > prag


def clustere(masca, minim_celule=25):
    h, w = masca.shape
    vazut = np.zeros_like(masca, dtype=bool)
    gasite = []
    for y in range(h):
        for x in range(w):
            if not masca[y, x] or vazut[y, x]:
                continue
            coada = deque([(y, x)])
            vazut[y, x] = True
            celule = []
            while coada:
                cy, cx = coada.popleft()
                celule.append((cy, cx))
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < h and 0 <= nx < w and masca[ny, nx] and not vazut[ny, nx]:
                        vazut[ny, nx] = True
                        coada.append((ny, nx))
            if len(celule) >= minim_celule:
                ys = [c[0] for c in celule]
                xs = [c[1] for c in celule]
                gasite.append({
                    'arii': len(celule),
                    'x0': min(xs) * SCARA, 'y0': min(ys) * SCARA,
                    'x1': (max(xs) + 1) * SCARA, 'y1': (max(ys) + 1) * SCARA,
                })
    return sorted(gasite, key=lambda c: -c['arii'])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('baza')
    ap.add_argument('rezultat')
    ap.add_argument('--prag', type=int, default=60)
    a = ap.parse_args()
    gasite = clustere(masca(a.baza, a.rezultat, a.prag))
    if not gasite:
        print('NICIO SCHIMBARE DETECTATĂ — verifică pragul sau imaginile.')
        return
    print(f'{len(gasite)} zone schimbate (sortate după mărime):')
    for i, c in enumerate(gasite, 1):
        cx = (c['x0'] + c['x1']) // 2
        cy = (c['y0'] + c['y1']) // 2
        print(f"  #{i} x {c['x0']}-{c['x1']}  y {c['y0']}-{c['y1']}  "
              f"centru {cx},{cy}  arie {c['arii'] * SCARA * SCARA}px")
    print('\nSugestie brand (primul = personaj mare, ultimul = creatura/obiectul mic):')
    mare = sorted(gasite, key=lambda c: -(c['x1'] - c['x0']))[:2]
    for c in mare:
        print(f"  --ntag NUME:{(c['x0'] + c['x1']) // 2}:{max(60, c['y0'] - 40)}")
    mic = min(gasite, key=lambda c: c['arii'])
    cx, cy = (mic['x0'] + mic['x1']) // 2, (mic['y0'] + mic['y1']) // 2
    print(f'  --cerc {cx}:{cy}:{max(110, (mic["x1"] - mic["x0"]) // 2 + 40)}')
    print(f'  sageata din coltul cel mai apropiat spre {cx},{cy}')


if __name__ == '__main__':
    main()
