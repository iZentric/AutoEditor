# SHORTS verticale (9:16, <60s) din varfurile cu cel mai mare scor ale live-ului
import json, os, subprocess, sys

def sh(c):
    print(">>", " ".join(c[:5]), "...", flush=True)
    subprocess.run(c, check=True)

ff = subprocess.run([sys.executable, "-c",
                     "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())"],
                    capture_output=True, text=True).stdout.strip()
plan = json.load(open("episodes/plan.json", encoding="utf-8"))
varfuri = sorted([e for e in plan if e.get("varf")], key=lambda e: -float(e.get("scor") or 0))
if not varfuri:
    print("fara varfuri in plan -> sarim shorts", flush=True)
    sys.exit(0)
alese = []
for e in varfuri:
    v = float(e["varf"])
    if v < 120:                                  # sarim primele 2 min (caldarea live-ului)
        continue
    if any(abs(v - x) < 300 for x in alese):     # minim 5 min intre shorturi
        continue
    alese.append(v)
    if len(alese) >= 12:                         # rezerva de candidati (capul final decide)
        break
if not alese:
    alese = [float(varfuri[0]["varf"])]

MAXS = (os.environ.get("MAX_SH", "auto") or "auto").strip().lower()
if MAXS in ("auto", "ai"):
    # AI-ul DECIDE cate shorturi: doar varfurile ELITA (scor >= 0.75 din maximul live-ului),
    # minim 5 min intre ele, plafon 6 — calitate peste cantitate.
    smax = max(float(e.get("scor") or 0) for e in varfuri)
    prag = 0.75 * smax
    alese = []
    for e in varfuri:
        v = float(e["varf"])
        if v < 120 or float(e.get("scor") or 0) < prag:
            continue
        if any(abs(v - x) < 300 for x in alese):
            continue
        alese.append(v)
        if len(alese) >= 6:
            break
    if not alese:
        alese = [float(varfuri[0]["varf"])]
    print(f"SHORTS: AI-ul decide -> {len(alese)} shorturi (doar scor >= {prag:.1f})", flush=True)
elif int(MAXS or 0) <= 0:
    print("MAX_SH=0 -> fara shorts (cerut explicit)", flush=True)
    sys.exit(0)
else:
    alese = alese[:int(MAXS)]

titluri = {}
try:
    for linie in open("episodes/titluri.txt", encoding="utf-8"):
        if ":" in linie:
            k, t = linie.split(":", 1)
            titluri[k.strip()] = t.strip()
except FileNotFoundError:
    pass

for i, v in enumerate(sorted(alese), 1):
    a = max(0.0, v - 25.0)
    out = f"episodes/SHORT{i:02d}.mp4"
    sh([ff, "-y", "-ss", f"{a:.1f}", "-i", "live_curent.mp4", "-t", "50",
        "-vf", "crop=ih*9/16:ih,scale=1080:1920:flags=lanczos,unsharp=5:5:0.5",
        "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", out])
    titlu = titluri.get(f"EP{i:02d}", "") or "Cel mai tare moment de pe live"
    desc = (f"{titlu}\n\nShort din live-ul complet. Episoadele intregi (2K) + miniaturile "
            f"sunt in aceeasi pagina de Releases.\n\n#shorts #gaming #romania")
    open(f"episodes/SHORT{i:02d}_upload.txt", "w", encoding="utf-8").write(
        f"TITLU: {titlu[:100]}\n\nDESCRIERE:\n{desc}\n")
    try:                      # LIVRARE PE RAND: shortul merge pe release imediat (numit dupa titlu)
        from upload_release import incarca_pe_release, slug_nume
        incarca_pe_release(out, nume=slug_nume(titlu, nr=i))
    except Exception:
        pass
    print(f"SHORT{i:02d} OK (50s vertical) + upload.txt", flush=True)
print(f"SHORTS GATA: {len(alese)} bucati", flush=True)
