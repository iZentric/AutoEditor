#!/usr/bin/env python3
"""
VEGHEAZA — paznicul canalului. Tu faci live; el isi da seama SINGUR cand e gata
si porneste FLUX (descarca -> vede tot -> alege -> randeaza episoade).

  python vegheaza.py              <- il lasi deschis; verifica la 10 minute
  python vegheaza.py --odata      <- o singura verificare (ca sa testezi)
  python vegheaza.py --interval 5 (minute intre verificari)

Cum stie ca e live nou? Uitareste ultimele 8 videoclipuri ale canalului (yt-dlp,
fara API key). Orice video MAI LUNG de 30 de minute care nu a fost procesat =
live VOD -> il ia la procesat. Shorts si clipuri sunt ignorate automat.

Cand gaseste: marcheaza in vegheaza_state.json (ca sa nu-l ia de 2 ori),
porneste flux.py cu link-ul si tipareste progresul. Tu revii doar la final.
"""
import argparse
import json
import os
import subprocess
import sys
import time

BASE = os.path.dirname(os.path.abspath(__file__))
CANAL = os.environ.get("YOUTUBE_CHANNEL_URL",
                       "https://www.youtube.com/channel/UCBoZcTLayAUgYTPsyrStiLg")
STARE = os.path.join(BASE, "vegheaza_state.json")
MIN_DUR = 900  # 15 min: formatul tau (episoade/live-uri); shorts si clipuri sunt in alt tab, ignorate


def citeste_stare():
    if os.path.exists(STARE):
        try:
            return set(json.load(open(STARE, encoding="utf-8")))
        except Exception:
            return set()
    return set()


def salveaza_stare(stare):
    json.dump(sorted(stare), open(STARE, "w", encoding="utf-8"), indent=1)


def listeaza_canal():
    """Ultimele videoclipuri ale canalului: [(id, durata_sec, titlu)] — yt-dlp, fara API key."""
    cmd = [sys.executable, "-m", "yt_dlp", "--flat-playlist", "--playlist-end", "8",
           "--print", "%(id)s\t%(duration)s\t%(title)s", CANAL + "/videos"]
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=BASE)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip().splitlines()[-1] if r.stderr.strip() else "yt-dlp a esuat")
    iesire = []
    for linie in r.stdout.strip().splitlines():
        bucati = linie.split("\t")
        if len(bucati) != 3:
            continue
        vid, dur, titlu = bucati
        try:
            dur = int(float(dur)) if dur not in ("NA", "") else 0
        except ValueError:
            dur = 0
        iesire.append((vid, dur, titlu))
    return iesire


def gaseste_live_nou(stare, min_dur=MIN_DUR):
    """Primul video lung inca neprocesat (live/episod nou), sau None."""
    for vid, dur, titlu in listeaza_canal():
        if vid in stare:
            continue
        if dur >= min_dur:
            return vid, titlu
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--odata", action="store_true", help="o singura verificare, apoi iese")
    ap.add_argument("--interval", type=int, default=10, help="minute intre verificari (implicit 10)")
    opt = ap.parse_args()
    stare = citeste_stare()
    print("VEGHEAZA pornit pe canalul tau. Tu doar faci live — episoadele apar in episodes/.")
    while True:
        gasit = None
        try:
            gasit = gaseste_live_nou(stare)
        except Exception as ex:
            print(f"   ! verificarea a esuat ({str(ex)[:100]}) — reincerc")
        if gasit:
            vid, titlu = gasit
            url = "https://www.youtube.com/watch?v=" + vid
            print(f">>> LIVE NOU GASIT: {titlu[:70]}")
            print("    pornesc FLUX (descarcare + analiza + editare)... poate dura mult.")
            stare.add(vid)
            salveaza_stare(stare)  # marcat INAINTE, ca sa nu-l ia de 2 ori
            r = subprocess.run([sys.executable, os.path.join(BASE, "flux.py"), url], cwd=BASE)
            if r.returncode != 0:
                print(f"    ! FLUX a esuat (cod {r.returncode}). Repara si ruleaza manual:")
                print(f"      python flux.py {url}")
            print("    GATA. Astept urmatorul live...")
        elif opt.odata:
            print("Niciun live nou de procesat.")
            break
        if opt.odata:
            break
        time.sleep(opt.interval * 60)


if __name__ == "__main__":
    main()
