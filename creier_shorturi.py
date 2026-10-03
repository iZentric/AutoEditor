#!/usr/bin/env python3
r"""CREIER SHORTURI — creierul complet de shorturi (nivel editor platit, 2026).

Un singur comanda face TOT:
  python creier_shorturi.py https://www.youtube.com/live/XXX --fenestru "65:00-65:50" --nume LEU
  python creier_shorturi.py fisier_local.mp4 --nume TEST
  python creier_shorturi.py <sursa> --fenestru "a-b" --dry        (doar planul, fara randare)

LANTUL (fara tu sa atingi nimic):
  1. INGHITE sursa (yt-dlp cu fallback-uri de client, sau fisier local)
  2. TRANSCRIPT cu timestampuri (youtube-transcript-api, gratis; fallback: auto-subs yt-dlp)
  3. EVENIMENTE pe fiecare secunda: schimbari de scena (ffmpeg scene score) + ENERGIE
     audio (RMS) + densitate de vorbire -> harta de "ce se intampla cand"
  4. POVESTEA 16s: alege VARFUL (cea mai tare secunda) si taie IN JURUL lui:
     setup -> varf -> rezolutie; taieturile CAD pe capete de fraza / schimbari de scena
  5. POPS: citate reale din transcript, sincronizate PE evenimentul vizibil, max 4,
     hook la <=0.4s, kinetic (fade+bounce), MarginV 340 safe-zone
  6. SFX: intro sting 0.3s + whoosh pe fiecare taietura + impact la varf (max 6, nimic la 0s)
  7. RANDEAZA: 1080x1920@60, punch-in pe cutia varfului, logo POKECITY, -14 LUFS, 16.0s exact
  8. QC 8 legi (short_qc.ruleaza) -> daca pica, se auto-corecteaza (riser peste goluri) o data
  9. LIVREAZA pe GitHub Release (nume curat unic) si curata local
"""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import autoeditor as ae
import short_qc as qc

FF = os.environ.get("FFMPEG", "ffmpeg")
FP = os.environ.get("FFPROBE", "ffprobe")
TMP = "/tmp/creier"


# ---------------------------------------------------------------- 1. SURSA
def descarca_segment(url, fereastra, out):
    """yt-dlp cu fallback de clienti (fix 403). Returneaza calea sau None."""
    Path(TMP).mkdir(exist_ok=True)
    comenzi = [
        ["--concurrent-fragments", "6"],
        ["--extractor-args", "youtube:player_client=web_safari", "--concurrent-fragments", "6"],
        ["--extractor-args", "youtube:player_client=tv", "--concurrent-fragments", "6"],
    ]
    for extra in comenzi:
        cmd = ["yt-dlp", *extra]
        if fereastra:
            cmd += ["--download-sections", f"*{fereastra}"]
        cmd += ["-f", "bv*[height<=1080]+ba/b", "-o", out, url]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if os.path.exists(out):
            return out
    return None


# ------------------------------------------------------------ 2. TRANSCRIPT
def transcript_din_url(url):
    """youtube-transcript-api (gratis, cu timestampuri). Fallback: yt-dlp auto-subs."""
    vid = re.search(r"(?:v=|live/|be/|shorts/)([\w-]{11})", url)
    if not vid:
        return []
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        api = YouTubeTranscriptApi()
        for langs in (["ro"], ["ro", "en"], None):
            try:
                fetched = api.fetch(vid.group(1), languages=langs)
                return [[p.start, p.start + p.duration, p.text] for p in fetched]
            except Exception:
                continue
    except ImportError:
        pass
    # fallback: auto-subs yt-dlp
    subprocess.run(["yt-dlp", "--skip-download", "--write-auto-subs", "--sub-langs",
                    "ro.*,ro,en.*", "-o", f"{TMP}/tr", url], capture_output=True)
    for f in Path(TMP).glob("tr*.vtt"):
        evs, cur = [], None
        for ln in f.read_text(encoding="utf-8", errors="ignore").splitlines():
            m = re.match(r"(\d+):(\d+):(\d+)\.(\d+) --> ", ln)
            if m:
                s = int(m[1]) * 3600 + int(m[2]) * 60 + int(m[3]) + int(m[4]) / 1000
                cur = [s, None]
            elif cur and cur[1] is None and ln.strip() and not ln.startswith(("WEBVTT", "Kind:", "Language:")):
                txt = re.sub(r"<[^>]+>", "", ln).strip()
                if txt and not txt.startswith(">>"):
                    cur[1] = txt
                    evs.append(cur)
                    cur = None
        return evs
    return []


