#!/usr/bin/env python3
r"""
AUTOEDITOR POKECITY v2 — MODUL POVESTE
Dintr-un live intreg construieste episoade CU INTELES, nu doar taieturi:

STRUCTURA unui episod (~2:50, ordenata ca o poveste pe care o inteleg copiii):
  0:00  INTRO-REACTIE (8s)  = cadru din MIJLOCUL momentului maxim: copilul vede
                            imediat ce va fi ("uite ce se intampla mai tarziu!")
  0:08  SETUP (55s)         = un moment tare de la INCEPUTUL live-ului (cum a pornit totul)
  1:03  DESFASURARE (55s)   = un moment din MIJLOCUL live-ului (actiunea creste)
  1:58  MOMENTUL MAXIM (52s)= EXPLOZIA completa, cu hook cu 15s inainte
  2:48  CTA + final brusc

Ordinea e CRONOLOGICA (inceput -> mijloc -> finalul live-ului) => povestea se
intelege fara sa sari. Texte de engagement pentru copii apar pe ecran:
  - la 0:12 "CE CREZI CĂ SE INTAMPLA? Scrie in comentarii!"
  - la 1:48 "ATENTIE! ACUM VINE MOMENTUL CEL MAI TARE!"
  - la final: LIKE + comentariu

Momentele sunt luate DIN TOT LIVE-UL (inceput/mijloc/sfarsit), nu doar dintr-o zona.

COMENZI:
  python autoeditor.py live.mp4                  -> episoade in modul poveste (recomandat)
  python autoeditor.py live.mp4 --clasic         -> mod v1 (o singura scena/episod)
  python autoeditor.py live.mp4 --doar-analiza   -> doar arata planul (rapid)
"""
import argparse
import base64
import json
import math
import os
import random
import time
import urllib.request
import urllib.error
import re
import shutil
import subprocess
import sys
from datetime import datetime
from idei_ai import idei_cu_ai, verifica_idee_cu_video
from editorial import approved_episodes, sound_catalogue, sound_filter
from performance import cached_json, file_digest, measured

# ═══════════ SETĂRI ═══════════
DURATA = 170          # lungime episod (2:50) — finalul taie BRUSC
MAX_EPISOADE = 8      # plafon calitate
HOOK_INAINTE = 15    # secunde inainte de explozie (hook-ul din care incepe scena)
INTERRUPTIE = 90      # distanta minima intre momente (mod clasic)
MUZICA_VOLUME = 0.12  # volum muzica de fundal
COLD_OPEN = 8         # secunde de reactie la inceput (teaserul momentului maxim)
P1 = 55               # SETUP (scena 1)
P2 = 55               # DESFASURARE (scena 2)
INTREBARE_TEXT = "CE CREZI CĂ SE INTÂMPLĂ? Scrie în comentarii!"
HYPE_TEXT = "ATENTIE! ACUM VINE MOMENTUL CEL MAI TARE!"
CTA_TEXT = "LIKE + scrie în comentarii ce vrei în episodul următor!"
NUME_CANAL = "iZentric"
# SLOTURI DE EFECTE: pui sunetul in assets/efecte/ cu numele de mai jos si e automat
# pe TOATE episoadele, pentru totdeauna. Zero configurare per video.
EFECTE_SLOTS = {
    "intrare":  0,          # la 0:00 — cold-open (sunet de intrare/drum roll)
    "hype":     None,       # se calculeaza: START_P3-10s (pe textul galben)
    "explozie": None,       # la START_P3 — exact la momentul maxim (airhorn/vine boom)
    "victorie": None,       # la durata-8s — dupa momentul maxim
    "final":    None,       # la durata-5s — pe CTA
}
# ══════════════════════════════

COLD_P1 = COLD_OPEN                    # 8
START_P2 = COLD_P1 + P1                # 63
START_P3 = START_P2 + P2               # 118  <- aici cade MOMENTUL MAXIM (min 2, regula MrBeast)


def gaseste_ffmpeg():
    p = shutil.which("ffmpeg")
    if p:
        return p
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        sys.exit("NU GASESC ffmpeg. Windows: winget install ffmpeg  (sau: pip install imageio-ffmpeg)")


