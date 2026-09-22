#!/usr/bin/env python3
r"""
PRIVESTE — Gemini VIDEAZA tot: dai un link YouTube sau un fisier si obtine
analiza completa: transcript + CE SE VEDE in joc + momentele cu minute + idei de episoade.

FOLOSIRE:
  python priveste.py https://www.youtube.com/watch?v=XXXX     <- VOD-ul tau de pe canal (RECOMANDAT)
  python priveste.py live_comprimat.mp4                        <- fisier local (max 2GB)

OUTPUT: cunoastere/analize/ANALIZA_<data>.md + afisat in consola.
Apoi momentele alese le pui in momente.txt si rulezi autoeditorul ca de obicei.
"""
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import autoeditor as ae

UPLOAD = "https://generativelanguage.googleapis.com/upload/v1beta/files"
GEN = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def citeste_cheie():
    k = ae.citeste_cheie_gemini(BASE)
    if not k:
        sys.exit("Lipseste GEMINI_API_KEY in autoeditor/.env (gratis: aistudio.google.com/apikey)")
    return k


def mime_de(cale):
    if cale.lower().endswith(".mp4"):
        return "video/mp4"
    if cale.lower().endswith(".webm"):
        return "video/webm"
    if cale.lower().endswith(".mkv"):
        return "video/x-matroska"
    return "video/mp4"


def upload_fisier(cheie, cale):
    """File API, upload resumable (format din docs oficiale ai.google.dev)."""
    dim = os.path.getsize(cale)
    if dim > 2 * 1024 ** 3:
        sys.exit("Fisierul e peste 2GB (limita File API). Comprima-l sau foloseste link-ul YouTube al VOD-ului.")
    mime = mime_de(cale)
    print(f"1/3 Incarc {os.path.basename(cale)} ({dim/1e6:.0f} MB) la Google...")
    cerere = urllib.request.Request(
        UPLOAD,
        data=json.dumps({"file": {"display_name": os.path.basename(cale)}}).encode(),
        method="POST",
        headers={"x-goog-api-key": cheie,
                 "X-Goog-Upload-Protocol": "resumable",
                 "X-Goog-Upload-Command": "start",
                 "X-Goog-Upload-Header-Content-Length": str(dim),
                 "X-Goog-Upload-Header-Content-Type": mime,
                 "Content-Type": "application/json"})
    with urllib.request.urlopen(cerere, timeout=120) as r:
        url = r.headers.get("x-goog-upload-url")
    if not url:
        sys.exit("Nu am primit URL-ul de upload (verifica cheia).")
    cerere2 = urllib.request.Request(
        url, data=open(cale, "rb").read(), method="POST",
        headers={"Content-Length": str(dim),
                 "X-Goog-Upload-Offset": "0",
                 "X-Goog-Upload-Command": "upload, finalize",
                 "Content-Type": mime})
    with urllib.request.urlopen(cerere2, timeout=1800) as r:
        info = json.load(r)
    uri = info.get("file", {}).get("uri")
    nume = info.get("file", {}).get("name")
    print(f"   incarcat: {uri}")
    # asteptam procesarea
    for i in range(60):
        cerere3 = urllib.request.Request(
            f"https://generativelanguage.googleapis.com/v1beta/{nume}",
            headers={"x-goog-api-key": cheie})
        with urllib.request.urlopen(cerere3, timeout=60) as r:
            st = json.load(r).get("state", "")
        if st == "ACTIVE":
            break
        if st == "FAILED":
            sys.exit("Google a esuat la procesarea fisierului.")
        print("   procesez...")
        time.sleep(10)
    return uri, mime


def cere(cheie, model, parts, incercari=4):
    cerere = urllib.request.Request(
        GEN.format(model=model),
        data=json.dumps({"contents": [{"parts": parts}]}).encode(),
        method="POST",
        headers={"x-goog-api-key": cheie, "Content-Type": "application/json"})
    for i in range(incercari):
        try:
            with urllib.request.urlopen(cerere, timeout=900) as r:
                d = json.load(r)
            return d["candidates"][0]["content"]["parts"][0]["text"]
        except urllib.error.HTTPError as ex:
            if ex.code in (503, 429, 500) and i < incercari - 1:
                pauza = 20 * (i + 1)
                print(f"   (model ocupat {ex.code}; astept {pauza}s si reincerc {i+2}/{incercari})")
                time.sleep(pauza)
                continue
            corp = ex.read().decode()[:400]
            raise RuntimeError(f"Eroare API {ex.code}: {corp}") from None
    raise RuntimeError("API neraspuns dupa retry")