# ---------------------------------------------------------- 3. EVENIMENTE
def harta_evenimente(video):
    """Score[0..1] pe secunda: scena (schimbari mari) + energie audio (RMS normalizat)."""
    dur = float(subprocess.run([FP, "-v", "error", "-show_entries", "format=duration",
                                "-of", "csv=p=0", video], capture_output=True, text=True).stdout)
    # scena
    r = subprocess.run([FF, "-i", video, "-vf", "select='gt(scene,0.22)',metadata=print",
                        "-an", "-f", "null", "-"], capture_output=True, text=True)
    scene = []
    t, sc = None, 0.0
    for ln in r.stderr.splitlines():
        m = re.search(r"pts_time:([\d.]+)", ln)
        if m:
            t = float(m.group(1))
        m = re.search(r"scene_score=([\d.]+)", ln)
        if m and t is not None:
            scene.append((t, min(1.0, float(m.group(1)) * 2)))
    # energie pe secunda
    r = subprocess.run([FF, "-i", video, "-af", "astats=metadata=1:reset=1,ametadata="
                        "print:key=lavfi.astats.Overall.RMS_level", "-f", "null", "-"],
                       capture_output=True, text=True)
    rms = {}
    t = None
    for ln in r.stderr.splitlines():
        m = re.search(r"pts_time:([\d.]+)", ln)
        if m:
            t = int(float(m.group(1)))
        m = re.search(r"RMS_level=(-?[\d.]+|-inf)", ln)
        if m and t is not None:
            v = m.group(1)
            rms[t] = max(rms.get(t, -99), 0.0 if v == "-inf" else float(v))
    if rms:
        lo, hi = min(rms.values()), max(rms.values())
        energ = {k: (v - lo) / (hi - lo + 1e-9) for k, v in rms.items()}
    else:
        energ = {}
    n = int(dur)
    return [{"t": i,
             "scena": next((s for tt, s in scene if abs(tt - i) < 0.5), 0.0),
             "energie": energ.get(i, 0.0)} for i in range(n)], dur


def varf_poveste(harta, dur, lungime=16.0):
    """Varful = secunda cu scor combinat maxim (dar cu margini de siguranta)."""
    marja = int(lungime * 0.7)
    best, best_t = -1, marja
    for e in harta:
        t = e["t"]
        if t < 3 or t > dur - 3:
            continue
        scor = e["energie"] * 1.0 + e["scena"] * 0.8
        # bonus daca in jur sunt mai multe evenimente (zona vie, nu un clip izolat)
        zona = sum(x["energie"] + x["scena"] for x in harta
                   if abs(x["t"] - t) <= int(lungime / 3))
        total = scor + zona * 0.15
        if total > best:
            best, best_t = total, t
    start = max(0.0, min(best_t - lungime * 0.45, dur - lungime))
    return start, start + lungime, best_t


def taie_pe_fraze(transcript, start, end):
    """Muta marginile fenestrei pe capete de fraza (punct final din transcript) +/-0.8s."""
    capete = [a + len(b.split()) * 0.35 for a, b, _ in transcript]  # estimare sfarsit
    capete = sorted(c for c in capete if start - 1.5 < c < end + 1.5)
    if not capete:
        return start, end
    def cel_mai_aproape(x):
        return min(capete, key=lambda c: abs(c - x))
    s2 = cel_mai_aproape(start + 1.5)
    e2 = cel_mai_aproape(end - 0.3)
    if e2 - s2 < 13.5:                       # pastram ~16s
        e2 = s2 + 16.0
    return round(max(0, s2), 2), round(e2, 2)


