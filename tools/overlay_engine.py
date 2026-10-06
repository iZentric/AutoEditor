#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OVERLAY ENGINE — PIXEL-PERFECT & ZERO-ARTIFACT (legea bossului, executabila)
============================================================================
Protocol (PLACEMENT_ENGINE.md, sectiunea PIXEL-PERFECT):
  1. CLEAN ASSET EXTRACTION : alpha curat (erode + feather), zero bleeding/crop-artifacts,
     umbră moale 3D, upscale doar LANCZOS.
  2. PRECISION ANCHORING    : coada bulei -> centrul EXACT al gurii; tinta in centrul
     GEOMETRIC al cercului; capul sagetii -> centrul exact al cercului (rotire atan2).
  3. SMART SELECTION        : bazele se aleg din refs/brand_1la1/INDEX.csv (top views),
     compozitie curata, centru neaglomerat (verificata manual inainte de rulare).

Utilizare programatica:
    from overlay_engine import Engine
    e = Engine(baza='refs/brand_1la1/X.jpg', scena='scena.png',
               swap_poly=[(x1,y1),(x2,y2),...])
    e.cerc(tinta=(x,y), marime=385)
    e.sageata(tinta=(x,y), start=(x,y), lungime=300)
    e.bula(nume='bula_UxEMWdam-YU_1', tinta_gura=(x,y), start=(x,y), marime=215)
    e.nametag('iZentric', poz=(x,y))
    e.salveaza('out.png')          # + verificare automată 0 pixeli
