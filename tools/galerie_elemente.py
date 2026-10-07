#!/usr/bin/env python3
"""Face o pagină HTML cu toate elementele tăiate EXACT, grupate per thumbnail.

Bossul vede, agentul nu are ochi. Pagina arată fiecare element pe fundal de
șah (transparentul se vede), lângă sursa din care a fost tăiat.

Folosire:
    python3 tools/galerie_elemente.py --elemente elemente_brand/JH/EXACT \
        --surse refs/surse_jh --out /home/user/preview/exact.html \
        --copiaza /home/user/preview/EXACT
"""
import argparse
import csv
import os
import shutil


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--elemente", default="elemente_brand/JH/EXACT")
    ap.add_argument("--surse", default="refs/surse_jh")
    ap.add_argument("--out", default="/home/user/preview/exact.html")
    ap.add_argument("--copiaza", default=None, help="unde copiază imaginile (pt. server)")
    args = ap.parse_args()

    raport = os.path.join(args.elemente, "RAPORT.csv")
    if not os.path.exists(raport):
        raise SystemExit(f"lipsește {raport} — rulează întâi tools/taie_exact.py")
    with open(raport, newline="", encoding="utf-8") as f:
        randuri = list(csv.DictReader(f))

    baza_web = os.path.basename((args.copiaza or args.elemente).rstrip("/"))
    if args.copiaza:
        os.makedirs(args.copiaza, exist_ok=True)
        for r in randuri:
            s = os.path.join(args.elemente, r["fisier"])
            d = os.path.join(args.copiaza, r["fisier"])
            if os.path.exists(s):
                os.makedirs(os.path.dirname(d), exist_ok=True)
                shutil.copy2(s, d)
        surse_web = "surse_jh"
        os.makedirs(os.path.join(os.path.dirname(args.out), surse_web), exist_ok=True)
        for f in os.listdir(args.surse):
            if f.endswith(".jpg"):
                shutil.copy2(os.path.join(args.surse, f),
                             os.path.join(os.path.dirname(args.out), surse_web, f))
    else:
        surse_web = args.surse

    grupe = {}
    for r in randuri:
        sursa = r["sursa"]
        grupe.setdefault(sursa, []).append(r)

    piese = []
    piese.append("""<!DOCTYPE html><html lang="ro"><head><meta charset="utf-8">
<title>Elemente EXACT de la JocuriHorrorSky</title><style>
 body{background:#111;color:#eee;font-family:system-ui;margin:0;padding:18px}
 h1{font-size:21px;margin:0 0 6px}
 p{color:#aaa;font-size:13.5px;margin:0 0 18px;line-height:1.55}
 .grup{background:#1b1b1b;border:1px solid #333;border-radius:12px;padding:14px;margin-bottom:22px}
 .grup h2{font-size:15px;margin:0 0 4px;color:#ff5a5f}
 .sursa{max-width:420px;border-radius:8px;display:block;margin:8px 0 12px;border:1px solid #444}
 .el{display:inline-block;vertical-align:top;margin:6px;text-align:center;width:230px}
 .cutie{background:#333 url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16"><rect width="8" height="8" fill="%232a2a2a"/><rect x="8" y="8" width="8" height="8" fill="%232a2a2a"/></svg>');
   border:1px solid #555;border-radius:6px;padding:6px;height:150px;display:flex;align-items:center;justify-content:center}
 .cutie img{max-width:100%;max-height:140px;display:block}
 .nume{font:11.5px monospace;color:#9a9a9a;margin-top:5px;word-break:break-all}
 .stare{font:11px monospace;font-weight:bold}
 .ok{color:#00e676}.ver{color:#ffb300}
 .tip{font:11px monospace;color:#7ab7ff}
 a{color:#7ab7ff}
</style></head><body>
<h1>Elemente tăiate EXACT din thumbnailurile lui Jocuri Horror</h1>
<p>Fiecare element e tăiat <b>ÎNTREG</b> (cu contur și codiță cu tot) din sursa originală,
cu fundalul scos (pătrățelele = transparent). <b>Pixelii sunt cei din poza lui</b> —
nimic refăcut, nimic generat. Sursa e 1280×720, adică maximul pe care YouTube îl servește
pentru clipurile astea (am încercat și 1920×1080: nu există).<br>
Verde = întreg · Galben = verifică (posibil tăiat sau lipit de altceva).</p>""")

    for sursa, els in sorted(grupe.items()):
        nume_sursa = os.path.splitext(sursa)[0]
        piese.append(f'<div class="grup"><h2>{nume_sursa}</h2>')
        cale_sursa = f"{surse_web}/{sursa}"
        if os.path.exists(os.path.join(os.path.dirname(args.out), cale_sursa)):
            piese.append(f'<img class="sursa" src="{cale_sursa}" alt="sursa">')
        for r in els:
            img = f"{baza_web}/{r['fisier']}"
            cls = "ok" if r["stare"] == "COMPLET" else "ver"
            piese.append(
                f'<div class="el"><div class="cutie"><img src="{img}" alt=""></div>'
                f'<div class="nume">{os.path.basename(r["fisier"])}</div>'
                f'<div class="tip">{r["tip"]} · {r["marime"]}</div>'
                f'<div class="stare {cls}">{r["stare"]}</div></div>')
        piese.append("</div>")

    piese.append("</body></html>")
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write("".join(piese))
    print(f"scris {args.out} — {len(randuri)} elemente în {len(grupe)} grupe")


if __name__ == "__main__":
    main()
