# PIPELINE GITHUB ACTIONS: URL live -> episoade 2K -> Release (ruleaza pe runner, nu local)
import os, sys, subprocess

URL = sys.argv[1]
MAXN = sys.argv[2] if len(sys.argv) > 2 else "2"

def sh(cmd, env=None):
    print(">>", " ".join(cmd), flush=True)
    r = subprocess.run(cmd, env=env)
    if r.returncode != 0:
        sys.exit(f"!! A PICAT: {' '.join(cmd[:4])}")

# 1) descarcare 1080p60 H.264 (runner ARE ffmpeg -> fuziunea merge nativ)
# YouTube blocheaza IP-urile de datacenter ("Sign in to confirm you're not a bot"):
#  - clientul android_vr/tv trece de obicei fara cookies
#  - daca exista cookies.txt (Secret COOKIES_YT) -> folosim cookies = garantat
strategii = []
if os.path.exists("cookies.txt"):
    strategii += [["--cookies", "cookies.txt", "--extractor-args", "youtube:player_client=web_safari"],
                  ["--cookies", "cookies.txt", "--extractor-args", "youtube:player_client=mweb"],
                  ["--cookies", "cookies.txt"]]
strategii += [["--extractor-args", "youtube:player_client=android_vr"], []]
gata = False
for s in strategii:
    cmd = [sys.executable, "-m", "yt_dlp", "--merge-output-format", "mp4",
           "--concurrent-fragments", "8", "-o", "live_curent.%(ext)s", "--no-playlist"] + s +           ["-f", "299+140/312+140/best[height<=1080][vcodec^=avc1]+bestaudio", URL]
    print(">> strategie descarcare:", " ".join(s) or "default", flush=True)
    if subprocess.run(cmd).returncode == 0:
        gata = True
        break
    print("   strategie picata, incerc urmatoarea...", flush=True)
if not gata:
    sys.exit("!! toate strategiile de descarcare au picat")
src = "live_curent.mp4"
if not os.path.exists(src):
    v, a = "live_curent.f299.mp4", "live_curent.f140.m4a"
    if os.path.exists(v) and os.path.exists(a):
        subprocess.run(["ffmpeg", "-y", "-i", v, "-i", a, "-c", "copy", "-shortest", src], check=True)
if not os.path.exists(src):
    sys.exit("!! descarcarea a esuat")
print("SURSA:", src, os.path.getsize(src) // (1024 * 1024), "MB", flush=True)

# 2) randare (runner 7GB RAM = fara AE_USOR) + poarta STRICTA: doar ce chiar merita
env = dict(os.environ, PYTHONUNBUFFERED="1", AE_POARTA=os.environ.get("AE_POARTA", "0.6"))
cmd = [sys.executable, "autoeditor.py", src, "--calitate", "1080p", "--max", MAXN]
if os.environ.get("SUBTITRARI", "0") == "1":   # whisper pe live 2h = ~10 min; default OFF pt viteza
    cmd += ["--subtitrari"]
sh(cmd, env=env)

# 3) urcare 2K (2560x1440 lanczos+unsharp)
sh([sys.executable, "urca_2k.py"])
print("PIPELINE GITHUB GATA", flush=True)
