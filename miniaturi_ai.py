#!/usr/bin/env python3
"""MINIATURI stil CANALE-TOP Minecraft (deconstructie Gannicus96 + lifehack-uri CTR).
Doc complet: cunoastere/REGULI_MINIATURI.md

Ideea NU este cadrul real cu sageti (v1) — aceea este doar FALLBACK.
v2 = AI recreeaza SCENA DIN CLIP (aceleasi skinuri, aceleasi obiecte — regula
creatorului: miniatura TREBUIE sa contina chestii din video principal) ca
ilustratie 3D cartoon Minecraft, cu emotie extrema, contur alb sticker,
sageata rosie, culori care lupta cu feed-ul.

Folosire:
  din cod:  from miniaturi_ai import genereaza_din_cadre, genereaza_din_video
  CLI:      python3 miniaturi_ai.py CADRU1.jpg [CADRU2.jpg ...] --titlu "..." --out mini.png --cheie KEY
            python3 miniaturi_ai.py --video EP01.mp4 --titlu "..." --out mini.png --cheie KEY
"""
import base64
import json
import os
import subprocess
import sys
import urllib.request

# Modele imagine Gemini, in ordinea incercarii (env AE_MINIATURI_MODELE le poti schimba)
MODELE = os.environ.get(
    "AE_MINIATURI_MODELE",
    "gemini-2.5-flash-image,gemini-2.5-flash-image-preview",
)

PROMPT = """You are the thumbnail artist for a top Minecraft YouTube channel for kids (style reference: Gannicus96, JocuriHorror — Romanian top creators).
You receive REAL frames from an actual clip. TASK: recreate THIS EXACT SCENE as a high-quality 3D cartoon Minecraft render (blocky pixel game look), changing ONLY the presentation:
1. SAME scene as the frames: SAME characters (identical skins, faces, outfits as in the frames), SAME creatures/objects/place (mobs, blocks, items, builds). Do NOT invent anything that is not visible in the clip.
2. Main character CLOSE-UP filling about half the frame, EXTREME emotion: huge wide eyes, mouth wide open (shock / joy / fear — whichever matches the moment in the frames).
3. The star object or creature of the moment (diamonds, chest, mob, build) BIG and bright next to the character.
4. Thick white sticker-style outline around the main character and the star object.
5. A fat glossy RED arrow with white outline pointing at the star object; if the moment is a surprise, add a big red "?!".
6. Background: bright saturated Minecraft world (vivid green grass, blue sky or the scene's own place), slightly blurred.
7. ONE dominant focal point (character OR object — character usually), everything else smaller and supporting.
8. Colors that fight the feed: strong red, yellow, electric blue, neon green. High contrast, high saturation. NO pastel, NO dull tones.
9. Widescreen 16:9, crisp at phone size. Absolutely NO added text, NO words, NO letters, NO watermark."""


def _cadre_din_fisiere(caleuri):
    cadre = []
    for c in caleuri:
        if os.path.exists(c):
            cadre.append(base64.b64encode(open(c, "rb").read()).decode())
    return cadre


def cadre_din_video(ff, video, centre_durate):
    """3 cadre REALE din clip la momentele date (secunde) -> b64."""
    cadre = []
    for centru in centre_durate:
        cale = os.path.join("/tmp", f"mini_cadru_{int(centru)}.jpg")
        subprocess.run(
            [ff, "-y", "-ss", str(max(0, centru)), "-i", video,
             "-frames:v", "1", "-vf", "scale=768:-2", "-q:v", "4", cale],
            capture_output=True)
        if os.path.exists(cale):
            cadre.append(base64.b64encode(open(cale, "rb").read()).decode())
    return cadre


