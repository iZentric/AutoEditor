# Urca episoadele randate la 2K (2560x1440 lanczos+unsharp) — pas separat ca sa fie fiabil pe 2GB RAM
import os, subprocess, sys, glob
import imageio_ffmpeg
ff = imageio_ffmpeg.get_ffmpeg_exe()
for ep in sorted(glob.glob("episodes/EP*_*.mp4")):
    if "_2K" in ep or os.path.exists(ep.replace(".mp4", "_2K.mp4")):
        continue
    out = ep.replace(".mp4", "_2K.mp4")
    print("2K:", ep, "->", out, flush=True)
    r = subprocess.run([ff, "-y", "-i", ep, "-vf",
        "scale=2560:1440:flags=lanczos,unsharp=5:5:0.8",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-c:a", "copy", "-movflags", "+faststart", out],
        capture_output=True, text=True)
    if r.returncode == 0 and os.path.exists(out):
        os.replace(out, ep)  # inlocuim originalul cu varianta 2K
        print("   OK 2K:", ep, os.path.getsize(ep) // (1024*1024), "MB", flush=True)
    else:
        print("   EROARE:", (r.stderr or "")[-300:], flush=True)
print("GATA 2K", flush=True)
