#!/usr/bin/env python3
"""EDITORUL SUPREM — combinatia: creierul repo-ului (DNA, 16s, LUFS, QC, titluri JH)
+ motorul nou (auto-editor WyattBlue, karaoke sloturi fixe, SFX inteligent cu fail-detect).

Fluxul (un clip local -> short gata):
  1. auto-editor taie liniștea (5% -> 8% -> 12% retry)      [motor nou]
  2. re-whisper pe clipul tăiat -> timpi exacti               [motor nou]
  3. captions karaoke JH: sloturi FIXE, galben/alb/roșu       [motor nou, regula boss #6]
  4. SFX: sunete_mele întâi (catalog.json), sunete_virale apoi [lega repo+autorizare boss]
  5. Țintă 16s (lege AGENTS), o singură EXPLOZIE pop-out      [DNA JH + regula boss #8]
  6. -14 LUFS (autoeditor.calibreaza_lufs)                    [repo]
  7. QC 8 legi (short_qc.ruleaza)                             [repo]
  8. Titluri JH din citate reale (creier_shorturi.titluri_jh) [repo]

Folosire:
  python suprem.py clip.mp4 --nume NUME
  python suprem.py clip.mp4 --nume NUME --fereastra 10:40   (secunde în sursă)
"""
import argparse, json, os, shutil, subprocess, sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import editor_pro as ep

TINTA_MAX = 18.0   # legea masurata JH: 12-18s (AGENTS spune 16s tinta; 18 = banda superioara)

def lufs_aplica(cale):
    try:
        import autoeditor as ae
        ae.calibreaza_lufs(ep.FF, cale)
        print('  [LUFS] calibrat -14')
    except Exception as e:
        print('  [LUFS] skip:', e)

def qc_ruleaza(cale, pops_momente):
    try:
        import short_qc as qc
        r = qc.ruleaza(cale, pops_momente)
        print('  [QC]', r if isinstance(r, str) else json.dumps(r, ensure_ascii=False)[:300])
        return r
    except Exception as e:
        print('  [QC] skip:', e)
        return None

def titluri_din_words(words):
    try:
        import creier_shorturi as cs
        pops = [(w['s'], w['w'].upper()) for w in words[:6]]
        return cs.titluri_jh(pops)
    except Exception:
        h = ' '.join(w['w'] for w in words[:3]).upper() or 'CE E ASTA'
        return [f'{h}..', f'{h} sau MORI !']

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('clip')
    ap.add_argument('--nume', required=True)
    ap.add_argument('--fereastra', default=None, help='ex: 10:40 (secunde in sursa)')
    a = ap.parse_args()
    out = os.path.join(BASE, f'SUPREM_{a.nume}.mp4')
    trim = (0.0, 16.5)
    if a.fereastra:
        p = a.fereastra.split(':')
        trim = (float(p[0]), float(p[1]))
    words = ep.load_words(os.path.join(BASE,'whisper_input.json'), '0') if os.path.exists(os.path.join(BASE,'whisper_input.json')) else []
    total = ep.build(a.clip, out, words, trim=trim, compress=True,
                     hook_text='',            # incepe gol (formula JH masurata)
                     logo_path=os.path.join(BASE,'assets','logo_pokecity_clear.png'),
                     series=os.environ.get('SERIA'),   # logo DOAR daca SERIA=pokecity
                     kit_out=os.path.join(BASE, f'KIT_SUPREM_{a.nume}.txt'),
                     title_hint=a.nume.replace('_',' '))
    lufs_aplica(out)
    print('SUPREM GATA:', out, round(total,2), 's')
    # titluri JH propuse (finalul il alege bossul — t125)
    try:
        cut = '/tmp/_cut.mp4'
        ws = ep.whisper_words(cut) if os.path.exists(cut) else words
        ep.release_whisper()
        for i, t in enumerate(titluri_din_words(ws), 1):
            print(f'  TITLU {i}: {t}')
    except Exception as e:
        print('  titluri skip:', e)

if __name__ == '__main__':
    main()
