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
import os
import random
import time
import urllib.request
import re
import shutil
import subprocess
import sys
from datetime import datetime

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
CTA_TEXT = "LIKE + scrie în comentarii ce prindem în episodul următor!"
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


def gaseste_efecte(folder_assets):
    """Cauta efectele in assets/efecte/ dupa numele sloturilor (orice format audio).
    lipsa = slotul se sari; prezenta = se aplica automat peste tot."""
    d = os.path.join(folder_assets, "efecte")
    gasite = {}
    if os.path.isdir(d):
        for nume in EFECTE_SLOTS:
            for f in os.listdir(d):
                if os.path.splitext(f)[0].lower() == nume and not f.startswith("."):
                    gasite[nume] = os.path.join(d, f)
                    break
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
    h, rest = divmod(int(sec), 3600)
    m, s = divmod(rest, 60)
    return f"{h}:{m:02d}:{s:02d}.00"


def scrie_ass(nume, durata, poveste):
    """Textele pe ecran: semnatura colt + intrebare (0:12) + hype (inainte de maxim) + CTA final."""
    linii = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1920", "PlayResY: 1080", "",
             "[V4+ Styles]",
             "Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, BorderStyle",
             "Style: CTA,Arial,84,&H00FFFFFF,&H00000000,&H80000000,1,4,0,2,60,60,90,1",
             "Style: WM,Arial,44,&H00FFFFFF,&H00000000,&H80000000,1,3,0,7,40,40,30,1",
             "Style: HYPE,Arial,96,&H0000E5FF,&H00000000,&H80000000,1,5,0,2,60,60,90,1",
             "", "[Events]",
             "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    if NUME_CANAL:
        linii.append(f"Dialogue: 0,0:00:00.00,{_ts(durata)},WM,,0,0,0,,{NUME_CANAL}")
    if poveste and poveste.get("tip") == "poveste":
        linii.append(f"Dialogue: 0,{_ts(12)},{_ts(21)},CTA,,0,0,0,,{INTREBARE_TEXT}")
        linii.append(f"Dialogue: 0,{_ts(START_P3 - 10)},{_ts(START_P3 - 2)},HYPE,,0,0,0,,{HYPE_TEXT}")
    linii.append(f"Dialogue: 0,{_ts(max(0, durata-5))},{_ts(durata)},CTA,,0,0,0,,{CTA_TEXT}")
    open(nume, "w", encoding="utf-8").write("\n".join(linii) + "\n")
    return os.path.basename(nume)


def comanda_randare(ff, video, poveste, durata, folder, muzica, logo, nr, efecte=None, tinta_h=0, sfx_rand=None, confeti=None, h_out=1080):
    """O comanda ffmpeg: concateneaza scenele (+intro-reactia), pune logo, textele, muzica."""
    ass = scrie_ass(os.path.join(folder, f"EP{nr:02d}.ass"), durata, poveste)
    cmd = [ff, "-y"]
    for start, lung in poveste["scene"]:
        cmd += ["-ss", str(max(0, start)), "-t", str(lung), "-i", video]
    filtre, n = [], len(poveste["scene"])
    # concat vrea perechi INTERLEAVED per segment: [0:v][0:a][1:v][1:a]...
    concat_in = "".join(f"[{i}:v][{i}:a]" for i in range(n))
    filtre.append(f"{concat_in}concat=n={n}:v=1:a=1[vc][ac]")
    # calitate: daca cerem 2K si sursa e mai mica -> scalare LANCZOS + usor sharpen
    # (YouTube da bitrate mai mare la 1440p => imaginea supravietuieste mai bine re-encodarii lor)
    if tinta_h:
        filtre.append(f"[vc]scale=-2:{tinta_h}:flags=lanczos,unsharp=5:5:0.3:5:5:0.0[vc2]")
        src_vc = "[vc2]"
    else:
        src_vc = "[vc]"
    if logo:
        cmd += ["-i", logo]
        li = n
        filtre += [f"[{li}:v]scale=140:-1[lg]",
                   f"{src_vc}scale=trunc(iw/2)*2:trunc(ih/2)*2[b0]",
                   "[b0][lg]overlay=W-w-24:24[b1]",
                   f"[b1]subtitles={ass}[vout]"]
    else:
        filtre += [f"{src_vc}scale=trunc(iw/2)*2:trunc(ih/2)*2,subtitles={ass}[vout]"]
    vmap = "[vout]"
    if confeti:
        cmd += ["-i", confeti]
        ci = n + (1 if logo else 0)
        # confeti.webm = 2s cu fundal transparent; tpad=clone (transparent) pana la moment, apoi overlay
        intarziere = max(0, durata - 8)
        filtre.append(f"[{ci}:v]scale=-2:{h_out},tpad=start_duration={intarziere}:start_mode=clone[cf]")
        filtre.append(f"[vout][cf]overlay=0:0:eof_action=pass[vfin]")
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
            filtre.append(f"[{idx}:a]adelay={int(t*1000)}:all=1,volume={vol:.2f}[x{idx}]")
            intrari_rand.append(f"[x{idx}]")
    amix_in = "[ac]" + ("[bg]" if muzica else "") + "".join(intrari_sfx) + "".join(intrari_rand)
    filtre.append(f"{amix_in}amix=inputs={amix_in.count('[')}:duration=first:normalize=0[a0]")
    filtre.append(f"[a0]afade=t=out:st={max(0, durata-2)}:d=2[aout]")
    harta_a = "[aout]"
    out = f"EP{nr:02d}.mp4"
    crf = "20" if tinta_h else "23"
    preset = "medium" if tinta_h else "veryfast"
    cmd += ["-filter_complex", ";".join(filtre), "-map", vmap, "-map", harta_a,
            "-c:v", "libx264", "-preset", preset, "-crf", crf,
            "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out]
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=folder)
    if r.returncode != 0 or not os.path.exists(os.path.join(folder, out)):
        print(f"  ! EP{nr:02d}: ffmpeg a esuat: {(r.stderr or '')[-800:]}")
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


