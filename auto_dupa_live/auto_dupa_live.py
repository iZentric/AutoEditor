# AUTO-DUPA-LIVE: tu doar dai live -> acest script face RESTUL singur.
# Ce face: prinde inregistrarea OBS cand termini live-ul -> o urca pe pixeldrain ->
#          declanseaza singur pipeline-ul de pe GitHub -> episoadele apar in Releases.
import base64, json, os, sys, time
import requests

DIR = os.path.dirname(os.path.abspath(__file__))
FORMATII = (".mp4", ".mkv", ".flv", ".mov", ".ts")

def env(nume, implicit=""):
    if os.path.exists(os.path.join(DIR, ".env")):
        for linie in open(os.path.join(DIR, ".env"), encoding="utf-8"):
            if linie.strip().startswith(nume + "="):
                return linie.split("=", 1)[1].strip()
    return implicit

# foldere urmarite: folderul din .env SAU Videos (acolo salveaza OBS implicit)
FOLDERE = [f for f in [env("FOLDER_LIVE"),
                       os.path.join(os.path.expanduser("~"), "Videos")] if f and os.path.isdir(f)]
if not FOLDERE:
    sys.exit("!! nu gasesc folderul cu inregistrarile. Scrie in .env:  FOLDER_LIVE=C:\\Users\\tu\\Videos")

TOKEN = env("GITHUB_TOKEN")
if not TOKEN:
    sys.exit("!! lipsa GITHUB_TOKEN in .env (vezi CITESTE-MA.txt)")
MAXEP = env("MAX_EPISOADE", "2")

def log(*a):
    print(time.strftime("[%H:%M:%S]"), *a, flush=True)

def dimensiune_stabila(cale):
    """Live-ul tocmai s-a terminat: asteptam sa se scrie COMPLET (dimensiune nemodificata)."""
    ultima, nr = -1, 0
    while nr < 3:
        d = os.path.getsize(cale)
        if d == ultima:
            nr += 1
        else:
            nr, ultima = 0, d
        time.sleep(20)
    return True

def pixeldrain(cale):
    log("urc pe pixeldrain (fara cont, poate dura pana la 1h pe net lent)...")
    with open(cale, "rb") as f:
        r = requests.post("https://pixeldrain.com/api/file",
                          files={"file": (os.path.basename(cale), f)}, timeout=60 * 60 * 6)
    r.raise_for_status()
    return "https://pixeldrain.com/u/" + r.json()["id"]

def declansa_github(link):
    """Scrie link-ul in repo (declansa/live.txt) -> push -> workflow-ul porneste singur."""
    cap = "https://api.github.com/repos/iZentric/AutoEditor/contents/declansa/live.txt"
    H = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github+json"}
    continut = base64.b64encode(link.encode()).decode()
    corp = {"message": "live nou gata", "content": continut, "branch": "main"}
    g = requests.get(cap, headers=H, timeout=30)
    if g.status_code == 200:
        corp["sha"] = g.json()["sha"]
    p = requests.put(cap, headers=H, data=json.dumps(corp), timeout=30)
    p.raise_for_status()

procesate = set()
log("AUTO-DUPA-LIVE pornit. Urmaresc:", ", ".join(FOLDERE))
log("Faceti live cu Recording pornit in OBS; cand terminati, restul e automat.")
while True:
    for folder in FOLDERE:
        for nume in os.listdir(folder):
            cale = os.path.join(folder, nume)
            if (nume.lower().endswith(FORMATII) and os.path.isfile(cale)
                    and nume not in procesate and not nume.startswith("~$")):
                procesate.add(nume)
                log("gasit inregistrare noua:", nume)
                try:
                    dimensiune_stabila(cale)
                    link = pixeldrain(cale)
                    log("LINK:", link)
                    declansa_github(link)
                    log("DECLANSAT: pipeline-ul ruleaza pe GitHub -> episoade in ~30 min in Releases")
                    log("https://github.com/iZentric/AutoEditor/actions")
                    destinatie = os.path.join(DIR, "incarcat")
                    os.makedirs(destinatie, exist_ok=True)
                    os.replace(cale, os.path.join(destinatie, nume))
                except Exception as e:
                    log("!! eroare la", nume, ":", e)
                    procesate.discard(nume)
    time.sleep(15)
