# PIPELINE GITHUB ACTIONS: sursa -> episoade 2K -> Release
import glob, os, re, sys, subprocess, time

URL = (sys.argv[1] if len(sys.argv) > 1 else "").strip()
MAXN = sys.argv[2] if len(sys.argv) > 2 else "2"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"

def sh(cmd, env=None):
    print(">>", " ".join(cmd[:6]), "...", flush=True)
    r = subprocess.run(cmd, env=env)
    if r.returncode != 0:
        sys.exit(f"!! A PICAT: {' '.join(cmd[:4])}")

def sursa_gata():
    if os.path.exists("live_curent.mp4") and os.path.getsize("live_curent.mp4") > 50_000_000:
        print("SURSA:", os.path.getsize("live_curent.mp4") // (1024 * 1024), "MB", flush=True)
        return True
    return False

if not URL:
    print("Release de episoade (ep-*) - nimic de procesat", flush=True)
    sys.exit(0)

# ── 0) CONTEXT PT AI: titlul+canalul original al live-ului (oEmbed public, fara cookies) ──
import json as _json
_ctx = os.environ.get("CTX_URL") or (URL if re.fullmatch(r'[A-Za-z0-9_-]{11}', URL) or
                                     "youtube" in URL else "")
_m = (re.search(r'[?&]v=([A-Za-z0-9_-]{11})', _ctx) or
      re.search(r'/(?:live|shorts)/([A-Za-z0-9_-]{11})', _ctx)) if _ctx else None
_yid = (_m.group(1) if _m else (_ctx if re.fullmatch(r'[A-Za-z0-9_-]{11}', _ctx) else "")) if _ctx else ""
if _yid:
    try:
        _r = subprocess.run(["curl", "-sS", "--max-time", "30",
                             f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={_yid}&format=json"],
                            capture_output=True, text=True)
        _d = _json.loads(_r.stdout)
        open("context_sursa.txt", "w", encoding="utf-8").write(
            f"TITLU ORIGINAL: {_d.get('title','')}\nCANAL: {_d.get('author_name','')}\n")
        print("context AI: '" + _d.get('title', '')[:70] + "'", flush=True)
    except Exception as _e:
        print("context AI: n-am putut lua titlul (" + str(_e)[:40] + ") — mergem fara", flush=True)

# ── CACHE: daca fisierul e deja aici (run anterior picat dupa descarcare), nu redescarcam ──
if sursa_gata():
    print(">> sursa gasita in cache -> sarim descarcarea", flush=True)
else:
    yt = bool(re.fullmatch(r'[A-Za-z0-9_-]{11}', URL)) or any(
        d in URL for d in ("youtube.com", "youtu.be", "download_my_video"))

    # ── 1a) YOUTUBE: token de download extras AUTOMAT din pagina Studio (3 reincercari) ──
    if yt and os.path.exists("cookies.txt") and "SAPISID" in open("cookies.txt").read():
        m = (re.search(r'[?&]v=([A-Za-z0-9_-]{11})', URL) or
             re.search(r'/(?:live|shorts)/([A-Za-z0-9_-]{11})', URL))
        vid = m.group(1) if m else (URL if re.fullmatch(r'[A-Za-z0-9_-]{11}', URL)
                                    else URL.rstrip("/").split("/")[-1][:11])
        dl = None
        for incercare in range(1, 4):
            print(f">> extragem token din Studio pt {vid} (incercarea {incercare}/3)...", flush=True)
            sh(["curl", "-sS", "-L", "--max-time", "60", "-b", "cookies.txt", "-A", UA,
                "-o", "studio_page.html", f"https://studio.youtube.com/video/{vid}/edit"])
            pg = open("studio_page.html", encoding="utf-8", errors="ignore").read()
            m = re.search(r'download_my_video\?v=([A-Za-z0-9_-]+)(?:\\u0026|&)t=([A-Za-z0-9_-]+)', pg)
            if m:
                dl = f"https://www.youtube.com/download_my_video?v={m.group(1)}&t={m.group(2)}"
                print("   token extras OK (automat)", flush=True)
                break
            titlu = re.search(r'<title>([^<]{0,80})', pg)
            print(f"   nu a venit token (pagina: {titlu.group(1) if titlu else 'fara titlu'}) -> reincercam", flush=True)
            os.remove("studio_page.html")
            time.sleep(10)
        if not dl:
            sys.exit("!! Studio nu ne-a dat token dupa 3 incercari -> cookies uzate: iesi si intra in studio.youtube.com apoi re-exporta cookies in Secret COOKIES_YT")
        print(">> descarcare oficiala din Studio...", flush=True)
        sh(["curl", "-sS", "-L", "--max-time", "1800", "-b", "cookies.txt", "-A", UA,
            "-o", "live_curent.mp4", dl])
        cap = open("live_curent.mp4", "rb").read(300) if os.path.exists("live_curent.mp4") else b""
        if cap.startswith(b"<"):
            sys.exit("!! Studio a trimis pagina de login -> cookies uzate: re-exporta in Secret COOKIES_YT")
        print("STUDIO OK:", os.path.getsize("live_curent.mp4") // (1024 * 1024), "MB", flush=True)

    # ── 1b) GOOGLE DRIVE ──
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

    # ── 1c) PIXELDRAIN ──
    elif "pixeldrain.com" in URL:
        print(">> sursa: pixeldrain", flush=True)
        fid = URL.rstrip("/").split("/u/")[1].split("/")[0] if "/u/" in URL else URL.rstrip("/").split("/")[-1]
        sh(["curl", "-L", "-o", "live_curent.mp4", f"https://pixeldrain.com/api/file/{fid}?download"])
        if not sursa_gata():
            sys.exit("!! download pixeldrain a esuat")

    # ── 1d) FISIER DIRECT (release GitHub = drag&drop, sau orice link .mp4) ──
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

    # ── 1e) YOUTUBE fara cookies: strategii (riscante; ultima speranta) ──
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
            sys.exit("!! descarcarea YouTube a picat -> pune cookies proaspete in Secret COOKIES_YT (sau link pixeldrain/Drive)")
        v, a = "live_curent.f299.mp4", "live_curent.f140.m4a"
        if os.path.exists(v) and os.path.exists(a) and not os.path.exists("live_curent.mp4"):
            subprocess.run(["ffmpeg", "-y", "-i", v, "-i", a, "-c", "copy", "-shortest",
                            "live_curent.mp4"], check=True)

if not sursa_gata():
    sys.exit("!! nicio sursa disponibila")

# ── 2) RANDARE (runner 7GB) + poarta STRICTA: doar ce chiar merita ──
env = dict(os.environ, PYTHONUNBUFFERED="1", AE_POARTA=os.environ.get("AE_POARTA", "0.6"))
cmd = [sys.executable, "autoeditor.py", "live_curent.mp4", "--calitate", "1080p", "--max", MAXN]
if os.environ.get("SUBTITRARI", "0") == "1":   # whisper pe live 2h = ~10 min; default OFF pt viteza
    cmd += ["--subtitrari"]
sh(cmd, env=env)

# ── 2b) SHORTS (verticale 9:16, <60s, din varfurile maxime) ──
if os.path.exists("episodes/plan.json"):
    sh([sys.executable, "shorts.py"])

# ── 2c) UPLOAD AUTOMAT pe YouTube (doar daca exista Secretele OAuth; altfel skip) ──
if glob.glob("episodes/EP*.mp4"):
    sh([sys.executable, "-m", "pip", "install", "-q", "google-api-python-client requests"])
    r = subprocess.run([sys.executable, "auto_upload_yt.py"])
    print("(upload YT: cod", r.returncode, "- 0=publicat, skip=in asteptare)", flush=True)

# ── 3) URCARE 2K (2560x1440 lanczos+unsharp) ──
sh([sys.executable, "urca_2k.py"])
print("PIPELINE GITHUB GATA", flush=True)
