#!/usr/bin/env python3
r"""
PAL TELEGRAM — AI-ul canalului in telefonul tau, oriunde esti.

CE POȚI ÎNTREBA DE PE TELEFON (chat normal):
  „ce momente are live-ul de aseara?"
  „vreau clip cu caderea din casuta"
  „randeaza momentele din momente.txt"
  „ce facusem azi dimineata?"

SETARE (o data, 3 minute):
  1. Telegram -> cauti @BotFather -> /newbot -> nume (ex: PAL PokeCity)
  2. BotFather iti da un TOKEN (de tip 123456:ABC-DEF...) -> il pui in autoeditor/.env:
       TELEGRAM_TOKEN=...
       TELEGRAM_USER_ID=...
  3. Pentru TELEGRAM_USER_ID: scrii lui @userinfobot pe Telegram -> iti da ID-ul tau
     (botul raspunde NUMAI tie — nimeni altcineva nu-l poate comanda)
  4. Rulezi pe PC (unde sunt live-urile):   python pal_telegram.py
  5. De pe telefon: deschizi chatul cu botul tau -> vorbesti.

COMENZI suplimentare (optional):
  /momente            -> analizeaza ultimul live din prindere/ si iti arata top momente
  /randeaza           -> porneste randarea cu momente.txt (in fundal, pe PC-ul tau)
  /status             -> ce face randarea chiar acum
"""
import json
import os
import subprocess
import sys
import time
import urllib.parse
import urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import autoeditor as ae
import pal  # chatul text + contextul, din acelasi creier

API = "https://api.telegram.org/bot{tok}/{meth}"


def env():
    e = {}
    p = os.path.join(BASE, ".env")
    if os.path.exists(p):
        for lin in open(p, encoding="utf-8"):
            if "=" in lin and not lin.strip().startswith("#"):
                k, v = lin.strip().split("=", 1)
                e[k] = v
    for k in ("TELEGRAM_TOKEN", "TELEGRAM_USER_ID"):
        if os.environ.get(k):
            e[k] = os.environ[k]
    return e


def tg(tok, meth, payload=None):
    url = API.format(tok=tok, meth=meth)
    if payload is None:
        with urllib.request.urlopen(url, timeout=70) as r:
            return json.load(r)
    data = urllib.parse.urlencode(payload).encode()
    with urllib.request.urlopen(url, data=data, timeout=70) as r:
        return json.load(r)


def trimite(tok, chat, text):
    """Mesaje pana la 4096 chars; taiem pe randuri daca e mai lung."""
    while text:
        bucata, rest = text[:3900], text[3900:]
        if rest:
            cut = bucata.rfind("\n")
            if cut > 1000:
                bucata, rest = bucata[:cut], bucata[cut:] + rest
        tg(tok, "sendMessage", {"chat_id": chat, "text": bucata})
        text = rest


def gaseste_live():
    """Ultimul live gasit: prindere/ sau primul .mp4 din folderul autoeditor."""
    dosar = os.path.join(BASE, "prindere")
    if os.path.isdir(dosar):
        fisiere = [f for f in os.listdir(dosar) if f.lower().endswith((".mp4", ".mkv"))]
        if fisiere:
            return os.path.join(dosar, max(fisiere, key=lambda f: os.path.getmtime(os.path.join(dosar, f))))
    return None


def context_live(video, cache={}):
    """Momentelor+scoruri le tine minte per fisier (nu re-analizeaza la fiecare mesaj)."""
    if video in cache:
        return cache[video]
    ff = ae.gaseste_ffmpeg()
    context, nr, durata = pal.construieste_context(ff, video)
    cache[video] = context
    return context


def main():
    e = env()
    tok, user_id = e.get("TELEGRAM_TOKEN"), e.get("TELEGRAM_USER_ID")
    if not tok or not user_id:
        print("LIPSESTE setarea: TELEGRAM_TOKEN si TELEGRAM_USER_ID in autoeditor/.env")
        print("  1. @BotFather -> /newbot -> token")
        print("  2. @userinfobot -> ID-ul tau")
        sys.exit(1)
    user_id = str(user_id)
    print("PAL TELEGRAM pornit. Lasă fereastra deschisa; comenzi din telefon.")
    offset = 0
    while True:
        try:
            upd = tg(tok, "getUpdates", {"offset": offset + 1, "timeout": 60})
            for u in upd.get("result", []):
                offset = u["update_id"]
                msg = u.get("message") or {}
                chat = str((msg.get("chat") or {}).get("id", ""))
                if chat != user_id:                      # doar stapanul
                    trimite(tok, chat, "Nu sunt botul tau. 🙂")
                    continue
                text = (msg.get("text") or "").strip()
                if not text:
                    continue
                print("TG:", text[:80])
                if text.startswith("/momente"):
                    video = gaseste_live()
                    if not video:
                        trimite(tok, chat, "Nu gasesc niciun live in prindere/. Pune fisierul acolo.")
                        continue
                    trimite(tok, chat, "Ascult live-ul... (1-2 min)")
                    ctx = context_live(video)
                    trimite(tok, chat, "MOMENTELE:\n" + ctx)
                elif text.startswith("/randeaza"):
                    video = gaseste_live()
                    if not video:
                        trimite(tok, chat, "Niciun live in prindere/.")
                        continue
                    cmd = [sys.executable, os.path.join(BASE, "autoeditor.py"), video,
                           "--subtitrari", "--ai"]
                    subprocess.Popen(cmd, cwd=BASE)
                    trimite(tok, chat, "Randarea a PORNIT pe PC (fundal). Scrie /status cand vrei stadiul.")
                elif text.startswith("/status"):
                    logp = os.path.join(BASE, "episodes", "RAPORT.md")
                    if os.path.exists(logp):
                        coada = " ".join(open(logp, encoding="utf-8").read().split()[-120:])
                        trimite(tok, chat, "ULTIMUL RAPORT (coada):\n" + coada)
                    else:
                        trimite(tok, chat, "Inca nimic randat din ultima pornire.")
                else:
                    video = gaseste_live()
                    ctx = context_live(video) if video else "(niciun live disponibil acum)"
                    k = ae.citeste_cheie_gemini(BASE)
                    if not k:
                        trimite(tok, chat, "Lipseste GEMINI_API_KEY din .env (aistudio.google.com/apikey).")
                        continue
                    prompt = (
                        "Esti PAL, AI-ul canalului PokeCity (iZentric, Minecraft+Pokemon RO, copii 6-13). "
                        "Vorbesti romaneste, scurt, ca un prieten de gaming.\n\n"
                        "MOMENTELE DIN ULTIMUL LIVE:\n" + ctx + "\n\n"
                        "Ce a scris creatorul din telefon: \"" + text + "\"\n\n"
                        "Raspunde-i util (2-6 fraze): recomanda momente concrete cu minute daca cere "
                        "un tip de clip; daca cere altceva (idei titluri, ce sa faca maine), ajuta-l "
                        "dupa regulile canalului: doar clipuri cu motiv, titluri care promit doar ce "
                        "e in material, CTA LIKE+comentarii.")
                    try:
                        trimite(tok, chat, pal.intrebare_gemini(k, prompt))
                    except Exception as ex:
                        trimite(tok, chat, f"(eroare la Google: {str(ex)[:80]})")
        except Exception as ex:
            print("ciclu:", str(ex)[:100])
            time.sleep(5)


if __name__ == "__main__":
    main()