def fa_miniatura(cale_cadru, cale_out, titlu, logo=None):
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


def alege_sfx_inteligent(pool, durata, transcript, scene):
    """PRECIS, nu doar random: evenimentele REALE din vorbire primeste sunetul POTRIVIT
    (fericit_* la 'am prins!', cadere_* la 'a cazut!'). Daca evenimentele sunt rare,
    umple cu random in puncte sigure. -> [(t_episod, fisier, volum)]"""
    pe_cat = {"fericit": [], "cadere": [], "speriat": [], "generic": []}
    for cale in pool:
        nume = os.path.splitext(os.path.basename(cale))[0].lower()
        pus = False
        for tip in ("fericit", "cadere", "speriat"):
            if nume.startswith(tip + "_") or nume.startswith(tip + "-"):
                pe_cat[tip].append(cale)
                pus = True
                break
        if not pus:
            pe_cat["generic"].append(cale)

    alese = []
    for t_live, tip in detecteaza_evenimente(transcript):
        if len(alese) >= 4:
            break
        t_ep = live_to_episod(t_live, scene)
        if t_ep is None or not (8 <= t_ep <= durata - 8):
            continue
        if any(abs(t_ep - x) < 8 for x, _, _ in alese):
            continue
        candidati = pe_cat[tip] or pe_cat["generic"]
        if candidati:
            alese.append((t_ep, random.choice(candidati), random.uniform(0.7, 0.9)))
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


def profil_retentie(sm, scene, durata):
    """Protejeaza copiii de zonele MOARTE. Mapeaza energia live-ului pe timeline-ul
    episodului; cauta finalul mort (energie sub baza ≥12s continuu pana la capat).
    intoarce (dead_pct, longest_dead, cut_ep) — cut_ep = unde se taie elastic (None=nu e nevoie)."""
    n = len(sm)
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
    parts = [{"inline_data": {"mime_type": "image/jpeg", "data": d}} for d in cadre_b64]
    parts.append({"text": prompt})
    body = json.dumps({"contents": [{"parts": parts}],
                       "generationConfig": {"responseMimeType": "application/json",
                                            "temperature": 0.3}}).encode()
    req = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        data=body, method="POST",
        headers={"Content-Type": "application/json", "x-goog-api-key": cheie})
    with urllib.request.urlopen(req, timeout=90) as r:
        d = json.load(r)
    txt = d["candidates"][0]["content"]["parts"][0]["text"].strip()
    if txt.startswith("```"):                      # uneori vine cu garduri markdown
        txt = txt.strip("`")
        if txt.startswith("json"):
            txt = txt[4:]
    return json.loads(txt)