DEFAULT_MODELE = "gemini-3.8-flash,gemini-3.5-flash,gemini-flash-latest"


def modele_din_env():
    return [m.strip() for m in os.environ.get("GEMINI_MODEL", DEFAULT_MODELE).split(",") if m.strip()]


def cere_fallback(cheie, parts):
    """Incearca modelele in ordine (GEMINI_MODEL poate fi lista cu virgule).
    Daca unul e aglomerat (503) sau depaseste cota, trece automat la urmatorul."""
    modele = modele_din_env()
    per = 4 if len(modele) == 1 else 2
    ultima = None
    for model in modele:
        try:
            return model, cere(cheie, model, parts, incercari=per)
        except Exception as ex:
            print(f"   ! {model} n-a raspuns ({str(ex)[:70]})")
            ultima = ex
    raise ultima if ultima else RuntimeError("Niciun model configurat")


def prompt_complet():
    creier = ""
    p = os.path.join(BASE, "cunoastere", "canal.md")
    if os.path.exists(p):
        creier = open(p, encoding="utf-8").read()[:2500] + "\n\n"
    p2 = os.path.join(BASE, "cunoastere", "reguli.md")
    if os.path.exists(p2):
        creier += "REGULI INVATATE DE LA CREATOR:\n" + open(p2, encoding="utf-8").read()[:1200] + "\n\n"
    return (creier +
        "Esti PAL, editorul AI al canalului PokeCity (iZentric, Minecraft+Pokemon RO, copii 8-15 (public general, non-MFK)). "
        "VIDEAZA INTREGUL material (audio + imagine) si scrie o analiza completa in romana, in felul urmator:\n\n"
        "# ANALIZA COMPLETA\n"
        "## 1. DESPRE CE E VORBA (5 randuri)\n"
        "## 2. CE SE VEDE IN JOC (evenimentele mari, cu minute: prinderi, lupte, caderi, raiduri)\n"
        "## 3. CE SE SPUNE (rezumat pe sectiuni cu minute)\n"
        "## 4. TOP MOMENTE PENTRU EPISOADE (3-8 bucati; pentru fiecare: minut start, minut explozie, "
        "CE SE VEDE + CE SE SPUNE acolo, scor 0-10 pentru copii 8-15 (public general, non-MFK), si daca are MOTIV de exista fata de celelalte)\n"
        "## 5. TITLURI (pentru fiecare moment de sus: max 60 chars, promit doar ce se vede)\n"
        "## 6. RISCURI (limbaj/gesturi de verificat inainte de upload, cu minute exacte)\n"
        "Fii CONCRET cu minutele (ex: 1:08). Nu inventa nimic ce nu apare in material.")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    sursa = sys.argv[1]
    cheie = citeste_cheie()
    prompt = prompt_complet()

    if sursa.startswith("http"):
        print("Sursa: link YouTube (Gemini il vizioneaza direct)")
        parts = [{"text": prompt + "\n\nVIDEO: " + sursa}]
    else:
        if not os.path.exists(sursa):
            sys.exit(f"Nu gasesc fisierul {sursa}")
        uri, mime = upload_fisier(cheie, os.path.abspath(sursa))
        parts = [{"file_data": {"mime_type": mime, "file_uri": uri}},
                 {"text": prompt}]

    print(f"2/3 Gemini ({model}) vizioneaza TOT... (poate dura 1-5 min pentru ore de material)")
    try:
        model, text = cere_fallback(cheie, parts)
    except urllib.error.HTTPError as ex:
        corp = ""
        if hasattr(ex, "read"):
            try:
                corp = ex.read().decode()[:300]
            except Exception:
                pass
        sys.exit(f"Eroare API {ex.code}: {corp}")

    dosar = os.path.join(BASE, "cunoastere", "analize")
    os.makedirs(dosar, exist_ok=True)
    cale = os.path.join(dosar, "ANALIZA_" + time.strftime("%Y-%m-%d_%H%M") + ".md")
    open(cale, "w", encoding="utf-8").write(
        "# Analiza PRIVESTE — " + sursa + "\n\n" + text + "\n")
    print(f"3/3 SALVAT: {cale}\n")
    print(text[:3000])


if __name__ == "__main__":
    main()
