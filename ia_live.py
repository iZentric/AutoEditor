#!/usr/bin/env python3
r"""
IA LIVE — capteaza live-ul tau DIRECT, la rezolutia lui nativa (fara re-encodare YouTube).

CE REZOLVA:
  - ai live 2K in OBS? -> capteaza 2560x1440 nativ, ZERO pierderi de calitate
  - nu mai depinzi de yt-dlp / VOD descarcabil / limite YouTube
  - poate CURSA cu live-ul (inregistreaza in timp real, fara sa-l intrerupa)

CUM FOLOSESTI (2 metode):

METODA 1 — FACECAM (recomandat, 2 minute):
  1. In OBS: Settings -> Stream -> Custom -> Server:
     rtmp://localhost/live    Key: pokecity
  2. Adaugi sursa "Media Source" in OBS care arata spre:
     autoeditor/prindere/live_full.mp4
  3. Rulezi:  python ia_live.py
  4. Faci live normal. La final: Ctrl+C aici si ai fisierul complet.

METODA 2 — daca OBS nu duce rtmp://localhost (daca OBS nu duce rtmp://localhost):
  pornesti cu server extern (nginx-rtmp) — vezi README, sectiunea "Acces direct".

DUPA CAPTURA:
  python autoeditor.py prindere/live_full.mp4 --calitate nativ --subtitrari --ai
  (calitatea "nativ" pastreaza exact rezolutia capturii — 2K-ul tau, near-os)
"""
import os
import signal
import subprocess
import sys
import time

BASE = os.path.dirname(os.path.abspath(__file__))
DOSAR = os.path.join(BASE, "prindere")
os.makedirs(DOSAR, exist_ok=True)

SERVER = os.environ.get("LIVE_SERVER", "rtmp://0.0.0.0:1935/live")
CHEIE = os.environ.get("LIVE_KEY", "pokecity")


def gaseste_ffmpeg():
    import shutil
    p = shutil.which("ffmpeg")
    if p:
        return p
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        sys.exit("NU GASESC ffmpeg. Windows: winget install ffmpeg")


def main():
    ff = gaseste_ffmpeg()
    iesire = os.path.join(DOSAR, "live_full.mp4")
    print("=" * 60)
    print("IA LIVE — captura directa, rezolutie NATIVA (fara re-encodare)")
    print("=" * 60)
    print(f"  server : {SERVER}   (cheie: {CHEIE})")
    print(f"  fisier : {iesire}")
    print()
    print("  In OBS:")
    print("    Settings -> Stream -> Custom ->")
    print(f"      Server: rtmp://localhost/live      Key: {CHEIE}")
    print("    Settings -> Output -> Rescale OFF (lasa 2K-ul tau!)")
    print()
    print("  Porneste live-ul cand esti gata. STOP AICI cu Ctrl+C la final.")
    print()

    # copyts + copycodec: recording-ul e exact ce trimite OBS (bit pentru bit)
    cmd = [ff, "-y",
           "-listen", "1", "-timeout", "0",          # asteapta OBS-ul sa se conecteze
           "-i", f"{SERVER}/{CHEIE}",
           "-c", "copy",                              # ZERO re-encodare = ZERO pierdere
           "-copyts",
           iesire]
    proc = subprocess.Popen(cmd, stderr=subprocess.PIPE, text=True)
    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.send_signal(signal.SIGINT)
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
    if os.path.exists(iesire) and os.path.getsize(iesire) > 1000:
        mb = os.path.getsize(iesire) / 1e6
        print(f"\nGATA: live capturat complet ({mb:.0f} MB) -> {iesire}")
        print("PASUL URMATOR:")
        print(f"  python autoeditor.py prindere/live_full.mp4 --subtitrari --ai")
    else:
        print("\nNimic capturat. Verifica: OBS Settings -> Stream (server+key de mai sus).")


if __name__ == "__main__":
    main()
