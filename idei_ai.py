# IDEI, nu momente random: AI-ul citeste HARTA vorbelor din tot live-ul si alege 2-3 IDEI
# (evenimente concrete din joc cu inceput-desfasurare-final). Fiecare episod = interval CONTINUU
# care spune ideea; TITLUL = ideea. Inceputurile se aliniaza la TAIETURI de scena (PySceneDetect).
import os
import time


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
            r = ia_gemini(cheie, model, prompt, None)
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
