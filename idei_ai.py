# IDEI, nu momente random: AI-ul citeste HARTA vorbelor din tot live-ul si alege 2-3 IDEI
# (evenimente concrete din joc cu inceput-desfasurare-final). Fiecare episod = interval CONTINUU
# care spune ideea; TITLUL = ideea. Inceputurile se aliniaza la TAIETURI de scena (PySceneDetect).
# NIVEL 2026 (dupa cercetare: Gemini File API = 1 FPS cu timestamp-uri; Eklipse = verificare vizuala
# a evenimentului): fiecare idee este VERIFICATA trimistand SEGMENTUL REAL de video catre Gemini.
import json
import os
import time
import urllib.request


def incarca_video_gemini(cale, cheie):
    """Urc segmentul la File API (resumable, docs ai.google.dev): returneaza file_uri."""
    import mimetypes
    mt = mimetypes.guess_type(cale)[0] or "video/mp4"
    dim = os.path.getsize(cale)
    req = urllib.request.Request(
        "https://generativelanguage.googleapis.com/upload/v1beta/files",
        data=json.dumps({"file": {"display_name": os.path.basename(cale)}}).encode(),
        method="POST", headers={"Content-Type": "application/json", "x-goog-api-key": cheie,
                                "X-Goog-Upload-Protocol": "resumable",
                                "X-Goog-Upload-Command": "start",
                                "X-Goog-Upload-Header-Content-Length": str(dim),
                                "X-Goog-Upload-Header-Content-Type": mt})
    with urllib.request.urlopen(req, timeout=120) as r:
        url = r.headers["X-Goog-Upload-URL"]     # start-ul NU intoarce body — doar URL-ul de upload
    chunk = 8 * 1024 * 1024
    trimis = 0
    nume = ""
    with open(cale, "rb") as f:
        while trimis < dim:
            bucata = f.read(chunk)
            final = trimis + len(bucata) >= dim
            h = {"Content-Length": str(len(bucata)),
                 "X-Goog-Upload-Command": "upload, finalize" if final else "upload",
                 "X-Goog-Upload-Offset": str(trimis)}
            with urllib.request.urlopen(urllib.request.Request(url, data=bucata, headers=h,
                                                               method="POST"), timeout=600) as r:
                if final:
                    try:
                        nume = json.load(r)["file"]["uri"]
                    except Exception:
                        pass
            trimis += len(bucata)
    if not nume:
        raise RuntimeError("File API: finalize n-a returnat file.uri")
    # asteptam procesarea (state -> ACTIVE)
    for _i in range(30):
        with urllib.request.urlopen(urllib.request.Request(
                f"https://generativelanguage.googleapis.com/v1beta/files/{nume.split('/')[-1]}?key={cheie}"),
                timeout=60) as r:
            st = json.load(r).get("state", "")
        if st == "ACTIVE":
            return nume
        if st == "FAILED":
            raise RuntimeError("File API: procesare esuata")
        time.sleep(4)
    raise RuntimeError("File API: timeout procesare")


