# PIPELINE GITHUB ACTIONS: sursa (Studio SAU Drive SAU pixeldrain SAU fisier direct) -> episoade 2K -> Release
import os, sys, subprocess

URL = sys.argv[1] if len(sys.argv) > 1 else ""
MAXN = sys.argv[2] if len(sys.argv) > 2 else "2"
if not URL:
    print("Release de episoade (ep-*) - nimic de procesat", flush=True)
    sys.exit(0)

def sh(cmd, env=None):
    print(">>", " ".join(cmd[:6]), "...", flush=True)
    r = subprocess.run(cmd, env=env)
    if r.returncode != 0:
        sys.exit(f"!! A PICAT: {' '.join(cmd[:4])}")

def merge_video_audio():
    v, a = "live_curent.f299.mp4", "live_curent.f140.m4a"
    if os.path.exists(v) and os.path.exists(a) and not os.path.exists("live_curent.mp4"):
        subprocess.run(["ffmpeg", "-y", "-i", v, "-i", a, "-c", "copy", "-shortest",
                        "live_curent.mp4"], check=True)

def sursa_gata():
    if os.path.exists("live_curent.mp4") and os.path.getsize("live_curent.mp4") > 50_000_000:
        print("SURSA:", os.path.getsize("live_curent.mp4") // (1024 * 1024), "MB", flush=True)
        return True
    return False

# ── 1a) YOUTUBE: cookies + token de download extras AUTOMAT din pagina Studio ──
import re
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
yt = ("youtube.com" in URL or "youtu.be" in URL or "download_my_video" in URL)
if yt and os.path.exists("cookies.txt") and "SAPISID" in open("cookies.txt").read():
    dl = URL
    if "download_my_video" not in URL:  # orice link/id YouTube -> scoatem tokenul noi insine
        vid = (URL.split("v=")[1].split("&")[0] if "v=" in URL
               else URL.rstrip("/").split("/")[-1])
        print(f">> extragem token de download din Studio pt {vid}...", flush=True)
        sh(["curl", "-sS", "-L", "-b", "cookies.txt", "-A", UA,
            "-o", "studio_page.html", f"https://studio.youtube.com/video/{vid}/edit"])
        pg = open("studio_page.html", encoding="utf-8", errors="ignore").read()
        m = re.search(r'download_my_video\?v=([A-Za-z0-9_-]+)(?:\\u0026|&)t=([A-Za-z0-9_-]+)', pg)
        if not m:
            sys.exit("!! Studio nu ne-a dat token -> cookies expirate: re-exporta si re-pune Secret COOKIES_YT")
        dl = f"https://www.youtube.com/download_my_video?v={m.group(1)}&t={m.group(2)}"
        print("   token extras OK (automat)", flush=True)
    print(">> descarcare oficiala din Studio...", flush=True)
    sh(["curl", "-sS", "-L", "-b", "cookies.txt", "-A", UA, "-o", "live_curent.mp4", dl])
    cap = open("live_curent.mp4", "rb").read(300) if os.path.exists("live_curent.mp4") else b""
    if cap.startswith(b"<"):
        sys.exit("!! Studio a trimis pagina de login -> cookies expirate: re-exporta si re-pune COOKIES_YT")
    print("STUDIO OK:", os.path.getsize("live_curent.mp4") // (1024 * 1024), "MB", flush=True)
    studio_ok = True

# ── 1b) GOOGLE DRIVE (calitate originala, zero blocari) ──
elif "drive.google.com" in URL or "docs.google.com" in URL:
    print(">> sursa: Google Drive", flush=True)
    sh([sys.executable, "-m", "pip", "install", "-q", "gdown"])
    if "/d/" in URL:
        fid = URL.split("/d/")[1].split("/")[0]
    elif "id=" in URL:
        fid = URL.split("id=")[1].split("&")[0]
    else:
        sys.exit("!! link Drive fara id")
    sh([sys.executable, "-m", "gdown", "--fuzzy",
        f"https://drive.google.com/uc?id={fid}", "-O", "live_curent.mp4"])
    if not sursa_gata():
        sys.exit("!! download Drive a esuat (verifica 'Anyone with the link')")

# ── 1c) PIXELDRAIN (drag&drop fara cont) ──
elif "pixeldrain.com" in URL:
    print(">> sursa: pixeldrain", flush=True)
    fid = URL.rstrip("/").split("/u/")[1].split("/")[0] if "/u/" in URL else URL.rstrip("/").split("/")[-1]
    sh(["curl", "-L", "-o", "live_curent.mp4", f"https://pixeldrain.com/api/file/{fid}?download"])
    if not sursa_gata():
        sys.exit("!! download pixeldrain a esuat")

# ── 1d) FISIER DIRECT (release GitHub = drag&drop in browser, sau orice link .mp4) ──
elif ("/releases/" in URL and "github" in URL) or URL.lower().split("?")[0].endswith(
        (".mp4", ".mkv", ".mov", ".avi", ".webm", ".ts", ".flv", ".m4v")):
    print(">> sursa: fisier direct (release/upload)", flush=True)
    cmd = (["curl", "-sS", "-L", "-H", f"Authorization: Bearer {os.environ['ASSET_TOKEN']}",
            "-H", "Accept: application/octet-stream", "-o", "live_curent.mp4", URL]
           if os.environ.get("ASSET_TOKEN") else
           ["curl", "-sS", "-L", "-o", "live_curent.mp4", URL])
    sh(cmd)
    if not sursa_gata():
        sys.exit("!! download fisier a esuat sau fisier prea mic")

# ── 1e) YOUTUBE clasic: strategii (riscanta pe servere; caz ca totusi merge) ──
else:
    strategii = []
    if os.path.exists("cookies.txt"):
        strategii += [["--cookies", "cookies.txt", "--extractor-args", "youtube:player_client=web_safari"],
                      ["--cookies", "cookies.txt", "--extractor-args", "youtube:player_client=mweb"],
                      ["--cookies", "cookies.txt"]]
    strategii += [["--extractor-args", "youtube:player_client=android_vr"], []]
    gata = False
    for s in strategii:
        cmd = [sys.executable, "-m", "yt_dlp", "--merge-output-format", "mp4",
               "--concurrent-fragments", "8", "-o", "live_curent.%(ext)s", "--no-playlist"] + s + \
              ["-f", "299+140/312+140/best[height<=1080][vcodec^=avc1]+bestaudio", URL]
        print(">> strategie descarcare:", " ".join(s) or "default", flush=True)
        if subprocess.run(cmd).returncode == 0 and sursa_gata():
            gata = True
            break
        print("   strategie picata, incerc urmatoarea...", flush=True)
    if not gata:
        sys.exit("!! descarcarea YouTube a picat -> foloseste link Studio download_my_video, Drive sau pixeldrain")
    merge_video_audio()

if not sursa_gata():
    sys.exit("!! nicio sursa disponibila")

# ── 2) RANDARE (runner 7GB) + poarta STRICTA: doar ce chiar merita ──
env = dict(os.environ, PYTHONUNBUFFERED="1", AE_POARTA=os.environ.get("AE_POARTA", "0.6"))
cmd = [sys.executable, "autoeditor.py", "live_curent.mp4", "--calitate", "1080p", "--max", MAXN]
if os.environ.get("SUBTITRARI", "0") == "1":   # whisper pe live 2h = ~10 min; default OFF pt viteza
    cmd += ["--subtitrari"]
sh(cmd, env=env)

# ── 3) URCARE 2K (2560x1440 lanczos+unsharp) ──
sh([sys.executable, "urca_2k.py"])
print("PIPELINE GITHUB GATA", flush=True)
