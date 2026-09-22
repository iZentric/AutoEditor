# RAPID v1: URL live -> episoade 2K in episodes/ intr-un singur lanț (fara reluari)
import os, sys, subprocess, glob

URL = sys.argv[1]
MAXN = sys.argv[2] if len(sys.argv) > 2 else "8"

def sh(cmd, env=None):
    print(">>", " ".join(cmd), flush=True)
    r = subprocess.run(cmd, env=env)
    if r.returncode != 0:
        print("!! A PICAT:", " ".join(cmd[:3]), flush=True)
        sys.exit(1)

# 1) DESCARCARE 1080p60 H.264 + audio (fragmente paralele = x4 viteza)
sh([sys.executable, "-m", "yt_dlp", "-f", "299+140/312+140/best[height<=1080][vcodec^=avc1]+bestaudio",
    "--merge-output-format", "mp4", "--concurrent-fragments", "8",
    "-o", "liveuri/live_curent.%(ext)s", "--no-playlist", URL])
surse = sorted(glob.glob("liveuri/live_curent.*mp4"))
if not surse:
    print("!! niciun fisier descărcat", flush=True); sys.exit(1)
src = surse[0]
print("SURSA:", src, os.path.getsize(src) // (1024*1024), "MB", flush=True)

# 2) RANDARE 1080p30 (calea PROBATĂ pe 2GB RAM; 2K direct pica)
env = dict(os.environ, AE_USOR="1", PYTHONUNBUFFERED="1")
sh([sys.executable, "autoeditor.py", src, "--calitate", "1080p", "--max", MAXN,
    "--subtitrari", "--ai"], env=env)

# 3) URCARE la 2K lanczos+unsharp (treapta a doua, graf simplu = fiabil)
sh([sys.executable, "urca_2k.py"])
print("LANT COMPLET GATA", flush=True)