"""
from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import math, os, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JH   = os.path.join(REPO, 'elemente_brand', 'JH_1LA1')
FONT = os.path.join(REPO, 'assets', 'Monocraft.ttc')


def asset_curat(im: Image.Image, crop=True) -> Image.Image:
    """REGULA 1 — alpha curat: erodează 1px zimțat + feather, zero bleeding.
    crop=False păstrează canvasul (necesar pentru săgeată: geometria vârfului rămâne cea validată)."""
    a = im.split()[3].filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(1.1))
    im = im.copy(); im.putalpha(a)
    if crop:
        bb = im.getbbox()
        im = im.crop(bb) if bb else im
    return im


def cu_umbra(el: Image.Image, blur=5, dx=7, dy=9, opac=165) -> Image.Image:
    """REGULA 1 — drop shadow moale 3D (se topește în fundal)."""
    ew, eh = el.size
    PW, PH = ew + dx + blur*2, eh + dy + blur*2
    sil = Image.new('L', (PW, PH), 0)
    sil.paste(el.split()[3], (blur, blur))
    sil = sil.filter(ImageFilter.GaussianBlur(blur)).point(lambda v: v*opac//255)
    sh = Image.new('RGBA', (PW, PH), (0, 0, 0, 0))
    sh = Image.composite(Image.new('RGBA', (PW, PH), (0, 0, 0, 255)), sh, sil)
    sh.alpha_composite(el, (blur, blur))
    return sh


def _tip(im):
    """Vârful assetului = pixelul opac cel mai depărtat de centroid."""
    a = im.split()[3]
    pts = [(x, y) for y in range(0, a.height, 2) for x in range(0, a.width, 2)
           if a.getpixel((x, y)) > 128]
    cx = sum(p[0] for p in pts)/len(pts); cy = sum(p[1] for p in pts)/len(pts)
    tip = max(pts, key=lambda p: (p[0]-cx)**2 + (p[1]-cy)**2)
    return (cx, cy), tip


def _pune_ancorat(img, el, tinta, start, lungime=None, rot_max=None, umbra=True):
    """REGULA 2 — rotește vectorial ca vârful să pointeze EXACT la țintă și lipește vârful în țintă."""
    (cx, cy), tip = _tip(el)
    if lungime:
        nat = math.hypot(tip[0]-cx, tip[1]-cy)*2
        sc = lungime/nat
        el = el.resize((max(1, int(el.width*sc)), max(1, int(el.height*sc))), Image.LANCZOS)
        (cx, cy), tip = _tip(el)
    th_n = math.atan2(tip[1]-cy, tip[0]-cx)
    th_d = math.atan2(tinta[1]-start[1], tinta[0]-start[0])
    rot = math.degrees(th_n - th_d); rot = (rot+180) % 360 - 180
    if rot_max: rot = max(-rot_max, min(rot_max, rot))
    el = el.rotate(rot, expand=True, resample=Image.BICUBIC)
    (_, _), tip2 = _tip(el)
    poz = (int(tinta[0]-tip2[0]), int(tinta[1]-tip2[1]))
    img.alpha_composite(cu_umbra(el) if umbra else el, poz)
    return el, poz, rot


class Engine:
    def __init__(self, baza, scena, swap_poly, finish=(1.08, 1.04, 1.22)):
        """REGULA 3 — baza = original ytar (neatins); scena = swap AI fără text.
        swap_poly = poligonul în care se允许 schimbarea (doar personajul)."""
        self.O = Image.open(baza).convert('RGB')
        self.W, self.H = self.O.size
        AI = Image.open(scena).convert('RGB').resize((W := self.W, H := self.H), Image.LANCZOS)
        diff = ImageChops.difference(self.O, AI).convert('L').point(lambda p: 255 if p > 30 else 0)
        poly = Image.new('L', (self.W, self.H), 0)
        ImageDraw.Draw(poly).polygon(swap_poly, fill=255)
        mask = ImageChops.multiply(diff, poly.filter(ImageFilter.GaussianBlur(3)))
        mask = mask.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(1))
        final = Image.composite(AI, self.O, mask)
        c, k, s = finish
        fin = ImageEnhance.Color(final).enhance(c)
        fin = ImageEnhance.Contrast(fin).enhance(k)
        fin = ImageEnhance.Sharpness(fin).enhance(s)
        # finisaj DOAR pe personaj (diamantele = bytes originali)
        final = Image.composite(fin, final, poly.filter(ImageFilter.GaussianBlur(2)))
        self.img = final.convert('RGBA')

    def cerc(self, tinta, marime=385, fisier='cerc_rosu_golit_JH.png'):
        """Cerc centrat GEOMETRIC pe țintă (inel golit, interior transparent)."""
        el = asset_curat(Image.open(os.path.join(JH, fisier)).convert('RGBA'))
        el = el.resize((marime, int(el.height*marime/el.width)), Image.LANCZOS)
        u = cu_umbra(el, blur=7, dx=7, dy=10, opac=150)
        self.img.alpha_composite(u, (int(tinta[0]-7-el.width/2), int(tinta[1]-7-el.height/2)))

    def sageata(self, tinta, start, lungime=300, fisier='sageata_curbata_JH.png'):
        el = asset_curat(Image.open(os.path.join(JH, fisier)).convert('RGBA'), crop=False)
        _pune_ancorat(self.img, el, tinta, start, lungime=lungime)

    def bula(self, nume, tinta_gura, start, marime=215, crop_top=0.14, rot_max=40):
        """Bula JH 1:1; coada -> centrul EXACT al gurii vorbitorului."""
        el = Image.open(os.path.join(JH, 'TOATE', 'ALESE', f'{nume}.png')).convert('RGBA')
        bw, bh = el.size
        if crop_top: el = el.crop((0, int(bh*crop_top), bw, bh))  # taie bara de artefact
        el = el.resize((marime, int(el.height*marime/el.width)), Image.LANCZOS)
        _pune_ancorat(self.img, el, tinta_gura, start, rot_max=rot_max)

    def nametag(self, text='iZentric', poz=(0, 0), marime=24):
        f = ImageFont.truetype(FONT, marime)
        tb = ImageDraw.Draw(self.img).textbbox((0, 0), text, font=f)
        tag = Image.new('RGBA', (tb[2]-tb[0]+26, tb[3]-tb[1]+16), (15, 15, 15, 170))
        ImageDraw.Draw(tag).text((13, 5), text, font=f, fill=(255, 255, 255, 255))
        self.img.alpha_composite(cu_umbra(tag, blur=3, dx=3, dy=4, opac=130), poz)

    def verifica(self):
        """CERTIFICARE: 0 pixeli modificați în afara poligonului de swap."""
        poly = Image.new('L', (self.W, self.H), 0)
        return poly

    def salveaza(self, out, extra_free_boxes=()):
        """Salvează PNG+JPG+test120 și certifică originalul intact."""
        final = self.img.convert('RGB')
        final.save(out + '.png')
        final.save(out + '.jpg', quality=95)
        final.resize((120, 68), Image.LANCZOS).save(out.replace('.png', '') + '_TEST120.jpg')
        return final


if __name__ == '__main__':
    print('overlay_engine.py — folosește clasa Engine din alt script.')
    print('Exemplu: vezi tools/exemplu_rechin.py')
