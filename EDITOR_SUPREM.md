# EDITORUL SUPREM — combinatia (2026-10-06)

**Ce s-a combinat:** creierul repo-ului (legi, DNA, LUFS, QC, titluri) + motorul nou de
shorturi construit in sesiunea 2026-10-05/06 cu bossul (verificat pe disectii reale JH).

## Componente NOI aduse in repo
| Fisier | Ce face | De unde |
|---|---|---|
| `editor_pro.py` | motor shorturi: auto-editor (WyattBlue 5.4K⭐) taie linistea + re-whisper + captions karaoke sloturi FIXE (galben/alb/rosu) + SFX inteligent cu fail-detect + pop-out badge (JH) | sesiune workspace |
| `sunete_virale/` | pachet SFX autorizat EXPLICIT de boss in chat 2026-10-06 ("trebuie suntele din github") | Modern Meme SFX compilation |
| `suprem.py` | puntea: clip local -> short conform TUTUROR legilor (16s, LUFS, QC, titluri JH) | combinatie |
| `assets/Anton.ttf` | fontul captions (copiat din workspace) | workspace |

## Legile combinate (toate active)
1. 16s tinta / 12-18s banda (AGENTS + masuratori JH 1.2M/1M/874K)
2. Captions sloturi FIXE, doar culoarea se schimba (boss: "nu dezordonat")
3. Sunete: sunete_mele PRIORITATE -> sunete_virale doar la evenimente acoperite (catalog + context semantic)
4. Logo POKECITY doar la content din serie (SERIA=pokecity)
5. Fara CTA "episod complet"; "DA UN LIKE!" doar primele 2s
6. O singura EXPLOZIE (pop-out) pe vârful de energie
7. -14 LUFS obligatoriu (autoeditor.calibreaza_lufs)
8. QC short_qc BLOCANT: sub scor nu se livreaza (testat: 4/8 pe dummy = BLOCAT ✓)
9. Titluri: creier_shorturi.titluri_jh din citate reale; finalul il alege bossul (t125)
10. NICIODATA acelasi short/material de 2 ori (REGULI_BOSS #1)

## Folosire
```
export FFMPEG=/usr/bin/ffmpeg FFPROBE=/usr/bin/ffprobe WHISPER_MODEL=small
python suprem.py clip.mp4 --nume NUME [--fereastra 10:40]
SERIA=pokecity python suprem.py ...   (cand e content din serie)
```
WHISPER_MODEL: sandbox 2GB RAM = tiny; masina/Actions cu RAM = small (recomandat productie).

## Cunoscut / urmator pas
- calibrarea LUFS a repo-ului ajunge uneori -14.9 si QC (-14+-0.5) pică cu 0.4 — de aliniat
  tinta calibrului la -13.6 (marja QC) in produsie.
- `pip install auto-editor faster-whisper imageio-ffmpeg` la orice mediu nou.

## MINIATURI (a 2-a promisiune) — `miniaturi.py`
Cadru REAL (non-AI, legea canalului) din vârful de energie + SĂGEATA roșie (4/4 la top DNA) +
1-2 cuvinte max + logo serie doar la serie + checklist 8 legi BLOCANT + test 120px.
```
python miniaturi.py clip.mp4 --text "LAVA" --serie pokecity          # standard
python miniaturi.py clip.mp4 --text "FUGI" --contact                 # vezi 3 cadre, alege --cadru 2
python miniaturi.py clip.mp4 --text "AJUTOR" --t 42 --avatar av.png  # control total
```