def _apeleaza(cheie, model, prompt, cadre_b64):
    """REST Gemini image (aceeasi forma ca ia_gemini din autoeditor, FARA json-forţat).
    Returneaza bytes PNG sau None (motivul la stdout)."""
    parts = [{"inline_data": {"mime_type": "image/jpeg", "data": d}} for d in cadre_b64]
    parts.append({"text": prompt})
    body = json.dumps({"contents": [{"parts": parts}],
                       "generationConfig": {"temperature": 0.4}}).encode()
    req = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        data=body,
        headers={"Content-Type": "application/json", "x-goog-api-key": cheie})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            resp = json.loads(r.read().decode())
    except Exception as ex:
        print(f"   ! miniatura AI {model}: {ex}")
        return None
    for p in (resp.get("candidates") or [{}])[0].get("content", {}).get("parts", []):
        if "inlineData" in p and p["inlineData"].get("data"):
            return base64.b64decode(p["inlineData"]["data"])
        if "inline_data" in p and p["inline_data"].get("data"):
            return base64.b64decode(p["inline_data"]["data"])
    motiv = (resp.get("candidates") or [{}])[0].get("finishReason", "?")
    print(f"   ! miniatura AI {model}: fara imagine (finishReason={motiv})")
    return None


def genereaza_din_cadre(cheie, cadre_b64, out):
    """Incearca toate modelele din MODELE. Returneaza calea sau None."""
    if not cheie or not cadre_b64:
        return None
    for model in MODELE.split(","):
        img = _apeleaza(cheie, model.strip(), PROMPT, cadre_b64)
        if img:
            open(out, "wb").write(img)
            _la_1280x720(out)
            print(f"   miniatura AI GATA ({model}): {os.path.basename(out)}")
            return out
    return None


def genereaza_din_video(ff, video, centre_durate, cheie, out):
    return genereaza_din_cadre(cheie, cadre_din_video(ff, video, centre_durate), out)


def _la_1280x720(out):
    """YouTube vrea ~1280x720, <2MB."""
    try:
        from PIL import Image
        img = Image.open(out).convert("RGB")
        w, h = img.size
        tinta = 16 / 9
        if abs(w / h - tinta) > 0.01:
            if w / h > tinta:
                nw = int(h * tinta); x0 = (w - nw) // 2; img = img.crop((x0, 0, x0 + nw, h))
            else:
                nh = int(w / tinta); y0 = (h - nh) // 2; img = img.crop((0, y0, w, y0 + nh))
        img = img.resize((1280, 720), Image.LANCZOS)
        img.save(out, quality=92)
    except Exception as ex:
        print(f"   ! resize miniatura: {ex}")


if __name__ == "__main__":
    ap = sys.argv[1:]
    titlu, out, cheie, video, cadre = "MINIATURA", "miniatura_ai.png", os.environ.get("GEMINI_API_KEY"), None, []
    i = 0
    while i < len(ap):
        a = ap[i]
        if a == "--titlu":
            titlu = ap[i + 1]; i += 2
        elif a == "--out":
            out = ap[i + 1]; i += 2
        elif a == "--cheie":
            cheie = ap[i + 1]; i += 2
        elif a == "--video":
            video = ap[i + 1]; i += 2
        else:
            cadre.append(a); i += 1
    if video:
        ff = "ffmpeg"
        import shutil
        ff = shutil.which("ffmpeg") or ff
        # 3 cadre: 35% / 50% / 65% din durata
        try:
            dur = float(subprocess.run([ff, "-i", video], capture_output=True, text=True).stderr.split("Duration:")[1].split(",")[0].replace(":", ""))
        except Exception:
            dur = 170.0
        if dur > 3600:
            dur = dur / 100  # "000170.00" parse guard
        centre = [dur * 0.35, dur * 0.5, dur * 0.65]
        cale = genereaza_din_video(ff, video, centre, cheie, out)
    else:
        cale = genereaza_din_cadre(cheie, _cadre_din_fisiere(cadre), out)
    print("REZULTAT:", cale or "None -> foloseste miniatura clasică (fallback)")
    sys.exit(0 if cale else 3)