def analiza_audio(ff, video):
    """Volum RMS pe fiecare secunda -> [(secunda, dB), ...]."""
    cmd = [ff, "-i", video, "-map", "a:0", "-af",
           "aresample=44100,asetnsamples=44100,astats=metadata=1:reset=1,"
           "ametadata=print:key=lavfi.astats.Overall.RMS_level:file=-",
           "-f", "null", "-"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    seria, t = [], None
    for linie in ((r.stdout or "") + "\n" + (r.stderr or "")).splitlines():
        m = re.search(r"pts_time:([\d.]+)", linie)
        if m:
            t = int(float(m.group(1)))
            continue
        m = re.search(r"RMS_level=(-?[\d.]+|-inf)", linie)
        if m and t is not None:
            v = m.group(1)
            seria.append((t, -70.0 if v == "-inf" else float(v)))
            t = None
    if not seria:
        sys.exit("NU AM PUTUT CITI AUDIO-ul. Fisierul are pista de sunet?")
    return seria


def detecteaza_explozii(seria):
    """Varfuri de excitatie: volum peste baza zonei lui (±30s). Intoarce (varfuri, scor_per_secunda)."""
    valori = [v for _, v in seria]
    n = len(valori)
    sm = [sum(valori[max(0, i-1):i+2]) / len(valori[max(0, i-1):i+2]) for i in range(n)]
    median = sorted(sm)[n // 2]
    varfuri, scor = [], [0.0] * n
    for i, v in enumerate(sm):
        baza = sm[max(0, i-30):i+31]
        s = max(v - (sum(baza) / len(baza)), v - median)   # premiaza si exploziile lungi
        scor[i] = max(0.0, s)
        if s >= 5 and v >= median + 3:
            if varfuri and i - varfuri[-1][0] <= 45:
                if s > varfuri[-1][1]:
                    varfuri[-1] = (i, s)
            else:
                varfuri.append((i, s))
    return varfuri, scor


def _top_scor(scor, a, b, folosite, tol):
    """Cel mai bun varf din fereastra [a,b) care nu e prea aproape de momentele folosite."""
    best = None
    for sec, s in VARFURI_GLOBALE:
        if a <= sec < b and all(abs(sec - u) >= tol for u in folosite):
            if best is None or s > best[1]:
                best = (sec, s)
    return best


def alege_povesti(varfuri, scor, live_len, durata, max_ep):
    """Construieste episoade-POVESTEA: 3 scene cronologice (inceput/mijloc/sfarsit) + intro-reactie.
    Fixeaza: C = momentul maxim; A = setup din prima treime; B = desfasurare dintre A si C."""
    global VARFURI_GLOBALE
    VARFURI_GLOBALE = varfuri
    p3 = durata - START_P3
    if p3 < 30:
        p3 = 30
    povesti, folosite = [], []
    for C, s in sorted(varfuri, key=lambda x: -x[1]):
        if len(povesti) >= max_ep:
            break
        if not (15 <= C <= live_len - 40):
            continue
        if any(abs(C - u) < durata + 60 for u in folosite):
            continue
        A = _top_scor(scor, 15, min(int(live_len * 0.35), C - 160), folosite, 100)
        if not A:
            continue
        B = _top_scor(scor, A[0] + 80, C - 90, folosite, 100)
        if not B:
            continue
        povesti.append({
            "tip": "poveste", "scor": round(s + A[1] + B[1], 1),
            "scene": [(C - 2, COLD_P1),
                      (A[0] - HOOK_INAINTE, P1),
                      (B[0] - 10, P2),
                      (C - HOOK_INAINTE, p3)],
            "varf": C, "folosite": [A[0], B[0], C]})
        folosite += [A[0], B[0], C]
    return povesti, p3


def alege_clasic(varfuri, scor, live_len, durata, max_ep, deja):
    """Mod v1: un moment = un episod. Umple catul ramas dupa povesti."""
    alese = []
    folosite = [x for p in deja for x in p.get("folosite", [p["varf"]])]
    for C, s in sorted(varfuri, key=lambda x: -x[1]):
        if len(deja) + len(alese) >= max_ep:
            break
        start = max(0, C - HOOK_INAINTE)
        if start + durata > live_len:
            continue
        if any(abs(C - u) < durata for u in folosite):
            continue
        energie = sum(sorted((x for x in scor[start:start + durata]), reverse=True)[:5])
        alese.append({"tip": "clasic", "scor": round(energie, 1), "varf": C,
                      "scene": [(start, durata)], "folosite": [C]})
        folosite.append(C)
    return alese


def rezolutie_sursa(ff, video):
    """Citeste rezolutia live-ului (din informatiile ffmpeg). Fallback: 1080p."""
    r = subprocess.run([ff, "-i", video], capture_output=True, text=True)
    m = re.findall(r"(\d{3,4})x(\d{3,4})", r.stderr or "")
    for w, h in m:
        if int(w) >= 600 and int(h) >= 300:
            return int(w), int(h)
    return 1920, 1080


EXT_AUDIO = {".mp3", ".wav", ".ogg", ".m4a", ".flac", ".aac", ".opus", ".wma"}

# folderele lui din sunete_mele/ -> categoria de SFX in care intra
FOLDERE_MELE = {
    "FERICIT": "fericit",
    "OASE_RUPTE": "cadere",
    "CADERE": "cadere",
    "SPERIAT": "speriat",
    "COMICE": "generic",
}


SLOT_FOLDERE = {"INTRARE", "HYPE", "EXPLOZIE", "VICTORIE", "FINAL"}


def aranjeaza_sunete_mele():
    """Compatibility no-op: creator originals are never deleted or rewritten.

    Editorial indexing now happens in editorial.sound_catalogue(). The former
    in-place deduplication/splitting could destroy supplied files on a failed cut.
    """
    return None

# tu arunci fisierul cu ORICE nume natural — noi il aranjam dupa cuvinte
CUVINTE_SUNET = {
    "fericit": ["prins", "capturat", "reusit", "castig", "victor", "yay", "wohoo",
                "fericit", "evolutie", "level", "incredibil", "wow", "epic"],
    "cadere": ["oase", "crac", "os rupt", "rupt", "cade", "cadere", "cazut", "cazi",
               "teava", "prabus", "pamant", "splash", "busit"],
    "speriat": ["speriat", "fric", "groaza", "sting", "hop", "tensiune", "creepy"],
    "hit": ["hit", "lovit", "bambus", "bonk", "pumn", "poc", "pach", "smash", "sabie", "damage"],
}
# rar = ramane surpriza pentru copii (ex: bambus hit max 2 pe episod)
MAX_PE_CATEG = {"hit": 2, "cadere": 3, "fericit": 3, "speriat": 3, "generic": 3}


def clasifica_sunet(cale):
    """Categoria dupa NUMELE fisierului, fara diacritice."""
    nume = (os.path.splitext(os.path.basename(cale))[0].lower()
            .replace("ă", "a").replace("â", "a").replace("î", "i")
            .replace("ș", "s").replace("ț", "t"))
    for tip, cuvinte in CUVINTE_SUNET.items():
        if any(c in nume for c in cuvinte):
            return tip
    return "generic"


def sunete_mele_pool():
    """Sunetele lui: fisierul poate fi aruncat DIRECT in sunete_mele/ sau in orice
    subfolder cu orice nume — il clasificam automat dupa nume. Doar cele 5 foldere
    de sloturi (INTRARE/HYPE/EXPLOZIE/VICTORIE/FINAL) au regula fixa de pozitie."""
    d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sunete_mele")
    pe_cat = {"fericit": [], "cadere": [], "speriat": [], "hit": [], "generic": []}
    if not os.path.isdir(d):
        return pe_cat
    for f in os.listdir(d):
        cale = os.path.join(d, f)
        if f.startswith(".") or os.path.splitext(f)[1].lower() not in EXT_AUDIO:
            continue
        if os.path.splitext(f)[0].lower() in EFECTE_SLOTS:
            continue          # numit ca un slot (ex: intrare.wav) = doar pe slot, nu si random
        pe_cat[clasifica_sunet(cale)].append(cale)   # aruncat in radacina = dupa nume
    for fold in os.listdir(d):
        sub = os.path.join(d, fold)
        if not os.path.isdir(sub) or fold.startswith(".") or fold.upper() in SLOT_FOLDERE:
            continue
        tip_fix = FOLDERE_MELE.get(fold.upper())      # folder cu nume cunoscut = regula tare
        for f in os.listdir(sub):
            if f.startswith(".") or os.path.splitext(f)[1].lower() not in EXT_AUDIO:
                continue
            cale = os.path.join(sub, f)
            pe_cat[tip_fix or clasifica_sunet(cale)].append(cale)
    return pe_cat


def gaseste_efecte(folder_assets):
    """Cauta efectele pe sloturi: INTAI in sunete_mele/<SLOT>/ (sunetele tale,
    alegere random daca sunt mai multe), apoi in assets/efecte/<nume>.
    lipsa = slotul se sari; prezenta = se aplica automat peste tot."""
    d = os.path.join(folder_assets, "efecte")
    baza_mele = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sunete_mele")
    gasite = {}
    for nume in EFECTE_SLOTS:
        candidati = []
        sub = os.path.join(baza_mele, nume.upper())
        if os.path.isdir(sub):
            candidati += [os.path.join(sub, f) for f in os.listdir(sub)
                          if os.path.splitext(f)[1].lower() in EXT_AUDIO and not f.startswith(".")]
        if os.path.isdir(baza_mele):
            candidati += [os.path.join(baza_mele, f) for f in os.listdir(baza_mele)
                          if os.path.splitext(f)[0].lower() == nume
                          and os.path.splitext(f)[1].lower() in EXT_AUDIO
                          and not f.startswith(".")]
        if os.path.isdir(d):
            candidati += [os.path.join(d, f) for f in os.listdir(d)
                          if os.path.splitext(f)[0].lower() == nume
                          and os.path.splitext(f)[1].lower() in EXT_AUDIO
                          and not f.startswith(".")]
        if candidati:
            gasite[nume] = random.choice(candidati)
    return gasite


def citeste_momente(path):
    """Citeste fisierul tau de momente: 'm:ss' sau 'h:mm:ss', unul pe linie, # = comentariu."""
    momente = []
    for linie in open(path, encoding="utf-8"):
        linie = linie.strip()
        if not linie or linie.startswith("#"):
            continue
        p = linie.split(":")
        try:
            if len(p) == 2:
                momente.append(int(p[0]) * 60 + int(p[1]))
            elif len(p) == 3:
                momente.append(int(p[0]) * 3600 + int(p[1]) * 60 + int(p[2]))
        except ValueError:
            print(f"   ! linie neinteleasa in {path}: {linie!r}")
    return sorted(set(momente))


def alege_din_momente(momente, varfuri, scor, live_len, durata, max_ep):
    """MODUL MANUAL: momentele tale devin MOMENTUL MAXIM al fiecarui episod.
    In jurul fiecaruia construiesc cea mai buna forma: poveste (setup+desfasurare
    gasite automat in restul live-ului) sau, daca nu exista material inainte, scena completa."""
    global VARFURI_GLOBALE
    VARFURI_GLOBALE = varfuri          # pentru setup/desfasurare caut in TOT live-ul
    p3 = max(30, durata - START_P3)
    povesti, folosite = [], []
    for C in momente:
        if len(povesti) >= max_ep:
            break
        if not (15 <= C <= live_len - 40):
            print(f"   ! momentul {_ts(C)} e prea aproape de inceput/final — sarit")
            continue
        if any(abs(C - u) < durata for u in folosite):
            print(f"   ! momentul {_ts(C)} se suprapune cu altul — sarit")
            continue
        A = _top_scor(scor, 15, min(int(live_len * 0.35), C - 160), folosite, 100)
        B = _top_scor(scor, A[0] + 80, C - 90, folosite, 100) if A else None
        s_C = round(scor[C], 1) if C < len(scor) else 0.0
        if A and B:
            povesti.append({"tip": "poveste", "scor": s_C, "manual": True, "varf": C,
                            "scene": [(C - 2, COLD_P1), (A[0] - HOOK_INAINTE, P1),
                                      (B[0] - 10, P2), (C - HOOK_INAINTE, p3)],
                            "folosite": [A[0], B[0], C]})
            folosite += [A[0], B[0], C]
        else:
            start = max(0, C - HOOK_INAINTE)
            if start + durata > live_len:
                continue
            povesti.append({"tip": "clasic", "scor": s_C, "manual": True, "varf": C,
                            "scene": [(start, durata)], "folosite": [C]})
            folosite.append(C)
    return povesti, p3


def _ts(sec):
    # format ASS cere OBLIGATORIU H:MM:SS.CC (centisecunde) — fara ele libass arunca linia
    sec = max(0.0, float(sec))
    cs = int(round(sec * 100))
    h, rest = divmod(cs, 360000)
    m, rest = divmod(rest, 6000)
    s, cc = divmod(rest, 100)
    return f"{h}:{m:02d}:{s:02d}.{cc:02d}"


def scrie_ass(nume, durata, poveste, impact_words=None):
    """Textele pe ecran: semnatura colt + intrebare (0:12) + hype (inainte de maxim) + CTA final."""
    linii = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1920", "PlayResY: 1080", "",
             "[V4+ Styles]",
             "Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, BorderStyle",
             "Style: CTA,Arial,84,&H00FFFFFF,&H00000000,&H80000000,1,4,0,2,60,60,90,1",
             "Style: WM,Arial,44,&H00FFFFFF,&H00000000,&H80000000,1,3,0,7,40,40,30,1",
             "Style: HYPE,Arial,96,&H0000E5FF,&H00000000,&H80000000,1,5,0,2,60,60,90,1",
             "Style: IMPACT,Arial,96,&H00FFFFFF,&H00000000,&H70000000,1,4,0,5,40,40,40,3",
             "Style: POP,Arial,88,&H0000FFFF,&H00000000,&H80000000,1,6,0,2,60,60,150,1",
             "", "[Events]",
             "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    if NUME_CANAL:
        linii.append(f"Dialogue: 0,0:00:00.00,{_ts(durata)},WM,,0,0,0,,{NUME_CANAL}")
    if poveste and poveste.get("tip") == "poveste":
        linii.append(f"Dialogue: 0,{_ts(12)},{_ts(21)},CTA,,0,0,0,,{INTREBARE_TEXT}")
        linii.append(f"Dialogue: 0,{_ts(START_P3 - 10)},{_ts(START_P3 - 2)},HYPE,,0,0,0,,{HYPE_TEXT}")
    linii.append(f"Dialogue: 0,{_ts(max(0, durata-5))},{_ts(durata)},CTA,,0,0,0,,{CTA_TEXT}")
    linii.append(f"Dialogue: 0,{_ts(max(0, durata-5))},{_ts(durata)},CTA,,0,0,0,,{{\\fs56\\c&H0000E5FF&\\pos(960,700)}}ABONEAZĂ-TE ca să nu pierzi seria!")
    # SUBTITRARI-POP: replici-cheie, MARI si GALBENE, doar la momentele alese de AI
    if os.environ.get("AE_POPS", "1") != "0":
        for t_pop, text_pop in (poveste.get("_pops") or []):
            linii.append(f"Dialogue: 0,{_ts(t_pop)},{_ts(t_pop + 2.6)},POP,,0,0,0,,{text_pop}")
    # CUVINTE-IMPACT (stil JocuriHorror: „ZIAR" in cutie mare la obiecte): apar 0.8s, centrate, pe sunetele lui
    for t, cuvant in (impact_words or []):
        linii.append(f"Dialogue: 0,{_ts(t)},{_ts(t + 0.8)},IMPACT,,0,0,0,,"
                     f"{{\\pos(960,400)}}{cuvant}")
    open(nume, "w", encoding="utf-8").write("\n".join(linii) + "\n")
    return os.path.basename(nume)


def fps_sursa(ff, video):
    """FPS-ul sursei (fallback 30)."""
    r = subprocess.run([ff, "-i", video], capture_output=True, text=True, timeout=60)
    import re as _re2
    m = _re2.search(r"([0-9.]+) fps", r.stderr)
    return float(m.group(1)) if m else 30.0


def gaseste_meme(assets_dir):
    """Clipurile greenscreen ale creatorului: assets/meme/*.mp4|webm|mov|gif."""
    d = os.path.join(assets_dir, "meme")
    ext = {".mp4", ".webm", ".mov", ".gif", ".mkv"}
    return [os.path.join(d, f) for f in (os.listdir(d) if os.path.isdir(d) else [])
            if os.path.splitext(f)[1].lower() in ext and not f.startswith(".")]


def masoara_lufs(ff, cale):
    """Masura loudness-ul real (LUFS integrat) + true peak dintr-un fisier."""
    r = subprocess.run([ff, "-i", cale, "-af",
                        "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json",
                        "-f", "null", "-"], capture_output=True, text=True, timeout=600)
    j = r.stderr[r.stderr.find("{"):r.stderr.rfind("}") + 1]
    try:
        d = json.loads(j)
        return float(d.get("input_i", -70)), float(d.get("input_tp", 0))
    except Exception:
        return None, None


@measured("master-audio")
def calibreaza_lufs(ff, cale):
    """MASTER pentru YouTube (normalizeaza la -14 LUFS, NU amplifica ce e linistit!).
    Metoda de studio: 2 treceri loudnorm in mod LINIAR (gain static — zero pompare,
    plafon true-peak exact). -> (LUFS inainte, LUFS dupa) sau None."""
    if os.environ.get("AE_LUFS") == "0":
        return None
    i_in, peak = masoara_lufs(ff, cale)
    if i_in is None or peak is None or not math.isfinite(i_in) or not math.isfinite(peak):
        return None
    if abs(-14.0 - i_in) <= 0.4 and peak <= -1:                # deja in tinta
        return (i_in, i_in)
    tmp = cale.replace(".mp4", "_cal.mp4")
    i_out = i_in
    for trecere in range(2):
        d = masoara_lufs_json(ff, cale)
        if not d:
            return None
        lin = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={d['input_i']}:"
               f"measured_TP={d['input_tp']}:measured_LRA={d['input_lra']}:"
               f"measured_thresh={d['input_thresh']}:offset={d.get('target_offset', 0)}:linear=true,"
               "aresample=48000")
        r = subprocess.run([ff, "-y", "-i", cale, "-af", lin,
                            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                            "-movflags", "+faststart", tmp],
                           capture_output=True, text=True, timeout=900)
        if r.returncode != 0 or not os.path.exists(tmp):
            return None
        os.replace(tmp, cale)
        i_out, peak = masoara_lufs(ff, cale)
        if i_out is None or peak is None or not math.isfinite(i_out) or not math.isfinite(peak):
            return None
        if abs(-14.0 - i_out) <= 0.6 and peak <= -1:
            break
    print(f"   CALIBRARE YOUTUBE: {i_in:.1f} -> {i_out:.1f} LUFS (tinta -14, varfuri <= -1.5 dBTP)")
    return (i_in, i_out) if abs(-14.0 - i_out) <= 1 and peak <= -1 else None


def masoara_lufs_json(ff, cale):
    """Toate campurile de masurare loudnorm (pt trecerea liniara)."""
    r = subprocess.run([ff, "-i", cale, "-af",
                        "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json",
                        "-f", "null", "-"], capture_output=True, text=True, timeout=600)
    j = r.stderr[r.stderr.find("{"):r.stderr.rfind("}") + 1]
    try:
        return json.loads(j)
    except Exception:
        return None


def expr_zoom(poz, sfarsit, varf, crestere, fps, urcare, coborare):
    """O fereastra de zoom pentru zoompan: urca la varf, tine, coboara. In cadrane."""
    a, b = int(poz * fps), int(sfarsit * fps)
    return f"(between(in,{a},{b})*{crestere}*min((in-{a})/{max(1, int(urcare * fps))},1)*min(max(({b}-in)/{max(1, int(coborare * fps))},0),1))"


@measured("render-episode")
def comanda_randare(ff, video, poveste, durata, folder, muzica, logo, nr, efecte=None, tinta_h=0, sfx_rand=None, confeti=None, h_out=1080, dim=None, seria=None, meme=None):
    """O comanda ffmpeg: concateneaza scenele (+intro-reactia), pune logo, textele, muzica."""
    # cuvant-impact pe fiecare sunet al lui (ca „ZIAR"-ul de la JocuriHorror)
    cuvant_pt = {"hit": "PUM!", "cadere": "PAH!", "fericit": "WOW!", "speriat": "HOP!", "generic": "BAM!"}
    impact_words = [(max(0.2, t), cuvant_pt.get(clasifica_sunet(cale), "BAM!"))
                    for t, cale, _ in (sfx_rand or [])]
    ass = scrie_ass(os.path.join(folder, f"EP{nr:02d}.ass"), durata, poveste, impact_words)
    cmd = [ff, "-y"]
    # sursa MARE (live intreg 2h+): 6+ decodatoare simultane pe acelasi fisier = RAM explosion.
    # pre-taiem fiecare scena o data in clip mic (refolosibil la rerulare) si randam din clipuri.
    big = len(poveste["scene"]) > 1 and os.path.getsize(video) > 200 * 1024 * 1024
    tmp_sc = os.path.join(folder, "scene_tmp")
    if big:
        os.makedirs(tmp_sc, exist_ok=True)
    for i, (start, lung) in enumerate(poveste["scene"]):
        if big:
            clip = os.path.join(tmp_sc, f"EP{nr:02d}_s{i}.mp4")
            if not os.path.exists(clip):
                print(f"   pre-taie scena {i+1}/{len(poveste['scene'])} ({int(lung)}s)...", flush=True)
                subprocess.run([ff, "-y", "-ss", str(max(0, start)), "-t", str(lung), "-i", video,
                                "-r", "30", "-c:v", "libx264", "-preset", "ultrafast", "-crf", "18",
                                "-c:a", "aac", "-b:a", "192k", clip], capture_output=True)
            cmd += ["-i", clip]
        else:
            cmd += ["-ss", str(max(0, start)), "-t", str(lung), "-i", video]
    filtre, n = [], len(poveste["scene"])
    # concat vrea perechi INTERLEAVED per segment: [0:v][0:a][1:v][1:a]...
    concat_in = "".join(f"[{i}:v][{i}:a]" for i in range(n))
    filtre.append(f"{concat_in}concat=n={n}:v=1:a=1[vc][ac]")
    # NORMALIZARE VOCE (standard streaming): -16 LUFS constant, indiferent cat de departe
    # era microfonul — copiii nu trebuie sa joace cu volumul
    filtre.append("[ac]loudnorm=I=-16:TP=-1.5:LRA=11[acn]")
    # calitate: daca cerem 2K si sursa e mai mica -> scalare LANCZOS + usor sharpen
    # (YouTube da bitrate mai mare la 1440p => imaginea supravietuieste mai bine re-encodarii lor)
    # GRADE stil MrBeast: saturatie+contrast usor ridicate — cadrul "pica" si la
    # marimea de feed din telefon (confirmat: stilul lui e bright/saturated/high-contrast)
    vc_src = "[vc]"
    if os.environ.get("AE_GRADE", "1") != "0":
        filtre.append("[vc]eq=contrast=1.06:saturation=1.18[vcg]")
        vc_src = "[vcg]"
    if tinta_h:
        filtre.append(f"{vc_src}scale=-2:{tinta_h}:flags=lanczos,unsharp=5:5:0.3:5:5:0.0[vc2]")
        src_vc = "[vc2]"
    else:
        src_vc = vc_src
    # ZOOM-uri stil MrBeast: punch-in la cold-open, la textul HYPE si la CLIMAX.
    # zoompan = cadran cu cadran, centrat, max 1.14 (zero pierdere vizibila).
    zoom_txt = ""
    if dim and os.environ.get("AE_ZOOM", "0") == "1":   # zoom OFF by default (user: "fara zoom-uri degeaba")
        w_z, h_z, fps_z = dim
        if tinta_h:
            h_z = tinta_h
            w_z = int((dim[0] * tinta_h / dim[1]) // 2 * 2)
        w_z, h_z = max(2, int(w_z) // 2 * 2), max(2, int(h_z) // 2 * 2)
        ferestre = [(0.4, 6.5, 0.07, 0.5, 0.8),                                # cold-open punch
                    (START_P3 - 10, START_P3 - 4, 0.05, 0.6, 1.0),             # sub textul HYPE
                    (START_P3, min(START_P3 + 15, max(durata - 8, START_P3 + 6)), 0.14, 1.2, 1.0)]
        ferestre = [(a, min(b, durata - 1), c, d, e) for a, b, c, d, e in ferestre if a < durata - 2]
        cand = []
        # PUNCH-uri DINAMICE la varfurile REALE de energie (max 4) — ritmul masurat la
        # JocuriHorror: 178 de schimbari vizuale in 19.8 min = una la ~6.7s. Frame-ul
        # nostru are o singura camera; punch-ul pe energie e echivalentul editorial.
        if seria and poveste.get("scene"):
            idx_map = {int(s): v for s, v in seria}
            vol_ep = []
            for start, lung in poveste["scene"]:
                for t in range(int(lung)):
                    vol_ep.append(idx_map.get(int(start) + t))
            vii = sorted(v for v in vol_ep if v is not None)
            baza_v = vii[len(vii) // 2] if vii else 0
            for t, v in enumerate(vol_ep):
                if v is None or v < baza_v + 2 or not (10 <= t <= durata - 12):
                    continue
                if any(vol_ep[j] is not None and vol_ep[j] > v for j in range(max(0, t - 3), min(len(vol_ep), t + 4))):
                    continue                       # nu e maxim local
                if any(abs(t - x) < 12 for x in cand) or any(abs(t - a2) < 6 for a2, _, _, _, _ in ferestre):
                    continue                       # prea aproape de alt punch
                cand.append(t)
                if len(cand) >= 4:
                    break
            ferestre += [(t, min(t + 2.5, durata - 1), 0.10, 0.3, 0.9) for t in cand]
        # RESPIRAT: cadrul NU sta niciodata pe loc — oscilatie discreta (perioada 8s, pana la 1.035)
        respir = "0.035*(0.5-0.5*cos(in*2*PI/" + str(max(1, int(8 * fps_z))) + "))"
        zexpr = ("1+" + respir + ("+" + "+".join(expr_zoom(a, b, 0, c, fps_z, d, e)
                 for a, b, c, d, e in ferestre) if ferestre else ""))
        poveste["_zoom_n"] = len(ferestre)
        zoom_txt = (f",fps={fps_z},zoompan=z='{zexpr}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
                    f":d=1:s={w_z}x{h_z}:fps={fps_z}")
    if logo:
        cmd += ["-i", logo]
        li = n
        filtre += [f"[{li}:v]scale=140:-1[lg]",
                   f"{src_vc}scale=trunc(iw/2)*2:trunc(ih/2)*2[b0]",
                   "[b0][lg]overlay=W-w-24:24[b1]",
                   f"[b1]subtitles={ass}[vout]"]
    else:
        filtre += [f"{src_vc}scale=trunc(iw/2)*2:trunc(ih/2)*2{zoom_txt},subtitles={ass}[vout]"]
    vmap = "[vout]"
    if confeti:
        cmd += ["-i", confeti]
        ci = n + (1 if logo else 0)
        # confeti.webm = 2s cu fundal transparent; tpad=clone (transparent) pana la moment, apoi overlay
        intarziere = max(0, durata - 8)
        filtre.append(f"[{ci}:v]scale=-2:{h_out},chromakey=0x000000:0.15:0.02,tpad=start_duration={intarziere}:start_mode=clone[cf]")
        filtre.append(f"{vmap}[cf]overlay=0:0:eof_action=pass[vfin]")
        vmap = "[vfin]"
    harta_a = "[ac]"
    if muzica:
        cmd += ["-stream_loop", "-1", "-i", muzica]
        mi = n + (1 if logo else 0) + (1 if confeti else 0)
        filtre.append(f"[{mi}:a]volume={MUZICA_VOLUME}[bg]")
    # efectele pe sloturi (zero-config): adelay la timpul lor, apoi amix cu tot restul
    intrari_sfx = []
    if efecte:
        timpi = {"intrare": 0, "hype": START_P3 - 10, "explozie": START_P3,
                 "victorie": max(0, durata - 8), "final": max(0, durata - 5)}
        for k, (slot, cale) in enumerate(efecte.items()):
            cmd += ["-i", cale]
            idx = n + (1 if logo else 0) + (1 if confeti else 0) + (1 if muzica else 0) + k
            ms = int(timpi[slot] * 1000)
            filtre.append(f"[{idx}:a]adelay={ms}:all=1,volume=0.9[s{idx}]")
            intrari_sfx.append(f"[s{idx}]")
    intrari_rand = []
    if sfx_rand:
        baza_idx = n + (1 if logo else 0) + (1 if confeti else 0) + (1 if muzica else 0) + (len(efecte) if efecte else 0)
        for j, (t, cale, vol) in enumerate(sfx_rand):
            cmd += ["-i", cale]
            idx = baza_idx + j
            if poveste.get("ai_verified"):
                filtre.append(sound_filter(idx, t, f"x{idx}"))
            else:
                filtre.append(f"[{idx}:a]adelay={int(t*1000)}:all=1,volume={vol:.2f}[x{idx}]")
            intrari_rand.append(f"[x{idx}]")
    # MEME-uri greenscreen (assets/meme/): apar scurt (1.6s) pe momentele comice,
    # jos in stanga, decupate cu chromakey — ca la editorii de 40-120$/video
    if meme:
        momente_meme = [t for t, _, _ in (sfx_rand or [])][:3] or [round(durata * 0.35, 1), round(durata * 0.65, 1)]
        momente_meme = [t for t in momente_meme if 6 <= t <= durata - 10][:3]
        baza_idx = n + (1 if logo else 0) + (1 if confeti else 0) + (1 if muzica else 0) + (len(efecte) if efecte else 0) + (len(sfx_rand) if sfx_rand else 0)
        prev = vmap
        for j, t0 in enumerate(momente_meme):
            cale = random.choice(meme)
            cmd += ["-i", cale]
            idx_m = baza_idx + j
            # tpad clone = meme-ul incepe la t0 (secondary input-ul altfel se consuma din t=0 si overlay-ul
            # nu-l mai gaseste la momentul enable — BUG prins prin verificare vizuala)
            filtre.append(f"[{idx_m}:v]scale=-2:{max(2, h_out // 4)},"
                          f"tpad=start_duration={t0}:start_mode=clone,"
                          f"chromakey=0x00FF00:0.25:0.08[mk{idx_m}]")
            filtre.append(f"{prev}[mk{idx_m}]overlay=x=24:y=H-h-24:enable='between(t,{t0},{t0 + 1.6})':eof_action=pass[mm{idx_m}]")
            prev = f"[mm{idx_m}]"
        if prev != vmap:
            vmap = prev
            poveste["_meme_n"] = len(momente_meme)
    amix_in = "[acn]" + ("[bg]" if muzica else "") + "".join(intrari_sfx) + "".join(intrari_rand)
    filtre.append(f"{amix_in}amix=inputs={amix_in.count('[')}:duration=first:normalize=0[a0]")
    filtre.append(f"[a0]afade=t=out:st={max(0, durata-2)}:d=2[aout]")
    harta_a = "[aout]"
    out = f"EP{nr:02d}.mp4"
    crf = "20" if tinta_h or poveste.get("ai_verified") else "23"
    preset = "medium" if tinta_h or poveste.get("ai_verified") else "veryfast"
    # mediu sarac (sandbox 2GB): 30fps + x264 econom (AE_USOR=1) — aceeasi calitate perceputa, RAM redus de 3-4x
    usor = ["-r", "30", "-preset", "veryfast", "-x264opts", "rc-lookahead=20:ref=2:threads=2"] if os.environ.get("AE_USOR") == "1" and not poveste.get("ai_verified") else []
    cmd += ["-filter_complex", ";".join(filtre), "-map", vmap, "-map", harta_a,
            "-c:v", "libx264", "-preset", preset, "-crf", crf, *usor,
            "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out]
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=folder)
    if r.returncode != 0 or not os.path.exists(os.path.join(folder, out)):
        print(f"  ! EP{nr:02d}: ffmpeg a esuat: {(r.stderr or '')[-800:]}")
        try:
            open(os.path.join(folder, f"EROARE_EP{nr:02d}.log"), "w", encoding="utf-8").write(r.stderr or "")
        except Exception:
            pass
        open(os.path.join(folder, "err.txt"), "w").write("CMD: " + " ".join(cmd) + "\n\nSTDERR:\n" + (r.stderr or ""))
        return None
    return out


def cadre_miniatura(ff, episod, moment_relativ, nr, folder):
    """3 cadre REALE din clip, aproape de momentul maxim. Fara AI."""
    cadre = []
    for k, dt in enumerate([-6, 0, 6]):
        t = max(0, moment_relativ + dt)
        cale = f"EP{nr:02d}_cadru{k+1}.jpg"
        r = subprocess.run([ff, "-y", "-ss", str(t), "-i", episod,
                            "-frames:v", "1", "-q:v", "3", cale],
                           capture_output=True, text=True, cwd=folder)
        if r.returncode == 0 and os.path.exists(os.path.join(folder, cale)):
            cadre.append(cale)
    return cadre


FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def font_gros(size):
    """Font bold cross-platform (linux/windows/mac), cu fallback sigur."""
    from PIL import ImageFont
    for p in (FONT_BOLD, "C:/Windows/Fonts/arialbd.ttf",
              "/System/Library/Fonts/Supplemental/Arial Bold.ttf"):
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def fa_miniatura(cale_cadru, cale_out, titlu, logo=None, sageata=None):
    """MINIATURA in stil Minecraft, EDITATA din cadru REAL al live-ului
    (niciodata generata cu AI — regula canalului):
    crop 16:9 -> saturatie/contrast/sharpness boost -> logo -> text mare cu contur."""
    from PIL import Image, ImageEnhance, ImageDraw, ImageFont
    img = Image.open(cale_cadru).convert("RGB")
    w, h = img.size
    tinta = 1280 / 720
    if w / h > tinta:
        nw = int(h * tinta); x0 = (w - nw) // 2; img = img.crop((x0, 0, x0 + nw, h))
    else:
        nh = int(w / tinta); y0 = (h - nh) // 2; img = img.crop((0, y0, w, y0 + nh))
    img = img.resize((1280, 720), Image.LANCZOS)
    img = ImageEnhance.Color(img).enhance(1.28)      # culori tari = stilul Minecraft
    img = ImageEnhance.Contrast(img).enhance(1.10)
    img = ImageEnhance.Sharpness(img).enhance(1.15)
    d = ImageDraw.Draw(img)
    if logo and os.path.exists(logo):
        lg = Image.open(logo).convert("RGBA")
        lg.thumbnail((170, 170))
        img.paste(lg, (24, 24), lg)
    # SAGETA ROSIE stil Minecraft-kids: arata cat punctul de interes + cerc de accent
    if sageata:
        try:
            ax, ay = sageata[0], sageata[1]
            d.ellipse([ax - 95, ay - 95, ax + 95, ay + 95], outline=(255, 40, 40), width=14)
            cx = 1120
            cy = 140
            ang = math.atan2(ay - cy, ax - cx)
            gh = 70
            d.line([cx, cy, cx + int((ax - cx) * 0.86), cy + int((ay - cy) * 0.86)],
                   fill=(255, 40, 40), width=22)
            ex, ey = cx + int((ax - cx) * 0.86), cy + int((ay - cy) * 0.86)
            for da in (ang + 2.6, ang - 2.6):
                d.line([ex, ey, ex + int(gh * math.cos(da)), ey + int(gh * math.sin(da))],
                       fill=(255, 40, 40), width=22)
        except Exception:
            pass
    toate = [c for c in titlu.upper().replace("!", "").replace("?", "").replace("…", "").split() if len(c) > 1]
    # pastram cuvintele CU GREUTATE (nume/caietele de guerre), nu pe cele mici (CE, PE, UN)
    cuvinte = toate[:5]
    if len(toate) > 5:
        mici = {c for c in toate if len(c) <= 2}
        cuvinte = [c for c in toate if c not in mici][:5]
    linie = " ".join(cuvinte) if cuvinte else "CE S-A INTAMPLAT!"
    size = 96
    fnt = font_gros(size)
    while d.textlength(linie, font=fnt) > 1200 and size > 44:
        size -= 4
        fnt = font_gros(size)
    bb = d.textbbox((0, 0), linie, font=fnt, stroke_width=10)
    x = (1280 - (bb[2] - bb[0])) // 2
    y = 720 - (bb[3] - bb[1]) - 46
    d.text((x, y), linie, font=fnt, fill=(255, 255, 255), stroke_width=10, stroke_fill=(0, 0, 0))
    img.save(cale_out, quality=90)
    return cale_out


def gaseste_sfx_random(assets_dir):
    """Pool-ul de sunete comice: assets/efecte/random/ (orice fisiere audio)."""
    d = os.path.join(assets_dir, "efecte", "random")
    pool = []
    if os.path.isdir(d):
        for f in sorted(os.listdir(d)):
            if f.startswith("."):
                continue
            if os.path.splitext(f)[1].lower() in (".mp3", ".wav", ".ogg", ".m4a", ".flac", ".opus", ".aac"):
                pool.append(os.path.join(d, f))
    return pool


def alege_sfx_random(pool, durata):
    """2-3 accente comice pe timeline, la intamplare DAR precise: evitam
    intro-ul, fereastra momentului maxim, finalul (CTA) si pauzele mici intre ele."""
    protejate = [(0, 12), (START_P3 - 16, START_P3 + 18), (durata - 14, durata)]
    cate = 2 if durata < 200 else 3
    alese, incercari = [], 0
    while len(alese) < cate and incercari < 200:
        incercari += 1
        t = random.uniform(15, durata - 18)
        if any(a <= t <= b for a, b in protejate):
            continue
        if any(abs(t - x) < 25 for x, _, _ in alese):
            continue
        cale = random.choice(pool)
        vol = random.uniform(0.55, 0.85)
        alese.append((t, cale, vol))
    return sorted(alese)


CATEG_SFX = {
    "fericit": ["am reusit", "l-am prins", "am prins", "bravo", "cistig", "castig",
                 "fericit", "incredibil", "super", "wow", "epic", "l-am batut",
                 "am batut", "yes", "tare", "finalul"],
    "cadere": ["a cazut", "cazut", "s-a lovit", "sa lovit", "busit", "doare",
                "sparge", "spart", "a picat", "picat", "boom", "os"],
    "speriat": ["frica", "groaza", "speriat", "hop", "ce e asta", "ce-a fost", "stai ce"],
    "hit": ["lovit", "lovesc", "loveste", "lovire", "hit", "bambus", "bambusul", "sabie", "sabia",
            "pumn", "pumnul", "l-a batut", "damage", "pocnit", "l-am lovit", "atac"],
}


def detecteaza_evenimente(transcript):
    """Momente-semnal din CE AI ZIS: 'am prins!' = fericit, 'a cazut!' = cadere etc.
    -> [(secunda_live, tip)]. Fara transcript -> []."""
    import re as _re
    ev = []
    if not transcript:
        return ev
    for a, b, txt in transcript:
        tl = _re.sub(r"[^a-zăâîșț ]", " ", (txt or "").lower())
        tl = " " + tl + " "
        for tip, cuvinte in CATEG_SFX.items():
            if any(f" {c} " in tl for c in cuvinte):
                ev.append((int(a), tip))
                break
    ev.sort()
    curate = []
    for t, tip in ev:                      # max 1 eveniment/tip la 20s
        if not any(tt == tip and abs(t - x) < 20 for x, tt in curate):
            curate.append((t, tip))
    return curate


def live_to_episod(t_live, scene):
    """Un moment din live -> pozitia lui in episodul concatenat (None daca nu e in scena)."""
    offset = 0.0
    for start, dur in scene:
        if start <= t_live < start + dur:
            return offset + (t_live - start)
        offset += dur
    return None


CUV_POP = ("ha", "haha", "hahaha", "lol", "uau", "wow", "boom", "nu se poate", "prins",
           "prindem", "rar", "legendar", "incredibil", "atentie", "look", "frate", "boa",
           "s-a dus", "a cazut", "epic", "serios")


def pops_subtitrari(transcript, scene, durata):
    """SUBTITRARI-POP: doar la momentele-cheie (rasete, prinderi, hype) apare pe ecran
    replica, MARE si GALBENA (2.6s). Alege automat din transcriptul live-ului.
    -> [(t_in_episod, text)]; max 6 pe episod, minim 18s intre ele."""
    if not transcript:
        return []
    candit = []
    for a0, _b, t in transcript:
        tt = t.strip()
        if not (8 <= len(tt) <= 48) or len(tt.split()) < 2:
            continue
        tl = tt.lower()
        scor = sum(2 for c in CUV_POP if c in tl) + (1 if tt.isupper() or tt[:-1].isupper() else 0)
        if scor <= 0:
            continue
        poz = live_to_episod(a0, scene)
        if poz is None or poz < 14 or poz > durata - 9:
            continue
        candit.append((scor, poz, tt))
    candit.sort(key=lambda x: (-x[0], x[1]))
    alese = []
    for _scor, poz, tt in candit:
        if any(abs(poz - p) < 18 for p, _t in alese):
            continue
        alese.append((poz, tt.upper()))
        if len(alese) >= 6:
            break
    return sorted(alese)


def alege_sfx_inteligent(pool, durata, transcript, scene):
    """PRECIS, nu doar random: evenimentele REALE din vorbire primeste sunetul POTRIVIT
    (fericit_* la 'am prins!', cadere_* la 'a cazut!'). Daca evenimentele sunt rare,
    umple cu random in puncte sigure. -> [(t_episod, fisier, volum)]"""
    pe_cat = {"fericit": [], "cadere": [], "speriat": [], "hit": [], "generic": []}
    for cale in pool:
        nume = os.path.splitext(os.path.basename(cale))[0].lower()
        pus = False
        for tip in ("fericit", "cadere", "speriat", "hit"):
            if nume.startswith(tip + "_") or nume.startswith(tip + "-"):
                pe_cat[tip].append(cale)
                pus = True
                break
        if not pus:
            pe_cat["generic"].append(cale)
    for tip, lst in sunete_mele_pool().items():
        pe_cat[tip].extend(lst)

    alese = []
    folosite = {}
    for t_live, tip in detecteaza_evenimente(transcript):
        if len(alese) >= 4:
            break
        t_ep = live_to_episod(t_live, scene)
        if t_ep is None or not (8 <= t_ep <= durata - 8):
            continue
        if any(abs(t_ep - x) < 8 for x, _, _ in alese):
            continue
        if folosite.get(tip, 0) >= MAX_PE_CATEG.get(tip, 3):
            continue          # ex: bambus hit max 2/episod — rar = copiii raman pe tentă
        candidati = pe_cat.get(tip) or pe_cat["generic"]
        if candidati:
            alese.append((t_ep, random.choice(candidati), random.uniform(0.75, 0.95)))
            folosite[tip] = folosite.get(tip, 0) + 1
    protejate = [(0, 12), (durata - 14, durata)]
    incercari = 0
    while len(alese) < 2 and incercari < 100 and pe_cat["generic"]:
        incercari += 1
        t = random.uniform(15, durata - 18)
        if any(a <= t <= b for a, b in protejate) or any(abs(t - x) < 25 for x, _, _ in alese):
            continue
        alese.append((t, random.choice(pe_cat["generic"]), random.uniform(0.55, 0.85)))
    return sorted(alese)


def motiv_de_exista(episoade, prag=0.55):
    """Regula: un episod exista DOACA daca are motiv fata de cel mai bun.
    Prag: scor >= 55% din scorul celui mai tare episod din live.
    Un live de 4h cu 1 poveste excelenta + 5 mediocre = 1 EPISOD."""
    if len(episoade) <= 1:
        return episoade
    maxs = max(e["scor"] for e in episoade)
    bune = [e for e in episoade if e["scor"] >= prag * maxs]
    caze = len(episoade) - len(bune)
    if caze:
        print(f"   MOTIV DE EXISTA: {caze} episoade CAZUTE (sub {int(prag*100)}% din cel mai tare) — umplutura nu se posteaza")
    return bune


def comprima_zone_moarte(sm, scene, durata, min_scena=9):
    """STILUL JOH (confirmat in transcriptele lor): narare CONTINUA, fara goluri.
    Taie segmentele moarte >=min_scena din mijlocul scenelor; scena care pierde
    peste 35% din durata ramane intreaga (nu o facem neintelegibila).
    -> (scene_noi, secunde_taiate)"""
    if not sm:
        return scene, 0
    baza = sorted(sm)[len(sm) // 2]
    noi, taiate_total = [], 0
    for start, dur in scene:
        moarte, curent = [], [None, None]
        for t in range(int(dur)):
            idx = int(start) + t
            viu = 0 <= idx < len(sm) and sm[idx] >= baza + 2
            if not viu:
                if curent[0] is None:
                    curent[0] = t
                curent[1] = t
            else:
                if curent[0] is not None and curent[1] - curent[0] + 1 >= min_scena:
                    moarte.append((curent[0], curent[1]))
                curent = [None, None]
        if curent[0] is not None and curent[1] - curent[0] + 1 >= min_scena:
            moarte.append((curent[0], curent[1]))
        if not moarte:
            noi.append((start, dur))
            continue
        segmente, cursor = [], 0
        for a, b in moarte:
            if a < 10:            # pastram intrarea scenei
                continue
            segmente.append((cursor, a))
            cursor = b + 1
        segmente.append((cursor, int(dur)))
        pierdere = int(dur) - sum(b - a for a, b in segmente)
        if pierdere > 0.35 * dur:
            noi.append((start, dur))      # scena ramane INTREAGA (nu o saram — bug prins de test)
            continue
        for a, b in segmente:
            if b - a >= 6:
                noi.append((start + a, b - a))
        taiate_total += pierdere
    return noi, taiate_total


def profil_retentie(sm, scene, durata):
    """Protejeaza copiii de zonele MOARTE. Mapeaza energia live-ului pe timeline-ul
    episodului; cauta finalul mort (energie sub baza ≥12s continuu pana la capat).
    intoarce (dead_pct, longest_dead, cut_ep) — cut_ep = unde se taie elastic (None=nu e nevoie)."""
    n = len(sm)
    if not n:
        return 0.0, 0, None
    baza = sorted(sm)[n // 2]
    ep = []                     # energia episodului, secunda cu secunda
    for start, dur in scene:
        for t in range(int(dur)):
            idx = int(start) + t
            ep.append(sm[idx] if 0 <= idx < n else baza)
    if not ep:
        return 0.0, 0, None
    moarte = [v < baza + 2 for v in ep]
    dead_pct = 100.0 * sum(moarte) / len(moarte)
    longest = curent = 0
    for m in moarte:
        curent = curent + 1 if m else 0
        longest = max(longest, curent)
    cut_ep = None
    if moarte:
        i = len(moarte) - 1
        while i >= 0 and moarte[i]:
            i -= 1
        coada_morta = len(moarte) - 1 - i
        if coada_morta >= 12:
            cut_ep = len(moarte) - coada_morta + 8      # lasam 8s de racire dupa moment
    return dead_pct, longest, cut_ep


def citeste_cheie_gemini(baza):
    """Cheia AI din autoeditor/.env (GEMINI_API_KEY=...) sau din mediu. None = fara AI."""
    k = os.environ.get("GEMINI_API_KEY")
    if k:
        return k
    p = os.path.join(baza, ".env")
    if os.path.exists(p):
        for lin in open(p, encoding="utf-8"):
            if lin.strip().startswith("GEMINI_API_KEY="):
                return lin.strip().split("=", 1)[1].strip()
    return None


def ia_frames_ai(ff, video, centru):
    """6 cadre în jurul momentului (-10..+15s) -> AI-ul vede ACTIUNEA in joc, nu o poza."""
    cadre = []
    for k, dt in enumerate([-10, -5, 0, 5, 10, 15]):
        cale = os.path.join("/tmp", f"ai_cadru_{int(centru)}_{k}.jpg")
        subprocess.run([ff, "-y", "-ss", str(max(0, centru + dt)), "-i", video,
                        "-frames:v", "1", "-vf", "scale=512:-2", "-q:v", "5", cale],
                       capture_output=True)
        if os.path.exists(cale):
            cadre.append(base64.b64encode(open(cale, "rb").read()).decode())
    return cadre


def ia_gemini(cheie, model, prompt, cadre_b64):
    """Apel REST Gemini (format din docs oficiale ai.google.dev, verificat 09.2026):
    POST /v1beta/models/{model}:generateContent, header x-goog-api-key."""
    parts = [{"inline_data": {"mime_type": "image/jpeg", "data": d}} for d in (cadre_b64 or [])]
    parts.append({"text": prompt})
    body = json.dumps({"contents": [{"parts": parts}],
                       "generationConfig": {"responseMimeType": "application/json",
                                            "temperature": 0.3}}).encode()
    data = None
    last_error = None
    for current_model in dict.fromkeys(m.strip() for m in model.split(",") if m.strip()):
        for attempt in range(3):
            req = urllib.request.Request(
                f"https://generativelanguage.googleapis.com/v1beta/models/{current_model}:generateContent",
                data=body, method="POST",
                headers={"Content-Type": "application/json", "x-goog-api-key": cheie})
            try:
                with urllib.request.urlopen(req, timeout=90) as r:
                    data = json.load(r)
                break
            except urllib.error.HTTPError as ex:
                last_error = ex
                if ex.code in (429, 500, 503):
                    time.sleep(2 * (attempt + 1))
                    continue
                if ex.code == 404:
                    break
                raise
        if data is not None:
            break
    if data is None:
        raise RuntimeError("Niciun model configurat nu a raspuns") from last_error
    d = data
    txt = d["candidates"][0]["content"]["parts"][0]["text"].strip()
    if txt.startswith("```"):                      # uneori vine cu garduri markdown
        txt = txt.strip("`")
        if txt.startswith("json"):
            txt = txt[4:]
    return json.loads(txt)


def evalueaza_cu_ai(ff, cheie, model, episoade, video, transcript, baza):
    """Creierul: pentru fiecare candidat, AI-ul vede 2 cadre + ce s-a vorbit si
    da scor (0-10) + titlu personalizat. Fara AI bun in zona = candidatul cade."""
    ramase = []
    for e in episoade:
        varf = e["varf"]
        txt = " ".join(t for a, b, t in transcript if varf - 25 <= a <= varf + 15)[:400] if transcript else "(fara transcript)"
        # CREIERUL: contextul complet al canalului + titluri vechi (evita repetitiile)
        creier = ""
        p_creier = os.path.join(baza, "cunoastere", "canal.md")
        if os.path.exists(p_creier):
            creier = open(p_creier, encoding="utf-8").read()[:3000] + "\n\n"
        p_reguli = os.path.join(baza, "cunoastere", "reguli.md")
        if os.path.exists(p_reguli):
            creier += "REGULI INVATATE RECENT DE LA CREATOR (respecta-le cu prioritate):\n" + \
                      open(p_reguli, encoding="utf-8").read()[:1500] + "\n\n"
        p_adn = os.path.join(baza, "cunoastere", "adn_canale.md")
        if os.path.exists(p_adn):
            creier += "ADN CANALE CARE MERG (formule + ritualuri verificate — aplica-le la titluri si la ce momente ridici):\n" + \
                      open(p_adn, encoding="utf-8").read()[:2500] + "\n\n"
        p_trend = os.path.join(baza, "cunoastere", "trending_ro.md")
        if os.path.exists(p_trend):
            creier += "TRENDING RO CITIT ACUM (ce publicau concurenta zilele astea — aliniaza titlurile la ce merge ACUM):\n" + \
                      open(p_trend, encoding="utf-8").read()[:2500] + "\n\n"
        p_ctx = "context_sursa.txt"
        ctx_txt = ""
        if os.path.exists(p_ctx):
            ctx_txt = "CONTEXTUL SURSEI (live-ul original, ca sa stii despre ce e vorba):\n" + \
                      open(p_ctx, encoding="utf-8").read()[:400] + "\n\n"
        p_titluri = os.path.join(baza, "cunoastere", "titluri_folosite.txt")
        vechi_t = ""
        if os.path.exists(p_titluri):
            randuri = [r.strip() for r in open(p_titluri, encoding="utf-8") if r.strip()]
            vechi_t = "TITLURI DEJA FOLOSITE (nu le repeta, gaseste unghiuri noi): " + " | ".join(randuri[-25:]) + "\n\n"
        # CONTEXTUL LIVE-ULUI (de la creator la publicarea release-ului: link + notiza)
        p_ctx = os.environ.get("AE_CONTEXT", "")
        if p_ctx and os.path.exists(p_ctx):
            creier += ("CONTEXTUL ACESTUI LIVE (de la creator — prioritate MAXIMA, "
                       "foloseste-l pentru titlu, in_joc si scor):\n" +
                       open(p_ctx, encoding="utf-8").read()[:1200] + "\n\n")
        prompt = (
            ctx_txt + creier + vechi_t +
            'Esti editor AI pentru canalul "PokeCity" (Minecraft + Pokemon, COPII 8-15 ani (public general), Romania). '
            'Judeci un moment dintr-un live. Ce s-a vorbit in jur: "' + txt + '". '
             'Vezi 6 cadre din joc (Minecraft/Pixelmon pe serverul PokeCity). Analizeaza CE SE INTAMPLA '
            'IN JOC: ce face jucatorul (lupta, prinde pokemon, construieste, exploreaza, moare, raid, '
            'gasesc ceva rar), cu ce pokemon, ce eveniment de joc s-a petrecut. Raspunzi DOAR cu JSON '
            'si un camp nou "in_joc": descriere concreta a evenimentului din joc (1-2 propozitii). ' 
            '{"scor": 0-10 pt copii mari (8-15) care TREBUIE sa ramana pe video: PRIORITATE MAXIMA = AMUZAMENT (rasa copilul: trei, glume, troleli, reactii comice, personajele amuzante) + EVENIMENTE DIN JOC vizibile (prindere rar/legendar, raid, loot, moarte comica); episoadele trebuie sa fie amuzante din ale lor, nu doar din ale noastre; rasete/trolluri doar daca legate de joc; MENIU/SETARI/inventar/pauza/harti-vazute-pe-ecran (ex: ecran de Shader Packs, optiuni, pause) = scor 1 — NU e faza din joc; vorba de la soare la ploi sau grind fara eveniment in joc = scor 2-4; evenimente rare in joc, neprevazut; vorba goala sau grind fara nimic amuzant = scor 2-4; ', 
            '"de_ce": "o propozitie scurta", '
            '"titlu": "titlu YouTube max 60 caractere, stil MrBeast: PRIMELE 3 CUVINTE = soc/FOMO '
            '(AM GASIT, L-AM PRINS, NIMENI NU STIE, PRIMUL DIN...), apoi misterul; cuvintele-cheie in MAJUSCULE; romaneste. '
            "STILUL EXACT iSilent + JocuriHorror (top 2 RO, analizati pe 60 de titluri reale) — formulele lor de aur: "
            "«CE am gasit in X..» · «NU Cumpara din ACEST X..» / «NU sta in X..» (NU + verb + ACEST) · «CUM am FURAT cel mai RAR OU ?» "
            "(CUM + verb perfect + substantiv SUPERLATIV) · «L-am TROLLAT si a PLANS 😂» (actiune + CONSECINTA emotionala) · "
            "«ERA SA MOR...» / «NU m-am ENERVAT..» (reactie stoica, final misterios) · «CINE-I CRIMINALUL ?» / «CINE se ASCUNDE mai BINE pe X ?» "
            "(intrebare CINE) · «Sunt SKINWALKER ?» / «Te Ascunzi ?» (intrebare scurta 2-3 cuvinte) · «Te rog NU BEA asta.. 💀» · "
            "«Am gasit CAT in the HAT in Lumea MEA..» (RECURENT: acelasi personaj/joc in serii — pt noi: POKECITY in fiecare titlu de epilog) · "
            "«Am SCHIMBAT Nota La TEST din 3 in 10..» (transformare CU NUMERE). "
            "REGLE DE FORMAT obligatorii: max ~55 caractere · 0-1 emoji (😂/😭/💀/😱 doar daca se potriveste) · «..» la final = mister "
            "· substantivele-cheie in MAJUSCULE (POKECITY, LEGENDAR, RAR) · NICIODATA clickbait minciunos — titlul promite EXACT ce e in video · "
            "FARA «Ep. N»/«EP» in titlu — seria se leaga prin playlist in descriere, nu prin numar · "
            "varianta poate fi si intrebare. Scrie 3 variante: una CE am gasit, una intrebare scurta, una cu consecinta emotionala. "
            '"promite": ["ce promite titlul, max 3 lucruri"], '
            '"livrat": true/false — TRUE doar daca TOT ce promite titlul chiar se vede/se aude in moment}. '
            'Daca in moment se SCHIMBA jocul (Minecraft->Roblox sau invers), e faza regresie: ia DOAR segmentul intr-un singur joc. ''REGULA DE AUR: titlul descrie DOAR ce chiar se intampla in moment (vezi cadrele + ce s-a vorbit). '
            'Daca in moment nu se prinde niciun Pokemon, titlul nu are voie sa promita asta. Fara clickbait fals. '
            'Scor mic daca: plictisitor, doar zgomot fara eveniment, sau nu se intelege ce se intampla.')
        try:
            r = ia_gemini(cheie, model, prompt, ia_frames_ai(ff, video, varf - 10))
            if r.get("livrat") is False:      # titlul promitea ceva ce NU e in moment -> rescriere stricta
                r2 = ia_gemini(cheie, model,
                               prompt + ' TITLUL ANTERIOR ("' + str(r.get("titlu", "")) +
                               '") a promis lucruri care nu apar. Rescrie-l STRICT dupa ce se vede/auze.',
                               ia_frames_ai(ff, video, varf - 10))
                if r2.get("livrat", True):
                    r = r2
                print("   AI: titlu RECALIBRAT (promis != livrat)")
            e["ai_scor"] = float(r.get("scor", 0))
            e["ai_de_ce"] = str(r.get("de_ce", ""))[:120]
            e["ai_titlu"] = str(r.get("titlu", ""))[:70]
            e["ai_promite"] = "; ".join(str(x) for x in (r.get("promite") or [])[:3])
            e["ai_livrat"] = bool(r.get("livrat", True))
            e["ai_in_joc"] = str(r.get("in_joc", ""))[:220]
            print(f"   AI {varf//60}:{varf%60:02d} -> scor {e.get('ai_scor', '?')}/10 · {e['ai_de_ce'][:60]}")
            ramase.append(e)
        except Exception as ex:
            print(f"   ! AI a esuat la un moment ({str(ex)[:70]}) — il las sa treaca pe selectia pe energie")
            ramase.append(e)
        time.sleep(2)   # ritm blând pt nivelul gratuit
    buni = [e for e in ramase if e.get("ai_scor", 0) >= 6]
    return buni if buni else [max(ramase, key=lambda e: e.get("ai_scor", 0))]   # mereu pastram cel mai bun


def valid_transcript(value):
    if not isinstance(value, list):
        return False
    for row in value:
        if not isinstance(row, (list, tuple)) or len(row) != 3:
            return False
        a, b, text = row
        if (isinstance(a, bool) or isinstance(b, bool) or not isinstance(a, (int, float))
                or not isinstance(b, (int, float)) or not math.isfinite(a) or not math.isfinite(b)
                or not 0 <= a < b or not isinstance(text, str)):
            return False
    return True


def transcrie_live(video, model_nume=None, source_fingerprint=None):
    """Reuse the exact transcript when source bytes/model/decoding parameters match."""
    from importlib.metadata import version, PackageNotFoundError
    model_nume = model_nume or os.environ.get("WHISPER_MODEL", "small")
    try:
        package_version = version('faster-whisper')
    except PackageNotFoundError:
        package_version = 'unavailable'
    options = dict(language='ro', vad_filter=True, beam_size=5)
    identity = dict(source=source_fingerprint or file_digest(video), model=model_nume, engine=package_version,
                    compute='int8', device='cpu', options=options)

    def compute():
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            return None
        model = WhisperModel(model_nume, device='cpu', compute_type='int8',
                             cpu_threads=max(1, min(4, os.cpu_count() or 1)))
        segments, _ = model.transcribe(video, **options)
        return [(segment.start, segment.end, segment.text.strip())
                for segment in segments if segment.text.strip()]

    return cached_json('transcript-v1', identity, compute, valid_transcript)


def durata_sursa(ff, video):
    """Read duration from metadata; do not decode a multi-hour VOD just to count seconds."""
    result = subprocess.run([ff, '-i', video], capture_output=True, text=True, timeout=60)
    match = re.search(r'Duration: (\d+):(\d+):(\d+(?:\.\d+)?)', result.stderr or '')
    if not match:
        raise ValueError('Durata sursei nu poate fi citita')
    duration = int(match[1]) * 3600 + int(match[2]) * 60 + float(match[3])
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError('Durata sursei este invalida')
    return duration


def _fmt_srt(t):
    ms = int(round((t - int(t)) * 1000))
    h, rest = divmod(int(t), 3600)
    m, s = divmod(rest, 60)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def scrie_srt_episod(cale, transcript, poveste):
    """Remapeaza transcriptul live-ului pe timeline-ul EPISODULUI (scenele sar prin live!)."""
    linii, idx = [], 0
    offset = 0.0
    for start_live, dur in poveste["scene"]:
        for (a, b, txt) in transcript:
            sf = start_live + dur
            if b > start_live and a < sf:                    # se suprapune cu scena
                linii.append(f"{idx+1}")
                linii.append(f"{_fmt_srt(max(0, offset + a - start_live))} --> "
                             f"{_fmt_srt(max(0, offset + min(b, sf) - start_live))}")
                linii.append(txt)
                linii.append("")
                idx += 1
        offset += dur
    if idx:
        open(cale, "w", encoding="utf-8").write("\n".join(linii) + "\n")
    return idx


def grupeaza_cu_ai(cheie, model, episoade, transcript):
    """AI-ul vede TOATE momentele din live si le grupeaza pe TEMA/quest:
    ex 'cautam pasarea' -> toate momentele cu pasarea (de la inceput/mijloc/sfarsit)
    intr-un SINGUR episod, aranjat ca poveste. Fallback: nimic (raman ca inainte)."""
    if len(episoade) < 3:
        return None
    randuri = []
    for i, e in enumerate(episoade):
        ce = e.get("ai_in_joc") or e.get("ai_de_ce") or ""
        if not ce and transcript:
            try:
                bucati = [tx for a, b, tx in transcript
                          if a - 30 <= e["varf"] <= b + 30][:2]
                ce = " ".join(bucati)[:150]
            except Exception:
                ce = ""
        randuri.append(f"{i} | {_ts(e['varf'])} | scor {e['scor']} | {ce[:140]}")
    ctx = ""
    p_ctx = os.environ.get("AE_CONTEXT", "")
    if p_ctx and os.path.exists(p_ctx):
        ctx = ("\n\nCONTEXTUL LIVE-ULUI (de la creator — grupeaza pe temele lui): "
               + open(p_ctx, encoding="utf-8").read()[:800] + "\n")
    prompt = ('Esti editor AI pentru canalul PokeCity (Minecraft+Pokemon, copii 8-15, RO). '
              "Mai jos sunt TOATE momentele tari dintr-un LIVE (index | timp | scor | ce se intampla). "
              "Grupeaza momentele in EPISOADE pe ACEEASI tema/quest: daca in 3+ momente se urmareste "
              "acelasi lucru (ex: 'cautam un pokemon rar', 'construim baza', 'raid'), pune-le in ACELASI "
              "episod — de la inceput, mijloc si sfarsit al live-ului — ca sa formeze O POVESTE completa. "
              "Un moment apartine unui singur episod. Grup de MINIM 3 momente. "
              "Momentelor fara tema comuna NU le forta gruparea. "
              'Raspunzi DOAR cu JSON: {"grupuri": [{"tema": "numele quest-ului", "indici": [0,3,5]}]}\n'
              + ctx + "\n" + "\n".join(randuri))
    try:
        r = ia_gemini(cheie, model, prompt, None)
        grupuri = (r or {}).get("grupuri") or []
        if not grupuri:
            return None
    except Exception:
        return None
    folosite, rezultat = set(), []
    for g in grupuri:
        idxs = [i for i in g.get("indici", []) if isinstance(i, int) and 0 <= i < len(episoade)]
        if len(idxs) < 3:
            continue
        membri = sorted((episoade[i] for i in idxs), key=lambda e: e["varf"])
        maxim = max(membri, key=lambda e: e["scor"])
        scena = [(max(0, maxim["varf"] - 2), 8),
                 (max(0, membri[0]["varf"] - 15), 55),
                 (max(0, membri[1]["varf"] - 10), 55),
                 (max(0, maxim["varf"] - 15), 52)]
        rezultat.append({"tip": "poveste", "scor": round(sum(e["scor"] for e in membri) / len(membri), 1),
                         "scene": scena, "varf": maxim["varf"],
                         "folosite": sorted(set().union(*[set(e.get("folosite", [])) for e in membri])),
                         "tema": g.get("tema", "")})
        folosite.update(idxs)
    if not rezultat:
        return None
    restul = [e for i, e in enumerate(episoade) if i not in folosite]
    return sorted(rezultat + restul, key=lambda e: -e["scor"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--durata", type=int, default=DURATA)
    ap.add_argument("--max", type=int, default=MAX_EPISOADE)
    ap.add_argument("--clasic", action="store_true", help="mod v1: o scena pe episod")
    ap.add_argument("--momente", metavar="FISIER", help="tu zici momentele exacte (unul pe linie: m:ss sau h:mm:ss)")
    ap.add_argument("--calitate", default="1080p", choices=["1080p", "2k"],
                    help="2k = export 1440p cu lanczos+sharpen (recomandat daca live-ul e 1080p+)")
    ap.add_argument("--pachet", metavar="NUME", help="pachet de assets alternativ: assets_NUME/ (ex: halloween)")
    ap.add_argument("--subtitrari", action="store_true", help="genereaza .srt per episod (AI local, optiunal)")
    ap.add_argument("--ai", action="store_true", help="AI-minte (Gemini): intelege momentele semantic + titluri personalizate (cheie gratuita in autoeditor/.env)")
    ap.add_argument("--doar-analiza", action="store_true")
    opt = ap.parse_args()
    if opt.max < 1:
        ap.error("--max trebuie sa fie cel putin 1")
    if opt.ai:
        opt.clasic = True  # Strict AI mode always reviews a single continuous story.

    ff = gaseste_ffmpeg()
    baza = os.path.dirname(os.path.abspath(__file__))
    folder = os.path.join(baza, "episodes")
    os.makedirs(folder, exist_ok=True)
    assets_dir = os.path.join(baza, f"assets_{opt.pachet}") if opt.pachet else os.path.join(baza, "assets")
    if opt.pachet and not os.path.isdir(assets_dir):
        print(f"   ! pachetul assets_{opt.pachet}/ nu exista -> folosesc assets/ normal")
        assets_dir = os.path.join(baza, "assets")
    muzica = os.path.join(assets_dir, "muzica.mp3")
    muzica = muzica if os.path.exists(muzica) else None
    logo = os.path.join(assets_dir, "logo.png")
    logo = logo if (os.path.exists(logo) and os.environ.get("AE_LOGO", "0") == "1") else None   # watermark pe video OFF (user: "ai scris pe ecran iZentric"); miniaturile il pastreaza
    efecte = gaseste_efecte(assets_dir)
    confeti_p = os.path.join(assets_dir, "efecte", "confeti.webm")
    confeti_p = confeti_p if (os.path.exists(confeti_p) and os.environ.get("AE_CONFETI", "0") == "1") else None   # confetti OFF (user: "partile colorate pe ecran")
    pool_rand = gaseste_sfx_random(assets_dir)
    meme = gaseste_meme(assets_dir)
    catalogue = sound_catalogue(
        [os.path.join(baza, "sunete_mele"), os.path.join(assets_dir, "efecte")],
        lambda path: FOLDERE_MELE.get(os.path.basename(os.path.dirname(path)).upper())
        or clasifica_sunet(path))
    if opt.ai:
        # Fixed slots and random meme inserts cannot explain an event-specific choice.
        efecte, meme = {}, []
        if not citeste_cheie_gemini(baza):
            sys.exit("Calitate AI: cheia lipseste; nu randez clipuri neverificate.")
    print(f"assets: muzica={'DA' if muzica else 'NU'} · logo={'DA' if logo else 'NU'} · "
          f"efecte={','.join(efecte) if efecte else 'niciunul'} · "
          f"confeti={'DA' if confeti_p else 'nu'} · sunete-random={len(pool_rand)} · sunete-mele={sum(len(v) for v in sunete_mele_pool().values())} · meme-greenscreen={len(meme)}")

    w_src, h_src = rezolutie_sursa(ff, os.path.abspath(opt.video))
    fps_live = fps_sursa(ff, os.path.abspath(opt.video))
    tinta_h = 1440 if (opt.calitate == "2k" and h_src < 1440) else 0
    print(f"sursa: {w_src}x{h_src} -> export {'1440p (2K, lanczos+sharpen)' if tinta_h else 'rezolutie sursa'}")
    if opt.calitate == "2k" and h_src >= 1440:
        print("   live-ul TAIE deja in 2K+ -> pastram nativ, nimic de upscalat (cel mai bine)")
    if opt.ai:
        seria = []
        live_len = durata_sursa(ff, opt.video)
        source_sha = file_digest(opt.video)
        print(f"1/4 Sursa: {live_len/60:.1f} min; selectia AI nu necesita analiza RMS separata.")
        varfuri, scor = [], []
    else:
        print("1/4 Ascult live-ul (volum pe fiecare secunda)...")
        seria = analiza_audio(ff, opt.video)
        live_len = seria[-1][0]
        varfuri, scor = detecteaza_explozii(seria)

    print("2/4 Caut momentele si construiesc POVESTILE...")
    if opt.ai:
        episoade, p3 = [], opt.durata
        momente = citeste_momente(opt.momente) if opt.momente else []
        if opt.momente and not momente:
            sys.exit("Fisierul de momente este gol sau invalid.")
    elif opt.momente:
        momente = citeste_momente(opt.momente)
        if not momente:
            sys.exit(f"Nu am putut citi momente din {opt.momente} (format: m:ss sau h:mm:ss, unul pe linie)")
        print(f"   MOD MANUAL: {len(momente)} momente date de tine -> construiesc episoadele pe ele")
        episoade, p3 = alege_din_momente(momente, varfuri, scor, live_len, opt.durata, opt.max)
    else:
        if varfuri:
            # POARTA DE ELITA: intra doar momentele din clasa de varf a live-ului.
            # Daca live-ul are un singur moment tare, raman UNUL — umplutura NU se face.
            scor_max = max(s for _, s in varfuri)
            poarta = max(7.0, float(os.environ.get("AE_POARTA", "0.6")) * scor_max)  # 0.6 = doar ce CHIAR merita
            varfuri_elita = [v for v in varfuri if v[1] >= poarta]
            print(f"   poarta de elita: scor >= {poarta:.1f} -> {len(varfuri_elita)} momente merita episod")
        else:
            varfuri_elita = []
        if opt.clasic:
            episoade = alege_clasic(varfuri_elita, scor, live_len, opt.durata, opt.max, [])
            p3 = opt.durata
        else:
            episoade, p3 = alege_povesti(varfuri_elita, scor, live_len, opt.durata, opt.max)
            for e in episoade:                      # POVESTE = UN SINGUR JOC: setup+dezfasurare mutate langa varf
                sc = e["scene"]
                C = e["varf"]
                inapoi_set = min(450, max(60, C - 5))    # setup: ~7.5 min inainte de explozie
                inapoi_dez = min(240, max(30, C - 5))    # dezfasurare: ~4 min inainte (actiunea creste spre varf)
                e["scene"] = [sc[0], (max(1, C - inapoi_set), sc[1][1]),
                              (max(1, C - inapoi_dez), sc[2][1]), sc[3]]
            episoade += alege_clasic(varfuri_elita, scor, live_len, opt.durata, opt.max, episoade)
    if not episoade and not opt.ai:
        sys.exit("Niciun moment nu a trecut poarta de calitate. NU fac episoade slabe — regula ta: doar cel mai bun.")

    # transcript (daca e cerut de subtitrari SAU de AI) — o singura data, refolosit
    transcript = None
    if opt.subtitrari or opt.ai or pool_rand:
        tr = transcrie_live(os.path.abspath(opt.video),
                            source_fingerprint=source_sha if opt.ai else None)
        if tr is None:
            print("   (faster-whisper nu e instalat — subtitrari + sunete-semantice inactive: pip install faster-whisper)")
        else:
            transcript = tr
            print(f"   transcript AI: {len(tr)} replici")
            # MEMORIA: transcriptul fiecarui live intra in cunoastere/ (si in repo)
            cu_dir = os.path.join(baza, "cunoastere", "transcripte")
            os.makedirs(cu_dir, exist_ok=True)
            nume = datetime.now().strftime("LIVE_%Y-%m-%d_%H%M") + ".json"
            with open(os.path.join(cu_dir, nume), "w", encoding="utf-8") as f:
                json.dump({"data": datetime.now().isoformat(), "sursa": os.path.basename(opt.video),
                           "replici": tr}, f, ensure_ascii=False)
            print(f"   memorie: {nume} salvat in cunoastere/transcripte/")

    if opt.ai:
        cheie = citeste_cheie_gemini(baza)
        model = os.environ.get("GEMINI_MODEL", "gemini-3.6-flash")
        try:
            if opt.momente:
                idei = [{"inceput": max(0, t - 55), "sfarsit": min(live_len, max(0, t - 55) + 170),
                         "titlu": "Moment indicat de creator", "de_ce": "Selectie manuala"}
                        for t in momente]
            else:
                if not transcript:
                    raise ValueError("Transcript indisponibil")
                idei = idei_cu_ai(ia_gemini, cheie, model, transcript, live_len, baza)
            episoade, audit = approved_episodes(
                idei,
                lambda idea: verifica_idee_cu_video(
                    ff, cheie, model, os.path.abspath(opt.video), idea, catalogue=catalogue, transcript=transcript,
                    source_fingerprint=source_sha),
                catalogue, live_len, opt.max, transcript=transcript)
        except Exception as ex:
            episoade = []
            audit = [{"status": "neverificat", "motiv": f"Selectie indisponibila: {type(ex).__name__}"}]
        with open(os.path.join(folder, "DECIZII_AI.json"), "w", encoding="utf-8") as f:
            json.dump(audit, f, ensure_ascii=False, indent=2)
        if not episoade:
            with open(os.path.join(folder, "plan.json"), "w", encoding="utf-8") as f:
                json.dump([], f)
            with open(os.path.join(folder, "RAPORT.md"), "w", encoding="utf-8") as f:
                f.write("# Oprit: niciun episod verificat\nVezi DECIZII_AI.json. "
                        "Nu se livreaza selectie dupa zgomot sau idei neconfirmate.\n")
            sys.exit("Calitate AI: niciun episod aprobat. Vezi episodes/DECIZII_AI.json.")
        print(f"   AI: {len(episoade)} povesti verificate; fara efecte aleatorii")
    print(f"   plan: {len(episoade)} episoade ({sum(1 for e in episoade if e['tip']=='poveste')} in modul poveste)")

    rap = ["# RAPORT AUTOEDITOR (POVESTEA) — " + datetime.now().strftime("%d.%m.%Y %H:%M"),
           f"Sursa: {opt.video} ({live_len//60} min) · episod: {opt.durata}s",
           f"**DECIZIE AI: {len(episoade)} episoade** — doar momentele care au trecut poarta de calitate; restul ar fi umplutura.", ""]
    for k, e in enumerate(episoade, 1):
        if e.get("manual"):
            rap.append(f"- MOMENT EXACT ales de tine: {_ts(e['varf'])}")
        if e["tip"] == "poveste":
            sc = e["scene"]
            rap.append(f"## EP{k:02d} — POVESTEA (scor {e['scor']})")
            rap.append(f"- INTRO-REACTIE din {_ts(sc[0][0])} (teaserul momentului maxim)")
            rap.append(f"- SETUP din {_ts(sc[1][0])} (acelasi joc, cu cateva minute inainte de explozie)")
            rap.append(f"- DESFASURARE din {_ts(sc[2][0])} (actiunea creste — mijlocul)")
            rap.append(f"- MOMENTUL MAXIM din {_ts(sc[3][0])} (explozia completa)")
            rap.append(f"- Pe ecran: intrebare la 0:12 · hype la {_ts(START_P3-10)} · LIKE+comentariu la final (comentariile DESCHISE, public 9-15)")
        else:
            rap.append(f"## EP{k:02d} — CLASIC (scor {e['scor']})")
            rap.append(f"- Incepe la {_ts(e['scene'][0][0])} · explozie la {_ts(e['varf'])}")
        rap.append("")
    titluri = []
    for k, e in enumerate(episoade, 1):
        if e.get("ai_titlu"):
            rap.append(f"- TITLU AI (scor {e.get('ai_scor', '?')}/10): {e['ai_titlu']}")
            if e.get("ai_in_joc"):
                rap.append(f"- IN JOC: {e['ai_in_joc']}")
            if e.get("ai_promite"):
                rap.append(f"- PROMIS=LIVRAT {'OK ✓' if e.get('ai_livrat', True) else 'RECALIBRAT ✓'} (promite: {e['ai_promite']})")
            titluri.append(f"EP{k:02d}: {e['ai_titlu']}")

    if not titluri:
        rap.append("Titlurile sunt SABLON — le personalizezi dupa ce vizionezi.")
    if titluri:
        with open(os.path.join(folder, "titluri.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(titluri) + "\n")
    with open(os.path.join(folder, "RAPORT.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(rap))
    # Only verified source-relative peaks can seed the separate shorts review.
    with open(os.path.join(folder, "plan.json"), "w", encoding="utf-8") as f:
        json.dump([{"nr": k, "varf": e.get("varf"), "scor": e.get("scor"), "tip": e.get("tip"),
                    "scene": e.get("scene"), "ai_verified": e.get("ai_verified", False),
                    "titlu": e.get("ai_titlu")} for k, e in enumerate(episoade, 1)],
                  f, ensure_ascii=False)
    print("   raport: episodes/RAPORT.md")

    if opt.doar_analiza:
        print("GATA (doar analiza). Scoate --doar-analiza ca sa randeze.")
        return

    if not opt.ai:
        episoade = motiv_de_exista(episoade)
    print("3/4 Randez episoadele (cea mai lunga parte)...")
    h_out = tinta_h if tinta_h else (rezolutie_sursa(ff, os.path.abspath(opt.video))[1])
    sm_full = [v for _, v in seria]
    facute = []
    for k, e in enumerate(episoade, 1):
        eticheta = "POVESTEA" if e["tip"] == "poveste" else "clasic"
        # PROTECTIA RETENTIEI: daca finalul episodului e mort, il tai elastic (MrBeast:
        # tai cand s-a terminat povestea, nu cronometrul). Minim 90s.
        if sm_full and not e.get("ai_verified"):
            e["scene"], gol_taiat = comprima_zone_moarte(sm_full, e["scene"], opt.durata)
            if gol_taiat:
                print(f"   EP{k:02d}: COMPRIMARE stil-JOH: {int(gol_taiat)}s de gol scoase din mijloc")
        dead_pct, longest, cut_ep = ((0, 0, None) if e.get("ai_verified") else
                                      profil_retentie(sm_full, e["scene"], opt.durata))
        durata_ep = sum(d for _, d in e["scene"])
        if not e.get("ai_verified") and cut_ep and cut_ep < opt.durata - 20:
            durata_ep = max(90, cut_ep)
            ramas = durata_ep - sum(d for _, d in e["scene"][:-1])
            e["scene"][-1] = (e["scene"][-1][0], max(20, int(ramas)))
            print(f"   EP{k:02d}: FINAL ELASTIC {opt.durata}->{durata_ep}s (zona moarta de {int(dead_pct)}% taiata)")
        if transcript and not e.get("ai_verified") and os.environ.get("AE_POPS", "1") != "0":
            e["_pops"] = pops_subtitrari(transcript, e["scene"], durata_ep)
            if e["_pops"]:
                print(f"   EP{k:02d}: subtitrari-POP (mari, galbene) la {len(e['_pops'])} momente-cheie")
        if e.get("ai_verified"):
            # Keep the reviewed timeline intact: no energy-based cuts after approval.
            sfx_rand = [(s["sec"], s["path"], 1.0) for s in e["_sound_plan"]]
        else:
            sfx_rand = (alege_sfx_inteligent(pool_rand, durata_ep, transcript, e["scene"])
                        if pool_rand or catalogue else None)
        e["_sfx"] = sfx_rand or []
        if sfx_rand:
            detalii = ", ".join(f"{int(t)//60}:{int(t)%60:02d} {os.path.basename(c)}" for t, c, _ in sfx_rand)
            print(f"   EP{k:02d} ({eticheta}) · sunete: {detalii}{' + confeti' if confeti_p else ''}")
        else:
            print(f"   EP{k:02d} ({eticheta})...")
        out = comanda_randare(ff, os.path.abspath(opt.video), e, durata_ep, folder, muzica, logo, k,
                              efecte, tinta_h, sfx_rand, confeti_p, h_out,
                              dim=(w_src, h_src, fps_live), seria=seria, meme=meme)
        if opt.ai and not out:
            sys.exit(f"EP{k:02d}: randare esuata; livrarea este oprita.")
        if out:
            lu = calibreaza_lufs(ff, os.path.join(folder, out))
            if opt.ai and not lu:
                sys.exit(f"EP{k:02d}: master audio neverificat; livrarea este oprita.")
            if lu:
                e["_lufs"] = lu
            facute.append((k, e, out))
            print(f"   OK -> episodes/{out}")
            try:                      # LIVRARE PE RAND: episodul merge pe release imediat
                from upload_release import incarca_pe_release, slug_nume
                incarca_pe_release(os.path.join(folder, out),
                                   nume=slug_nume(e.get("ai_titlu") or "EPISOD", nr=k))
            except Exception:
                pass

    print("4/4 Cadre pt miniaturi (reale, din clip)...")
    for k, e, out in facute:
        if e["tip"] == "poveste":
            moment = START_P3 + HOOK_INAINTE   # explozia cade fix dupa inceputul scenei 3
        else:
            moment = e["varf"] - e["scene"][0][0]
        for c in cadre_miniatura(ff, out, moment, k, folder):
            print("   " + c)

    if facute:
        try:
            os.makedirs(os.path.join(baza, "cunoastere", "rapoarte"), exist_ok=True)
            rap_complet = open(os.path.join(folder, "RAPORT.md"), encoding="utf-8").read()
            open(os.path.join(baza, "cunoastere", "rapoarte",
                 "RAPORT_" + datetime.now().strftime("%Y-%m-%d_%H%M") + ".md"), "w",
                encoding="utf-8").write(rap_complet)
        except Exception:
            pass
        chk = ["", "## CHECKLIST (tot ce trebuie sa aiba un episod bun)"]
        for k, e, out in facute:
            chk.append(
                f"- EP{k:02d}: titlu {'AI: „' + e['ai_titlu'] + '”' if e.get('ai_titlu') else 'sablon (il personalizezi tu)'} · "
                f"moment {'scor AI ' + str(e.get('ai_scor', '?')) + '/10' if e.get('ai_scor') else 'scor energie ' + str(e['scor'])} · "
                f"sunete potrivite contextului: {len(e.get('_sfx', []))} · confeti: {'DA' if confeti_p else 'nu'} · "
                f"durata planificata: {sum(d for _, d in e['scene'])}s")
            for sound in e.get("_sound_plan", []):
                chk.append(f"  - {sound['sec']:.1f}s · {os.path.basename(sound['path'])}: {sound['motiv']}")
        for k, e, out in facute:
            if e.get("_lufs"):
                chk.append(f"- {out}: AUDIO CALIBRAT YOUTUBE {e['_lufs'][0]:.1f} -> {e['_lufs'][1]:.1f} LUFS (tinta -14, varfuri <= -1.5 dBTP)")
            chk.append(f"- {out}: zoom activ: {os.environ.get('AE_ZOOM', '0') == '1'}")
            if e.get("_meme_n"):
                chk.append(f"- {out}: {e['_meme_n']} meme-uri greenscreen pe momentele comice")
            chk.append(f"- {out}: GRADE culoare (saturatie 1.18, contrast 1.06 — pica in feed)")
        open(os.path.join(folder, "RAPORT.md"), "a", encoding="utf-8").write("\n".join(chk) + "\n")

    if opt.subtitrari and transcript:
        print("Scriu subtitrarile .srt (remapate pe scenele fiecarui episod)...")
        for k, e, out in facute:
            n = scrie_srt_episod(os.path.join(folder, out.replace(".mp4", ".srt")), transcript, e)
            print(f"   {out.replace('.mp4','.srt')}: {n} replici")
    elif opt.subtitrari:
        print("Subtitrari: transcriptul nu e disponibil (instalezi faster-whisper si rerulezi)")

    # ═══ KIT DE UPLOAD: tot ce lipuiesti in Studio, gata per episod ═══
    # MEMORIA: titluri in istoric + raport in cunoastere/
    titluri_noi = [e.get("ai_titlu") for e in episoade if e.get("ai_titlu")]
    if titluri_noi:
        with open(os.path.join(baza, "cunoastere", "titluri_folosite.txt"), "a", encoding="utf-8") as f:
            for t in titluri_noi:
                f.write(t + "\n")
    print("KIT de upload: miniaturi editate (din cadre REALE) + titlu/descriere/tag-uri...")
    TAGURI = ("nocivanu, nocivanu pokecity, nocivanu pokemon, pokecity, nocivanu minecraft, nociv, "
              "pokecity seria, minecraft cu pokemoni, pixelmon, minecraft pokemon mod, nocivanu extra, "
              "pixelmon server, nocivanu horror, pixelmon romania, isentric, izentric, minecraft romania, "
              "gaming romania, supercity, nocivanu supercity, minecarft")
    for k, e, out in facute:
        titlu_full = e.get("ai_titlu") or "Moment din live — de verificat"
        cadru = os.path.join(folder, f"EP{k:02d}_cadru2.jpg")
        try:
            if os.path.exists(cadru):
                p = fa_miniatura(cadru, os.path.join(folder, f"EP{k:02d}_miniatura.jpg"), titlu_full, logo, sageata=(820, 240))
                print(f"   miniatura A: {os.path.basename(p)}")
                for suf, sageata2 in (("B", (400, 600)), ("C", (640, 140))):
                    try:
                        p2 = fa_miniatura(cadru, os.path.join(folder, f"EP{k:02d}_miniatura_{suf}.jpg"),
                                          titlu_full, logo, sageata=sageata2)
                        print(f"   miniatura {suf}: {os.path.basename(p2)}")
                    except Exception:
                        pass
        except ImportError:
            print("   ! pt miniaturi instalezi: pip install pillow")
        desc = titlu_full + "\n\n"
        if e.get("ai_in_joc"):
            desc += e["ai_in_joc"] + "\n\n"
        elif e.get("ai_de_ce"):
            desc += e["ai_de_ce"] + "\n\n"
        desc += ("▶ SERIA COMPLETĂ: https://www.youtube.com/playlist?list=PLI1rZHL507Wk\n"
                 "👍 LIKE + scrie în comentarii ce prindem în episodul următor!\n"
                 "👉 ABONEAZĂ-TE: https://www.youtube.com/@izentric1?sub_confirmation=1\n\n"
                 "💬 Discord: https://discord.com/invite/qzBUttGxHZ\n"
                 "📩 Business: game.nation.izentric@gmail.com\n\n"
                 "#minecraft #pokemon #pokecity\n")
        open(os.path.join(folder, f"EP{k:02d}_upload.txt"), "w", encoding="utf-8").write(
            f"TITLU:\n{titlu_full}\n\nDESCRIERE:\n{desc}\nTAG-URI (lipești în câmpul Tag-uri):\n{TAGURI}\n"
               "PUBLIC: copii MAI MARI (9-15), stil trending RO gaming (JocuriHorror/Klorna/Silver).\n"
               "La upload lasa «NU e facut pentru copii» (implicit) = comentariile raman DESCHISE.\n"
               "NU cere niciodata date personale de la privitori minori (nume, adrese, conturi).\n")

    print(f"\nGATA: {len(facute)} episoade in autoeditor/episodes/")
    print("URMATOR PAS: vizioneaza-le pe TOATE inainte de upload. Tu esti filtrul de calitate.")


if __name__ == "__main__":
    main()
