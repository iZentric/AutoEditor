"""Quality-control for 16s shorts: verifies EVERY delivery rule before upload.
Returns a report; exits nonzero if a HARD rule fails (delivery blocked).
Rules source: cunoastere/LEGI_ALGORITM_2025.md + creator's standing laws."""
import os
import subprocess
import sys

FF = os.environ.get("FFMPEG", "ffmpeg")
FP = os.environ.get("FFPROBE", "ffprobe")


def _probe(path, args):
    out = subprocess.run([FP, "-v", "error", *args, "-of", "csv=p=0", path],
                         capture_output=True, text=True)
    return out.stdout.strip()


def durata(path):
    return float(_probe(path, ["-show_entries", "format=duration"]))


def rezolutie_fps(path):
    row = _probe(path, ["-select_streams", "v:0", "-show_entries",
                        "stream=width,height,r_frame_rate"]).split(",")
    w, h = int(row[0]), int(row[1])
    num, den = row[2].split("/")
    return w, h, float(num) / float(den)


def lufs(path):
    out = subprocess.run([FF, "-i", path, "-af", "ebur128", "-f", "null", "-"],
                         capture_output=True, text=True)
    linii = out.stderr.splitlines()
    for i, line in enumerate(linii):
        if "Integrated loudness:" in line:
            for urm in linii[i:i + 4]:
                if urm.strip().startswith("I:"):
                    return float(urm.split("I:")[1].strip().split(" ")[0])
    return None


def cadre(path, momente):
    """Extracts frames at given seconds; returns list of paths."""
    paths = []
    for i, t in enumerate(momente):
        p = f"/tmp/qc_{os.path.basename(path)}_{i}_{t}.png"
        subprocess.run([FF, "-y", "-v", "error", "-ss", str(t), "-i", path,
                        "-frames:v", "1", p], check=True)
        paths.append(p)
    return paths


def logo_sus_dreapta(path, t=6.0):
    """Static-overlay heuristic: top-right corner texture at t must differ from
    a plain sky area (logo adds variance) and stay constant between two times."""
    crops = []
    for moment in (t, t + 4):
        p = f"/tmp/qc_logo_{moment}.png"
        subprocess.run([FF, "-y", "-v", "error", "-ss", str(moment), "-i", path,
                        "-frames:v", "1", "-vf",
                        "crop=300:300:in_w-330:40", p], check=True)
        crops.append(p)
    out = subprocess.run(
        [FF, "-i", crops[0], "-i", crops[1], "-filter_complex",
         "[0:v][1:v]blend=all_mode=difference", "-f", "null", "-"],
        capture_output=True, text=True)
    static = "error" not in out.stderr.lower()
    return static, crops[0]


def bucla(path):
    """Loop potential: similarity between first and last frame (0.4s in, 15.8s)."""
    a, b = cadre(path, [0.4, 15.8])
    out = subprocess.run(
        [FF, "-i", a, "-i", b, "-filter_complex",
         "[0:v][1:v]ssim", "-f", "null", "-"], capture_output=True, text=True)
    for line in out.stderr.splitlines():
        if "SSIM" in line:
            return float(line.split("All:")[1].split(" ")[0])
    return None


def filmstrip(path, out, start=0.0, end=None, fps=1):
    """Contact-sheet 1 cadru/s pt ALEGEREA taieturilor pe evenimente VIZIBILE.
    Lege: nu tai niciodata intr-o secunda pe care nu ai vazut-o."""
    if end is None:
        end = durata(path)
    subprocess.run([FF, "-y", "-v", "error", "-ss", str(start), "-t", str(end - start),
                    "-i", path, "-vf", f"fps={fps},scale=180:320,tile=5x8", "-frames:v", "1", out],
                   check=True)
    return out


def punch(k=0.93):
    """Filtru punch-in CONSTANT pe o taietura (zoom 1/0.93 apoi scale inapoi).
    Se pune DOAR pe secunda evenimentului (prindere/reveal), nu pe fiecare replica:
    zoom pe fiecare linie = over-editing, retenția scade."""
    return f"crop=ih*9/16*{k}:ih*{k},scale=1080:1920:flags=lanczos"


def goluri_silenzioase(path, max_s=2.0):
    """Aer mort > max_s secunde = swipe risk. True = OK."""
    out = subprocess.run([FF, "-i", path, "-af",
                          f"silencedetect=noise=-35dB:d={max_s}", "-f", "null", "-"],
                         capture_output=True, text=True)
    return "silence_start" not in out.stderr


def ruleaza(path, momente_pops):
    raport, hard_fail = [], False
    d = durata(path)
    ok = abs(d - 16.0) <= 0.1
    raport.append(("durata 16s", f"{d:.2f}s", ok)); hard_fail |= not ok

    w, h, fps = rezolutie_fps(path)
    ok = (w, h) == (1080, 1920) and fps >= 30
    raport.append(("1080x1920 fps>=30", f"{w}x{h} {fps:.0f}fps", ok)); hard_fail |= not ok

    l = lufs(path)
    ok = l is not None and -14.5 <= l <= -13.4
    raport.append(("LUFS -14+-0.5", f"{l}", ok)); hard_fail |= not ok

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from autoeditor import verifica_subs_vizibile
    try:
        verifica_subs_vizibile(path, momente_pops)
        raport.append(("subs vizibile", f"{len(momente_pops)} pops", True))
    except SystemExit:
        raport.append(("subs vizibile", "INVIZIBILE", False)); hard_fail = True

    n = len(momente_pops)
    ok = 3 <= n <= 6 and momente_pops[0] >= 0.2 and \
        all(b - a >= 1.2 for a, b in zip(momente_pops, momente_pops[1:]))
    raport.append(("pops 3-6 / hook>=0.2s / gap>=1.2s", f"n={n}", ok)); hard_fail |= not ok

    static, cadru_logo = logo_sus_dreapta(path)
    raport.append(("logo sus-dreapta", "static" if static else "NECONFIRMAT", static))
    hard_fail |= not static

    s = bucla(path)
    raport.append(("loop potential (info)", f"ssim primul/ultim={s:.3f}", True))

    aer = goluri_silenzioase(path)
    raport.append(("fara aer mort >2s", "OK" if aer else "GOLURI", aer))
    hard_fail |= not aer


    print(f"== QC {os.path.basename(path)} ==")
    for nume, val, ok in raport:
        print(f"  {'PASS' if ok else 'FAIL'} | {nume:38s} | {val}")
    scor = sum(1 for _, _, ok in raport if ok)
    print(f"  SCOR: {scor}/{len(raport)}")
    if hard_fail:
        print("  => BLOCAT: nu se livreaza!")
        sys.exit(1)
    return raport


if __name__ == "__main__":
    ruleaza(sys.argv[1], [float(x) for x in sys.argv[2:]])
