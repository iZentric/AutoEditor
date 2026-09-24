# Denumire PUBLICA: EP01.mp4 -> numele din TITLU (fara "Ep. N" — userul nu vrea EP in nume).
# Rulat din workflow inainte de publicarea finala; upload.ttl/miniaturi/srt primesc aceeasi baza.
import glob
import os
import re

from upload_release import slug_nume

folosite = set()
for txt in sorted(glob.glob("episodes/*_upload.txt")):
    titlu = ""
    for linie in open(txt, encoding="utf-8"):
        if linie.startswith("TITLU:"):
            titlu = linie.split(":", 1)[1].strip()
            break
    baza_v = re.sub(r"_upload\.txt$", "", os.path.basename(txt))
    nr = int(re.sub(r"\D", "", baza_v.split("_")[-1]) or 0) if re.search(r"\d", baza_v) else None
    if not titlu:
        titlu = baza_v
    nou = slug_nume(titlu, nr=nr)
    while nou in folosite:                     # siguranta anti-coliziune
        nou = nou[:-4] + "_x" + nou[-4:]
    folosite.add(nou)
    for f in glob.glob(f"episodes/{baza_v}*"):
        ext = os.path.splitext(f)[1]
        rest = os.path.basename(f)[len(baza_v):]   # ex: "_miniatura_B.jpg" / "_upload.txt" / ".srt"
        dst = nou[:-4] + rest
        if f != dst and not os.path.exists(dst):
            os.replace(f, dst)
            print(f"   {os.path.basename(f)} -> {os.path.basename(dst)}")
print("DENUMIRE PUBLICA GATA (fisierele poarta titlurile, nu EP)")