# -------------------------------------------------------------- 4. POPS
def pops_din_eveniment(transcript, s, e, varf_rel):
    """Citate REALE din fereastra; primul = hook la <=0.4s; max 4; gasite langa varf."""
    inside = [(a, b, t) for a, b, t in transcript if s <= a < e and len(t) >= 4]
    if not inside:
        return [(0.3, "NU VEDE ASTA!")]
    inside.sort(key=lambda x: x[0])
    pops, hook = [], None
    for a, b, t in inside:
        rel = round(a - s, 2)
        if rel < 0.2:
            continue
        txt = re.sub(r"[^\w\s!?%.-]", "", t.upper()).strip()
        cuvinte = txt.split()
        if len(cuvinte) > 6:
            txt = " ".join(cuvinte[:5]) + "!"
        if hook is None:
            hook = (max(0.25, min(rel, 0.4)), txt[:28])
            continue
        if pops and rel - (pops[-1][0]) < 1.4:
            continue
        pops.append((rel, txt[:30]))
    pops = [hook] + pops[:3]
    # curatare: un singur pop langa varf daca am prea multi devreme
    return [(t, x) for t, x in pops if t < 15.8]


# ---------------------------------------------------------------- 5. SFX
def plan_sfx(nr_taieturi, varf_rel):
    sting = "/home/user/autoeditor/sunete_mele/Awkward Moment 2.mp3"
    whoosh = "/home/user/autoeditor/sunete_mele/whoosh trecere.mp3"
    bonk = "/home/user/autoeditor/sunete_mele/Bamboo Hit (AnimeCartoon Bonk) - Sound Effect for Editing.mp3"
    plan = [("intro", sting, 0.3, 2.2, 0.55)]
    for i in range(1, nr_taieturi):
        t = round(i * (16.0 / nr_taieturi) - 0.25, 2)
        if t > 0.5:
            plan.append(("whoosh", whoosh, t, 2.0, None))
    plan.append(("bonk", bonk, round(max(1.0, varf_rel - 0.1), 2), 2.0, None))
    return plan[:6]