def ia_gemini_video(cheie, model, prompt, cale_video):
    """Acelasi apel ca in autoeditor.ia_gemini, dar partea 1 = SEGMENTUL DE VIDEO (File API).
    Gemini mostreaza 1 FPS cu timestamp-uri — 'stie' ce se intampla in clip, nu ghiceste."""
    uri = incarca_video_gemini(cale_video, cheie)
    body = json.dumps({"contents": [{"parts": [
        {"file_data": {"mime_type": "video/mp4", "file_uri": uri}},
        {"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json", "temperature": 0.3}}).encode()
    modele = [model, "gemini-3.6-flash", "gemini-3.5-flash"]   # aliasii pot fi 503 -> ne coboram
    ultima = None
    d = None
    for m in modele:
        for incercare in range(3):
            req = urllib.request.Request(
                f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent",
                data=body, method="POST",
                headers={"Content-Type": "application/json", "x-goog-api-key": cheie})
            try:
                with urllib.request.urlopen(req, timeout=300) as r:
                    d = json.load(r)
                break
            except urllib.error.HTTPError as ex:
                ultima = ex
                if ex.code in (503, 500, 429):
                    time.sleep(6 * (incercare + 1))
                    continue
                raise
        if d:
            break
    if not d:
        raise RuntimeError(f"Gemini n-a raspuns pe niciun model ({ultima})")
    txt = d["candidates"][0]["content"]["parts"][0]["text"].strip()
    if txt.startswith("```"):
        txt = txt.strip("`").strip()
        if txt.lower().startswith("json"):
            txt = txt[4:].strip()
    return json.loads(txt)


def snap_taietura(video, t):
    """Apropie momentul de o taietura reala de scena (±25s) ca episodul sa nu porneasca brusc."""
    try:
        from scenedetect import ContentDetector, SceneManager, VideoManager
        vm = VideoManager([video], start_time=max(0, t - 25), end_time=t + 25)
        sm = SceneManager()
        sm.add_detector(ContentDetector())
        vm.set_downscale_factor(8)
        vm.start()
        sm.detect_scenes(vm, frame_skip=6)
        sc = sm.get_scene_list()
        if not sc:
            return t
        best = t
        for s, _e in sc:
            cut = int(s.get_seconds())
            if abs(cut - t) < abs(best - t):
                best = cut
        return best if abs(best - t) <= 25 else t
    except Exception:
        return t          # fara scenedetect pornim oricum (nu blocam)


def verifica_idee_cu_video(ff, cheie, model, video, ide, tmp="/tmp/segment_idee.mp4"):
    """NIVEL 2026: taie segmentul ideii (480p, mic) si il da Gemini sa-l VADA.
    Raspunde: se confirma evenimentul? un singur joc? titlul corect? unde e hook-ul?"""
    import subprocess
    inc, sf = int(ide["inceput"]), int(ide["sfarsit"])
    subprocess.run([ff, "-y", "-ss", str(max(0, inc - 5)), "-i", video, "-t", str(sf - inc + 10),
                    "-vf", "scale=854:480", "-c:v", "libx264", "-preset", "veryfast", "-crf", "28",
                    "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", tmp],
                   check=True, capture_output=True)
    prompt = (
        "Esti editor senior. Urmareste clipul. Verifica daca poate fi episod:\n"
        f"IDEEA propusa: \"{ide.get('titlu', '')}\" ({ide.get('de_ce', '')})\n"
        'Raspunzi DOAR cu JSON: {"ok": true/false (true doar daca ideea CHIAR se intampla vizibil in clip), '
        '"ce_se_intampla": "3 propozitii concrete cu ce VEZI in joc", '
        '"un_joc": true/false (false daca vedezi trecerea Minecraft<->Roblox sau meniuri/setari), '
        '"titlu_corectat": "titlul care descrie EXACT ce se vede, max 55 caractere, aceeasi idee", '
        '"hook_sec": secunda din clip cu cel mai tare moment (numar), '
        '"scor": 0-10 pt copii 8-15}')
    return ia_gemini_video(cheie, model, prompt, tmp)


def idei_cu_ai(ia_gemini, cheie, model, transcript, live_len, baza):
    """Editorul ADEVARAT: 2-3 IDEI cu poveste completa -> intervale continue + titluri.
    ia_gemini e functia din autoeditor (o primit ca parametru — fara import circular)."""
    linii = []
    for a, _b, t in transcript:
        linii.append(f"{int(a) // 60}:{int(a) % 60:02d} {t[:90]}")
    harta = "\n".join(linii)[:9000]
    stil = ""
    p = os.path.join(baza, "cunoastere", "adn_canale.md")
    if os.path.exists(p):
        stil = open(p, encoding="utf-8").read()[:1200]
    prompt = (
        "Esti editor YouTube senior. Mai jos e harta a CE SE VORBESTE intr-un live de gaming (min:sec — text). "
        "Alege 2-3 IDEI care pot fi EPISOADE: fiecare idee = un eveniment CONCRET din joc care are "
        "inceput-desfasurare-final (prindere pokemon rar/legendar, lupta/raid, gasirea unui loc/loot, "
        "un plan care reuseste sau esueaza amuzant). Fiecare episod = interval CONTINUU de secunde "
        "[inceput, sfarsit] care spune POVESTEA completa (150-170s). REGULI: un singur joc in interval "
        "(NU traversa trecerea Minecraft<->Roblox); nu incepe in meniu/setari/pauza; inceputul = 30-60s "
        "INAINTE de evenimentul tare (ca sa se inteleaga contextul); titlul SPUNE exact ideea "
        "(fara 'Ep.', max 55 caractere, stil: " + (stil[:600] if stil else "MrBeast RO") + "). "
        'Raspunzi DOAR cu JSON: {"idei":[{"titlu":"...","inceput":secunde,"sfarsit":secunde,'
        '"de_ce":"o propozitie","scor":0-10}]}\n\nHARTA LIVE:\n' + harta)
    for _inc in range(3):
        try:
            r = ia_gemini(cheie, model, prompt, [])
            idei = r.get("idei") or []
            bune = []
            for i in idei:
                try:
                    inc, sf = int(float(i["inceput"])), int(float(i["sfarsit"]))
                    if 0 <= inc < sf <= live_len - 10 and sf - inc >= 45:
                        i["inceput"], i["sfarsit"] = inc, sf
                        bune.append(i)
                except Exception:
                    pass
            if bune:
                return bune[:3]
        except Exception as ex:
            print(f"   ! idei ({str(ex)[:50]}) — reincerc", flush=True)
            time.sleep(2)
    return []
