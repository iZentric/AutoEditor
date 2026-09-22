#!/usr/bin/env python3
r"""
FLUX — AUTOPILOT COMPLET (ca „Ask Studio" din YT Studio, dar care SI CONSTRUIESTE episoadele):

  python flux.py https://www.youtube.com/watch?v=XXXX          <- VOD-ul tau (il descarca singur)
  python flux.py prindere/live_full.mp4                        <- sau fisier local
  python flux.py live.mp4 --fara-ai                            <- selectie pe energie (fara Gemini)
  python flux.py live.mp4 --max 4 --calitate 2k

CE FACE, CAP-COADĂ (fara tu sa atingi nimic):
  1. INGHITE live-ul: il descarca de pe YouTube (yt-dlp) sau il ia local
  2. VIDEAZA TOT: Gemini (sau analiza audio) -> TOATE momentele cu minute
  3. ALEGE singur cele mai bune (regula ta: doar ce are motiv de exista)
  4. SCRIE momente.txt si LANSEAZA autoeditorul (2K, subtitrari, AI)
  5. PRIMESTI episoadele + titluri + miniaturi + kit de upload in episodes/

REZULTATUL: tu doar ai facut live-ul. Aici se termina si editing-ul.
"""
import argparse
import json
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import autoeditor as ae
import priveste as pr


def descarca_vod(url):
    """Descarca VOD-ul tau de pe YouTube (yt-dlp, cea mai buna calitate <=1080p60 pt editare)."""
    dosar = os.path.join(BASE, "prindere")
    os.makedirs(dosar, exist_ok=True)
    out = os.path.join(dosar, "vod_descarcat.mp4")
    if os.path.exists(out) and os.path.getsize(out) > 1_000_000:
        print(f"   deja descarcat: {out} (il refolosesc)")
        return out
    print("1/4 Descarc VOD-ul de pe YouTube (yt-dlp)...")
    cmd = [sys.executable, "-m", "yt_dlp", "-f", "bv*[height<=1080]+ba/b",
           "--merge-output-format", "mp4", "-o", out, url]
    r = subprocess.run(cmd, cwd=BASE)
    if r.returncode != 0 or not os.path.exists(out):
        sys.exit("Descarcarea a esuat. Alternativa: OBS Recording sau ia_live.py (README: Accesul direct).")
    return out


def momente_cu_gemini(cheie, video):
    """Gemini VIDEAZA tot materialul si intoarce momentele in JSON structurat."""
    creier = ""
    for fis, plafon in (("canal.md", 2500), ("reguli.md", 1200)):
        p = os.path.join(BASE, "cunoastere", fis)
        if os.path.exists(p):
            creier += open(p, encoding="utf-8").read()[:plafon] + "\n\n"
    prompt = (creier +
        "Esti PAL, editorul AI al canalului PokeCity (iZentric, Minecraft+Pokemon RO, copii 6-13). "
        "VIDEAZA INTREGUL material si alege CELE MAI BUNE momente pentru episoade de ~3 minute. "
        "Raspunzi DOAR cu JSON in forma exacta:\n"
        '{"momente": [{"start": "m:ss", "scor": 0-10, "descriere": "ce se vede+ce se spune, 1-2 propozitii", '
        '"titlu": "max 60 chars, promite doar ce se vede", "motiv": "de ce merita episod"}]}\n'
        "REGULI: 3-8 momente MAXIM, sortate dupa scor. Doar momente cu MOTIV fata de celelalte "
        "(un live plictisitor = 1 singur moment). Fara clickbait fals. Start = cu putin inainte de explozie.")
    if video.lower().startswith("http"):
        parts = [{"text": prompt}, {"text": "VIDEO: " + video}]
    else:
        uri, mime = pr.upload_fisier(cheie, os.path.abspath(video))
        parts = [{"file_data": {"mime_type": mime, "file_uri": uri}}, {"text": prompt}]
    print("2/4 Gemini vizioneaza TOT si alege momentele...")
    _, text = pr.cere_fallback(cheie, parts)
    txt = text.strip()
    if txt.startswith("```"):
        txt = txt.strip("`")
        if txt.startswith("json"):
            txt = txt[4:]
    d = json.loads(txt)
    return d.get("momente", [])


def momente_cu_urechile(video):
    """Fara Gemini: selectia pe energie (poarta de elita), ca in autoeditor."""
    ff = ae.gaseste_ffmpeg()
    seria = ae.analiza_audio(ff, video)
    varfuri, scor = ae.detecteaza_explozii(seria)
    if varfuri:
        poarta = max(7.0, 0.5 * max(s for _, s in varfuri))
        elita = [v for v in varfuri if v[1] >= poarta]
    else:
        elita = []
    iesire = [{"start": f"{s // 60}:{s % 60:02d}", "scor": round(s, 1),
               "descriere": "(selectie pe energie)", "titlu": "", "motiv": "scor peste prag"}
              for s, s2 in elita[:8]]
    return iesire


def scrie_momente(momente, cale):
    with open(cale, "w", encoding="utf-8") as f:
        f.write("# momente alese de FLUX\n")
        for m in momente:
            f.write(str(m["start"]) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sursa", help="link YouTube VOD sau fisier local")
    ap.add_argument("--max", type=int, default=6)
    ap.add_argument("--calitate", default="2k", choices=["1080p", "2k"])
    ap.add_argument("--fara-ai", action="store_true", help="selectie pe energie, fara Gemini")
    opt = ap.parse_args()

    # 1) sursa
    if opt.sursa.startswith("http"):
        video = descarca_vod(opt.sursa)
    else:
        video = os.path.abspath(opt.sursa)
        if not os.path.exists(video):
            sys.exit(f"Nu gasesc {video}")
    print(f"1/4 Sursa: {video}")

    # 2+3) alegerea momentelor
    momente = []
    if not opt.fara_ai:
        cheie = ae.citeste_cheie_gemini(BASE)
        if cheie:
            try:
                momente = momente_cu_gemini(cheie, video)[:opt.max]
            except Exception as ex:
                print(f"   ! Gemini a esuat ({str(ex)[:80]}) -> trec pe selectia pe energie")
        else:
            print("   (fara cheie Gemini -> selectie pe energie; pune GEMINI_API_KEY in .env pentru ochii complei)")
    if not momente:
        momente = momente_cu_urechile(video)[:opt.max]
    if not momente:
        sys.exit("Niciun moment cu motiv de exista. NU fac episoade slabe.")
    for m in momente:
        print(f"   {m['start']} · scor {m['scor']} · {m.get('descriere', '')[:60]}")

    # 4) randarea
    fis_momente = os.path.join(BASE, "momente_auto.txt")
    scrie_momente(momente, fis_momente)
    print(f"3/4 momente_auto.txt scris ({len(momente)} momente). Lansez autoeditorul...")
    cmd = [sys.executable, os.path.join(BASE, "autoeditor.py"), video,
           "--momente", fis_momente, "--calitate", opt.calitate, "--subtitrari", "--ai"]
    r = subprocess.run(cmd, cwd=BASE)
    if r.returncode != 0:
        sys.exit("Randarea a esuat — vezi mesajele de mai sus / episodes/err.txt")

    print("4/4 GATA. Episoadele + titlurile + miniaturile + kit-ul sunt in autoeditor/episodes/")
    print("     Analiza completa a live-ului: cunoastere/analize/ (din rularea PRIVESTE asociata)")
    print("     URMATORUL PAS (singurul manual): vizioneaza episoadele, apoi uploadeaza.")


if __name__ == "__main__":
    main()