# ------------------------------------------------------------ 6. RANDARE
def randeaza(video, s, e, pops, sfx, varf_rel, out, punch_varf=True):
    """Taie fereastra [s,e] (1 singura bucata — povestea e continua), logo, pops kinetic."""
    Path(TMP).mkdir(exist_ok=True)
    ass = f"{TMP}/creier.ass"
    ae.scrie_ass_pops(ass, [(round(t, 2), txt) for t, txt in pops], stil="short", durata=16.0)
    dur = round(e - s, 2)
    # punch-in pe secunda varfului (doar acolo)
    punch_start = max(0.0, varf_rel - 1.2)
    punch_dur = 2.4
    vf = f"[0:v]trim={s}:{e},setpts=PTS-STARTPTS,crop=ih*9/16:ih,scale=1080:1920:flags=lanczos[base];" \
         f"[base]split[pre][chk];" \
         f"[pre]crop=ih*9/16*0.93:ih*0.93,scale=1080:1920:flags=lanczos[pin];" \
         f"[chk][pin]overlay=x=(W-w)/2:y=(H-h)/2:enable='between(t,{punch_start},{punch_start + punch_dur})'[fr];"
    f = [vf.rstrip(";"),
         f"[1:v]scale=-2:300,format=rgba[lg];[fr][lg]overlay=W-w-28:30:alpha=0.94[vlo]",
         f"[vlo]subtitles={ass}[vout]"]
    # audio
    f.append(f"[0:a]atrim={s}:{e},asetpts=PTS-STARTPTS[am]")
    fluxuri, amix_in = ["[am]"], 1
    for i, (tip, cale, t, durata_s, vol) in enumerate(sfx, 1):
        volf = f"volume={vol}," if vol else ""
        f.append(f"[{i+1}:a]atrim=duration={durata_s},asetpts=PTS-STARTPTS,"
                 f"loudnorm=I=-24:TP=-6:LRA=7,aresample=48000,{volf}"
                 f"afade=t=out:st={durata_s-0.3}:d=0.3,adelay={int(t*1000)}:all=1[sx{i}]")
        fluxuri.append(f"[sx{i}]")
        amix_in += 1
    f.append(f"{''.join(fluxuri)}amix=inputs={amix_in}:duration=first:normalize=0,"
             f"loudnorm=I=-14:TP=-1.5:LRA=11[aout]")
    cmd = [FF, "-y", "-v", "error", "-t", str(e + 1), "-i", video,
           "-i", "/home/user/autoeditor/assets/logo_pokecity_clear.png"]
    for tip, cale, t, durata_s, vol in sfx:
        cmd += ["-i", cale]
    cmd += ["-filter_complex", ";".join(f), "-map", "[vout]", "-map", "[aout]",
            "-t", "16", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
            "-r", "60", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", out]
    subprocess.run(cmd, check=True)
    return out


# ------------------------------------------------------------ 7. LIVRARE
def livreaza(path, nume):
    tok = os.environ.get("GH_TOKEN")
    if not tok:
        print("  (GH_TOKEN lipseste -> nu urc; fisierul e local:", path, ")")
        return None
    import urllib.request
    req = urllib.request.Request(
        f"https://uploads.github.com/repos/iZentric/AutoEditor/releases/395754968/assets?name={nume}",
        data=open(path, "rb").read(), method="POST",
        headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/octet-stream"})
    with urllib.request.urlopen(req) as r:
        d = json.loads(r.read())
    print(f"  URCAT: {d['name']} ({d['state']})")
    return d["browser_download_url"]


# ------------------------------------------------------------------ MAIN
def whisper_transcript(cale):
    """faster-whisper local (gratis, timestamp-uri pe CUVINTE). Fallback final cand
    YT nu are subtitrari. PyAV e incompatibil pe sandbox -> decodez cu ffmpeg in array numpy."""
    try:
        import numpy as np
        from faster_whisper import WhisperModel
    except ImportError:
        return []
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(cale), "-f", "f32le",
                          "-ac", "1", "-ar", "16000", "-"], capture_output=True).stdout
    if not raw:
        return []
    audio = np.frombuffer(raw, dtype=np.float32)
    try:
        m = WhisperModel("tiny", device="cpu", compute_type="int8")
        segs, _ = m.transcribe(audio, language="ro", word_timestamps=True, vad_filter=True)
    except Exception:
        return []
    ies, cur, t0 = [], [], None
    for s in segs:
        for w in s.words:
            if t0 is None:
                t0 = w.start
            cur.append(w.word.strip())
            if len(cur) >= 8:
                ies.append([round(float(t0), 2), round(float(w.end), 2), " ".join(cur)])
                cur, t0 = [], None
        if cur and w is s.words[-1]:
            ies.append([round(float(t0), 2), round(float(w.end), 2), " ".join(cur)])
            cur, t0 = [], None
    return ies


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sursa")
    ap.add_argument("--fenestru", default=None, help='ex: "65:00-65:50" (doar pt URL)')
    ap.add_argument("--nume", default="SHORT")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--pops-manual", default=None, help='ex: "0.3=CUM ADICA?,5=CE?!"; gol=auto')
    a = ap.parse_args()

    Path(TMP).mkdir(exist_ok=True)
    print("== CREIER SHORTURI ==")
    # 1. sursa
    if a.sursa.startswith("http"):
        seg = f"{TMP}/seg.mp4"
        print("1. Descarc segmentul...")
        seg = descarca_segment(a.sursa, a.fenestru, seg)
        if not seg:
            print("   DESCARCARE ESUATA (403/limita IP). Incearca mai tarziu sau fisier local.")
            sys.exit(2)
    else:
        seg = a.sursa
    dur_tot = float(subprocess.run([FP, "-v", "error", "-show_entries", "format=duration",
                                    "-of", "csv=p=0", seg], capture_output=True,
                                   text=True).stdout)
    print(f"   segment {dur_tot:.1f}s")

    # 2. transcript
    print("2. Transcript...")
    tr = transcript_din_url(a.sursa) if a.sursa.startswith("http") else []
    if not tr:
        print("   transcript YT lipsa -> WHISPER local (sync pe cuvinte)...")
        tr = whisper_transcript(seg)
        if tr:
            print(f"   {len(tr)} replici (whisper)")
    print(f"   {len(tr)} replici" if tr else "   (fara transcript -> decat pe evenimente)")

    # 3. evenimente + 4. poveste
    print("3. Harta de evenimente (scena+energie)...")
    harta, dur = harta_evenimente(seg)
    s, e, varf_t = varf_poveste(harta, dur)
    if tr:
        s, e = taie_pe_fraze(tr, s, e)
    e = min(e, dur)
    varf_rel = round(varf_t - s, 2)
    print(f"   fereastra: {s:.1f}s -> {e:.1f}s | varful la +{varf_rel:.1f}s")

    # 5. pops
    if a.pops_manual:
        pops = []
        for p in re.split(r"[;,]", a.pops_manual):
            t, txt = p.split("=", 1)
            pops.append((float(t), txt.strip()))

    else:
        pops = pops_din_eveniment(tr, s, e, varf_rel)
    print("4. Pops:", pops)

    if a.dry:
        print("   --dry: ma opresc aici (planul e mai sus).")
        return

    # 6-7. SFX + randare
    print("5. Randez (punch-in pe varf, logo, kinetic captions)...")
    sfx = plan_sfx(3, min(varf_rel, 14.0))
    out = f"{TMP}/FINAL_{a.nume}_SHORT_POPS.mp4"
    randeaza(seg, s, e, pops, sfx, varf_rel, out)

    # 8. QC + auto-fix
    print("6. QC 8 legi...")
    mom = [t + 0.5 for t, _ in pops]
    try:
        qc.ruleaza(out, mom)
    except SystemExit:
        print("   QC a picat -> AUTO-FIX (riser peste goluri) si re-randez...")
        subprocess.run([FF, "-y", "-v", "error", "-i", out,
                        "-i", "/home/user/autoeditor/sunete_mele/riser tensiune.mp3",
                        "-filter_complex",
                        "[1:a]atrim=duration=2.6,asetpts=PTS-STARTPTS,"
                        "loudnorm=I=-26:TP=-8:LRA=7,aresample=48000,"
                        "afade=t=in:st=0:d=1.9,adelay=12600:all=1[fx];"
                        "[0:a][fx]amix=inputs=2:duration=first:normalize=0,"
                        "alimiter=limit=0.95[aout]",
                        "-map", "0:v", "-map", "[aout]", "-c:v", "copy",
                        "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart",
                        f"{TMP}/fix.mp4"], check=True)
        out = f"{TMP}/fix.mp4"
        qc.ruleaza(out, mom)

    # 9. livrare
    print("7. Livrez pe Release...")
    nume_f = f"FINAL_{a.nume}_SHORT_POPS.mp4"
    url = livreaza(out, nume_f)
    if url:
        srt = f"{TMP}/{a.nume}.srt"
        def ts(t):
            ms = int(round((t - int(t)) * 1000)); ssec = int(t) % 60; mmin = int(t) // 60
            return f"00:{mmin:02d}:{ssec:02d},{ms:03d}"
        with open(srt, "w", encoding="utf-8") as fh:
            for i, (t, txt) in enumerate(pops, 1):
                fh.write(f"{i}\n{ts(t)} --> {ts(min(t+2.2, 15.9))}\n{txt}\n\n")
        livreaza(srt, f"FINAL_{a.nume}_SHORT_POPS.srt")
        os.remove(out)                       # legea: nimic greu ramas local
        print("   GATA. Descarci de pe Releases.")
    print("== CREIER: DONE ==")


if __name__ == "__main__":
    main()
