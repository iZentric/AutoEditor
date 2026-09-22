#!/usr/bin/env python3
r"""
PAL — prietenul-tău AI (in chat, cu VOCEa canalului in cap).
Vorbesti cu el inainte de randare: ii zici ce clip vrei, cauta in live,
iti arata momentele, construieste comanda, chiar lanseaza randarea.

COMENZI (in chat, in limba ta):
  „vreau clip cu cazatura din casuta"     -> cauta in transcriptul live-ului
  „aratami momentele"                     -> top momente cu scoruri
  „fa clipul"                             -> construieste + lanseaza randarea
  „sterge"-ul din urma"                   -> (vise, inca nu :) )

Rulezi:  python pal.py prindere/live_full.mp4
"""
import json
import os
import re
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

# refolosim creierul autoeditorului (aceleasi functii, zero duplicat)
import autoeditor as ae


def cheie():
    k = ae.citeste_cheie_gemini(BASE)
    if not k:
        print("PAL are nevoie de cheia Gemini (gratis): aistudio.google.com/apikey")
        print("-> pune GEMINI_API_KEY=... in autoeditor/.env si reruleaza")
        sys.exit(1)
    return k


def intrebare_gemini(k, prompt):
    """Apel simplu text->text (fara cadre)."""
    body = json.dumps({"contents": [{"parts": [{"text": prompt}]}],
                       "generationConfig": {"temperature": 0.5}}).encode()
    import urllib.request
    req = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{os.environ.get('GEMINI_MODEL', 'gemini-3.8-flash')}:generateContent",
        data=body, method="POST",
        headers={"Content-Type": "application/json", "x-goog-api-key": k})
    with urllib.request.urlopen(req, timeout=90) as r:
        d = json.load(r)
    return d["candidates"][0]["content"]["parts"][0]["text"].strip()


def construieste_context(ff, video):
    """Analizeaza live-ul o singura data -> (context_pt_AI, nr_momente, durata)."""
    seria = ae.analiza_audio(ff, video)
    varfuri, scor = ae.detecteaza_explozii(seria)
    tr = ae.transcrie_live(video) or []
    live_len = seria[-1][0]
    linii = []
    for sec, s in sorted(varfuri, key=lambda x: -x[1])[:12]:
        txt = " ".join(t for a, b, t in tr if sec - 20 <= a <= sec + 15)[:120] if tr else "(fara transcript)"
        linii.append(f"  minut {sec//60}:{sec%60:02d} · scor {s:.0f} · zici: \"{txt}\"")
    context = "\n".join(linii) if linii else "  (niciun moment tare detectat)"
    return context, len(varfuri), live_len


def main():
    if len(sys.argv) < 2:
        print("folosire: python pal.py LIVE.mp4")
        sys.exit(1)
    video = os.path.abspath(sys.argv[1])
    if not os.path.exists(video):
        sys.exit(f"nu gasesc {video}")
    k = cheie()

    print("Analizez live-ul o data (urechile + transcriptul)...")
    ff = ae.gaseste_ffmpeg()
    context, nr_momente, live_len = construieste_context(ff, video)
    print(f"Gata: {nr_momente} momente in {live_len//60} min. Vorbeste cu mine ('iesi' ca sa pleci).\n")

    istoric = []
    while True:
        try:
            cerere = input("TU: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nPAL: Pa!")
            break
        if not cerere:
            continue
        if cerere.lower() in ("iesi", "exit", "quit"):
            print("PAL: Pa! Succes la upload!")
            break
        istoric.append(f"TU: {cerere}")
        ultime = "\n".join(istoric[-6:])
        prompt = (
            "Esti PAL, prietenul AI al creatorului PokeCity (iZentric: Minecraft+Pokemon RO, copii 8-15 (public general)). "
            "Vorbesti romaneste, pe scurt, ca un prieten de gaming.\n\n"
            "MOMENTELE DIN LIVE (minute: scor, ce zice):\n" + context + "\n\n"
            "CONVERSATIA PANA ACUM:\n" + ultime + "\n\n"
            "Raspunde-i ca PAL (2-6 fraze). Daca vrea un anumit tip de clip, recomanda momente "
            "CONCRETE cu minutele. Daca cere ceva ce nu e in live, spune sincer + ce e cea mai "
            "buna alternativa. Daca e decizia luata, da-i comanda exacta:")
        try:
            rasp = intrebare_gemini(k, prompt)
            print(f"\nPAL: {rasp}\n")
            istoric.append(f"PAL: {rasp}")
        except Exception as ex:
            print(f"\nPAL: (ceva nu-a mers la Google: {str(ex)[:80]}) mai incerci?")


if __name__ == "__main__":
    main()
