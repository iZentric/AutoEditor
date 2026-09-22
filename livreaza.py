#!/usr/bin/env python3
"""
LIVREAZA — pipeline-ul complet, rulat de AGENT in laborator:
gaseste cel mai nou video de pe canal -> il descarca -> Gemini il vede TOT ->
alege momentele -> randeaza episoadele -> le PUNE PE GITHUB la Releases.

Creatorul nu instaleaza nimic: face live, zice „ia-l", si apoi descarca
video-urile gata de la github.com/iZentric/AutoEditor -> Releases.

  python livreaza.py                 <- cel mai nou video lung de pe canal
  python livreaza.py <link|fisier>   <- sursa exacta
  python livreaza.py --max 3         <- maxim N episoade (implicit 4)
Sterge local tot ce e greu (VOD + episoade) DUPA upload — la noi nu se strica nimic.
"""
import argparse
import glob
import json
import os
import subprocess
import sys
import time
import urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import flux as fx
import vegheaza as vg


def env_cheie(nume):
    for linie in open(os.path.join(BASE, ".env"), encoding="utf-8"):
        linie = linie.strip()
        if linie.startswith(nume + "="):
            return linie.split("=", 1)[1].strip()
    return None


def api(url, token, method="GET", data=None, tip=None):
    req = urllib.request.Request(url, method=method,
        headers={"Authorization": f"Bearer {token}",
                 "Accept": "application/vnd.github+json"})
    if data is not None:
        req.add_header("Content-Type", tip or "application/json")
        req.data = data if isinstance(data, bytes) else json.dumps(data).encode()
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read() or b"{}")


def release_pt_azi(token):
    tag = time.strftime("live-%Y-%m-%d")
    try:
        return api(f"https://api.github.com/repos/iZentric/AutoEditor/releases/tags/{tag}", token)
    except Exception:
        body = ("Episoade gata de upload, generate automat din ultimul live.\n\n"
                "Fiecare EP are alaturi fisierul *_upload.txt cu TITLU + DESCRIERE + TAG-URI "
                "(copy-paste in YouTube Studio). uploadeti video-ul cu acelasi numar.\n\n"
                "Generat de LIVREAZA la " + time.strftime("%d.%m.%Y %H:%M"))
        return api("https://api.github.com/repos/iZentric/AutoEditor/releases", token,
                   method="POST",
                   data={"tag_name": tag, "target_commitish": "main",
                         "name": f"Episoade {time.strftime('%d.%m.%Y')}", "body": body})


def urca_asset(token, rid, cale, nume, incercari=3):
    url = f"https://uploads.github.com/repos/iZentric/AutoEditor/releases/{rid}/assets?name={nume}"
    date = open(cale, "rb").read()
    for i in range(incercari):
        try:
            req = urllib.request.Request(url, method="POST", data=date,
                headers={"Authorization": f"Bearer {token}",
                         "Content-Type": "application/octet-stream"})
            with urllib.request.urlopen(req, timeout=1800) as r:
                d = json.loads(r.read())
            return d.get("name"), d.get("size", 0)
        except Exception as ex:
            if i == incercari - 1:
                raise
            print(f"   (upload esuat {str(ex)[:60]}; reincerc {i+2}/{incercari})")
            time.sleep(10)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sursa", nargs="?", default=None)
    ap.add_argument("--max", type=int, default=4)
    ap.add_argument("--pastra-local", action="store_true")
    opt = ap.parse_args()

    token = env_cheie("GITHUB_TOKEN")
    if not token:
        sys.exit("Lipseste GITHUB_TOKEN din .env")

    # 1) sursa
    if opt.sursa:
        sursa = opt.sursa
    else:
        gasit = vg.gaseste_live_nou(vg.citeste_stare())
        if not gasit:
            sys.exit("Niciun video nou pe canal.")
        vid, titlu = gasit
        sursa = "https://www.youtube.com/watch?v=" + vid
        print(f"1/5 Video nou gasit: {titlu[:60]}")

    # 2) descarcare (link) sau local
    if sursa.startswith("http"):
        video = fx.descarca_vod(sursa)
    else:
        video = os.path.abspath(sursa)
    print(f"2/5 Am materialul: {video}")

    # 3) analiza + momente
    cheie = fx.ae.citeste_cheie_gemini(BASE)
    momente = []
    if cheie:
        try:
            momente = fx.momente_cu_gemini(cheie, video)[:opt.max]
        except Exception as ex:
            print(f"   ! Gemini a esuat ({str(ex)[:70]}) -> pe energie")
    if not momente:
        momente = fx.momente_cu_urechile(video)[:opt.max]
    if not momente:
        sys.exit("Niciun moment cu motiv de exista — NU livrez gunoi.")
    for m in momente:
        print(f"   moment {m['start']} · scor {m['scor']}")

    # 4) randare
    fis_m = os.path.join(BASE, "momente_auto.txt")
    fx.scrie_momente(momente, fis_m)
    print("4/5 Randez episoadele (poate dura cateva minute)...")
    r = subprocess.run([sys.executable, os.path.join(BASE, "autoeditor.py"), video,
                        "--momente", fis_m, "--subtitrari", "--ai"], cwd=BASE)
    if r.returncode != 0:
        sys.exit("Randarea a esuat.")
    episoade = [e for e in sorted(glob.glob(os.path.join(BASE, "episodes", "EP*.mp4")))
                if os.path.getsize(e) > 5_000_000]          # sub 5MB = ffmpeg a crapat -> NU livram gunoi
    sparte = len(glob.glob(os.path.join(BASE, "episodes", "EP*.mp4"))) - len(episoade)
    if sparte:
        print(f"   ! {sparte} episoade sparte (render esuat) — aruncate, nu urcate")
    if not episoade:
        sys.exit("Niciun episod sanatos produs — vezi episodes/err.txt")
    print(f"5/5 {len(episoade)} episoade gata local. Urca pe GitHub...")

    # 5) release + upload
    rel = release_pt_azi(token)
    rid = rel["id"]
    urcate = []
    for cale in episoade + sorted(glob.glob(os.path.join(BASE, "episodes", "EP*_upload.txt"))):
        nume = os.path.basename(cale)
        print(f"   urc {nume} ({os.path.getsize(cale) // 1048576} MB)...")
        nume_u, marime = urca_asset(token, rid, cale, nume)
        urcate.append((nume_u, marime))
        print(f"   OK {nume_u}")
    analiza = sorted(glob.glob(os.path.join(BASE, "cunoastere", "analize", "ANALIZA_*.md")))
    if analiza:
        urca_asset(token, rid, analiza[-1], os.path.basename(analiza[-1]))

    # 6) curatenie locala (grea)
    if not opt.pastra_local:
        for c in [video] + episoade:
            try:
                os.remove(c)
            except OSError:
                pass
        # marcam in memoria veghezei ca e procesat
        if sursa.startswith("http"):
            vid = sursa.split("v=")[-1]
            stare = vg.citeste_stare()
            stare.add(vid)
            vg.salveaza_stare(stare)
    print("LIVRAT: github.com/iZentric/AutoEditor -> Releases")
    for nume_u, marime in urcate:
        print(f"   {nume_u} ({round(marime / 1048576, 1)} MB)")


if __name__ == "__main__":
    main()