def evalueaza_cu_ai(ff, cheie, model, episoade, video, transcript):
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
        p_titluri = os.path.join(baza, "cunoastere", "titluri_folosite.txt")
        vechi_t = ""
        if os.path.exists(p_titluri):
            randuri = [r.strip() for r in open(p_titluri, encoding="utf-8") if r.strip()]
            vechi_t = "TITLURI DEJA FOLOSITE (nu le repeta, gaseste unghiuri noi): " + " | ".join(randuri[-25:]) + "\n\n"
        prompt = (
            creier + vechi_t +
            'Esti editor AI pentru canalul "PokeCity" (Minecraft + Pokemon, COPII 6-13 ani, Romania). '
            'Judeci un moment dintr-un live. Ce s-a vorbit in jur: "' + txt + '". '
             'Vezi 6 cadre din joc (Minecraft/Pixelmon pe serverul PokeCity). Analizeaza CE SE INTAMPLA '
            'IN JOC: ce face jucatorul (lupta, prinde pokemon, construieste, exploreaza, moare, raid, '
            'gasesc ceva rar), cu ce pokemon, ce eveniment de joc s-a petrecut. Raspunzi DOAR cu JSON '
            'si un camp nou "in_joc": descriere concreta a evenimentului din joc (1-2 propozitii). ' 
            '{"scor": 0-10 (cat de tare e momentul pentru copii), '
            '"de_ce": "o propozitie scurta", '
            '"titlu": "titlu YouTube max 60 caractere, cu mister, romaneste", '
            '"promite": ["ce promite titlul, max 3 lucruri"], '
            '"livrat": true/false — TRUE doar daca TOT ce promite titlul chiar se vede/se aude in moment}. '
            'REGULA DE AUR: titlul descrie DOAR ce chiar se intampla in moment (vezi cadrele + ce s-a vorbit). '
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
            print(f"   AI {varf//60}:{varf%60:02d} -> scor {e['ai_scor']}/10 · {e['ai_de_ce'][:60]}")
            ramase.append(e)
        except Exception as ex:
            print(f"   ! AI a esuat la un moment ({str(ex)[:70]}) — il las sa treaca pe selectia pe energie")
            ramase.append(e)
        time.sleep(2)   # ritm blând pt nivelul gratuit
    buni = [e for e in ramase if e.get("ai_scor", 0) >= 6]
    return buni if buni else [max(ramase, key=lambda e: e.get("ai_scor", 0))]   # mereu pastram cel mai bun


def transcrie_live(video, model_nume=None):
    model_nume = model_nume or os.environ.get("WHISPER_MODEL", "small")
    """AI local (faster-whisper): 1 transcript cu timpi pentru TOT live-ul.
    intoarce None daca pachetul nu e instalat (nu e obligatoriu)."""
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        return None
    m = WhisperModel(model_nume, device="cpu", compute_type="int8")
    segs, _ = m.transcribe(video, language="ro", vad_filter=True)
    return [(s.start, s.end, s.text.strip()) for s in segs if s.text.strip()]


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
    logo = logo if os.path.exists(logo) else None
    efecte = gaseste_efecte(assets_dir)
    confeti_p = os.path.join(assets_dir, "efecte", "confeti.webm")
    confeti_p = confeti_p if os.path.exists(confeti_p) else None
    pool_rand = gaseste_sfx_random(assets_dir)
    print(f"assets: muzica={'DA' if muzica else 'NU'} · logo={'DA' if logo else 'NU'} · "
          f"efecte={','.join(efecte) if efecte else 'niciunul'} · "
          f"confeti={'DA' if confeti_p else 'nu'} · sunete-random={len(pool_rand)}")

    w_src, h_src = rezolutie_sursa(ff, os.path.abspath(opt.video))
    tinta_h = 1440 if (opt.calitate == "2k" and h_src < 1440) else 0
    print(f"sursa: {w_src}x{h_src} -> export {'1440p (2K, lanczos+sharpen)' if tinta_h else 'rezolutie sursa'}")
    if opt.calitate == "2k" and h_src >= 1440:
        print("   live-ul TAIE deja in 2K+ -> pastram nativ, nimic de upscalat (cel mai bine)")
    print("1/4 Ascult live-ul (volum pe fiecare secunda)...")
    seria = analiza_audio(ff, opt.video)
    live_len = seria[-1][0]
    print(f"   live: {live_len//60} min · {len(seria)} secunde analizate")

    print("2/4 Caut momentele si construiesc POVESTILE...")
    varfuri, scor = detecteaza_explozii(seria)
    print(f"   {len(varfuri) if len(varfuri)>0 else 0} momente-explozie detectate in tot live-ul")
    if opt.momente:
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
            poarta = max(7.0, 0.5 * scor_max)
            varfuri_elita = [v for v in varfuri if v[1] >= poarta]
            print(f"   poarta de elita: scor >= {poarta:.1f} -> {len(varfuri_elita)} momente merita episod")
        else:
            varfuri_elita = []
        if opt.clasic:
            episoade = alege_clasic(varfuri_elita, scor, live_len, opt.durata, opt.max, [])
            p3 = opt.durata
        else:
            episoade, p3 = alege_povesti(varfuri_elita, scor, live_len, opt.durata, opt.max)
            episoade += alege_clasic(varfuri_elita, scor, live_len, opt.durata, opt.max, episoade)
    if not episoade:
        sys.exit("Niciun moment nu a trecut poarta de calitate. NU fac episoade slabe — regula ta: doar cel mai bun.")

    # transcript (daca e cerut de subtitrari SAU de AI) — o singura data, refolosit
    transcript = None
    if opt.subtitrari or opt.ai or pool_rand:
        tr = transcrie_live(os.path.abspath(opt.video))
        if tr is None:
            print("   (faster-whisper nu e instalat — subtitrari + sunete-semantice inactive: pip install faster-whisper)")
        else:
            transcript = tr
            print(f"   transcript AI: {len(tr)} replici")
            # MEMORIA: transcriptul fiecarui live intra in cunoastere/ (si in repo)
            cu_dir = os.path.join(baza, "cunoastere", "transcripte")
            os.makedirs(cu_dir, exist_ok=True)
            nume = datetime.now().strftime("LIVE_%Y-%m-%d_%H%M") + ".json"
            json.dump({"data": datetime.now().isoformat(), "sursa": os.path.basename(opt.video),
                       "replici": tr}, open(os.path.join(cu_dir, nume), "w", encoding="utf-8"),
                      ensure_ascii=False)
            print(f"   memorie: {nume} salvat in cunoastere/transcripte/")

    if opt.ai:
        cheie = citeste_cheie_gemini(baza)
        if not cheie:
            print("   MOD AI OPRIT: lipseste cheia. Gratis, 1 min: aistudio.google.com/apikey -> Get API key")
            print("   -> creezi fisier autoeditor/.env cu linia:  GEMINI_API_KEY=cheia_ta")
        else:
            model = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
            print(f"   MOD AI ACTIV ({model}): {len(episoade)} candidati judecati semantic...")
            episoade = evalueaza_cu_ai(ff, cheie, model, episoade, os.path.abspath(opt.video), transcript)
            print(f"   AI a pastrat {len(episoade)} episoade (cele cu scor mic au cazut)")
    print(f"   plan: {len(episoade)} episoade ({sum(1 for e in episoade if e['tip']=='poveste')} in modul poveste)")

    rap = ["# RAPORT AUTOEDITOR (POVESTEA) — " + datetime.now().strftime("%d.%m.%Y %H:%M"),
           f"Sursa: {opt.video} ({live_len//60} min) · episod: {opt.durata}s", ""]
    for k, e in enumerate(episoade, 1):
        if e.get("manual"):
            rap.append(f"- MOMENT EXACT ales de tine: {_ts(e['varf'])}")
        if e["tip"] == "poveste":
            sc = e["scene"]
            rap.append(f"## EP{k:02d} — POVESTEA (scor {e['scor']})")
            rap.append(f"- INTRO-REACTIE din {_ts(sc[0][0])} (teaserul momentului maxim)")
            rap.append(f"- SETUP din {_ts(sc[1][0])} (cum a pornit totul — inceputul live-ului)")
            rap.append(f"- DESFASURARE din {_ts(sc[2][0])} (actiunea creste — mijlocul)")
            rap.append(f"- MOMENTUL MAXIM din {_ts(sc[3][0])} (explozia completa)")
            rap.append(f"- Pe ecran: intrebare la 0:12 · hype la {_ts(START_P3-10)} · LIKE+comentariu la final")
        else:
            rap.append(f"## EP{k:02d} — CLASIC (scor {e['scor']})")
            rap.append(f"- Incepe la {_ts(e['scene'][0][0])} · explozie la {_ts(e['varf'])}")
        rap.append("")
    titluri = []
    for k, e in enumerate(episoade, 1):
        if e.get("ai_titlu"):
            rap.append(f"- TITLU AI (scor {e['ai_scor']}/10): {e['ai_titlu']}")
            if e.get("ai_in_joc"):
                rap.append(f"- IN JOC: {e['ai_in_joc']}")
            if e.get("ai_promite"):
                rap.append(f"- PROMIS=LIVRAT {'OK ✓' if e.get('ai_livrat', True) else 'RECALIBRAT ✓'} (promite: {e['ai_promite']})")
            titluri.append(f"EP{k:02d}: {e['ai_titlu']}")
    if not titluri:
        rap.append("Titlurile sunt SABLON — le personalizezi dupa ce vizionezi.")
    if titluri:
        open(os.path.join(folder, "titluri.txt"), "w", encoding="utf-8").write("\n".join(titluri) + "\n")
    open(os.path.join(folder, "RAPORT.md"), "w", encoding="utf-8").write("\n".join(rap))
    print("   raport: episodes/RAPORT.md")

    if opt.doar_analiza:
        print("GATA (doar analiza). Scoate --doar-analiza ca sa randeze.")
        return

    episoade = motiv_de_exista(episoade)
    print("3/4 Randez episoadele (cea mai lunga parte)...")
    h_out = tinta_h if tinta_h else (rezolutie_sursa(ff, os.path.abspath(opt.video))[1])
    sm_full = [v for _, v in seria]
    facute = []
    for k, e in enumerate(episoade, 1):
        eticheta = "POVESTEA" if e["tip"] == "poveste" else "clasic"
        # PROTECTIA RETENTIEI: daca finalul episodului e mort, il tai elastic (MrBeast:
        # tai cand s-a terminat povestea, nu cronometrul). Minim 90s.
        dead_pct, longest, cut_ep = profil_retentie(sm_full, e["scene"], opt.durata)
        durata_ep = opt.durata
        if cut_ep and cut_ep < opt.durata - 20:
            durata_ep = max(90, cut_ep)
            ramas = durata_ep - sum(d for _, d in e["scene"][:-1])
            e["scene"][-1] = (e["scene"][-1][0], max(20, int(ramas)))
            print(f"   EP{k:02d}: FINAL ELASTIC {opt.durata}->{durata_ep}s (zona moarta de {int(dead_pct)}% taiata)")
        sfx_rand = (alege_sfx_inteligent(pool_rand, durata_ep, transcript, e["scene"])
                    if pool_rand else None)
        e["_sfx"] = sfx_rand or []
        if sfx_rand:
            detalii = ", ".join(f"{int(t)//60}:{int(t)%60:02d} {os.path.basename(c)}" for t, c, _ in sfx_rand)
            print(f"   EP{k:02d} ({eticheta}) · sfx random: {detalii}{' + confeti' if confeti_p else ''}")
        else:
            print(f"   EP{k:02d} ({eticheta})...")
        out = comanda_randare(ff, os.path.abspath(opt.video), e, durata_ep, folder, muzica, logo, k,
                              efecte, tinta_h, sfx_rand, confeti_p, h_out)
        if out:
            facute.append((k, e, out))
            print(f"   OK -> episodes/{out}")

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
                f"texte engagement (intrebare+hype+CTA): DA · durata exacta: {opt.durata}s")
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
        titlu_full = e.get("ai_titlu") or f"CE S-A INTAMPLAT PE POKECITY?! Ep. {k}"
        cadru = os.path.join(folder, f"EP{k:02d}_cadru2.jpg")
        try:
            if os.path.exists(cadru):
                p = fa_miniatura(cadru, os.path.join(folder, f"EP{k:02d}_miniatura.jpg"), titlu_full, logo)
                print(f"   miniatura: {os.path.basename(p)}")
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
            f"TITLU:\n{titlu_full}\n\nDESCRIERE:\n{desc}\nTAG-URI (lipești în câmpul Tag-uri):\n{TAGURI}\n")

    print(f"\nGATA: {len(facute)} episoade in autoeditor/episodes/")
    print("URMATOR PAS: vizioneaza-le pe TOATE inainte de upload. Tu esti filtrul de calitate.")


if __name__ == "__main__":
    main()
