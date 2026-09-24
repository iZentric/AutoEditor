# Livrare SIMPLA: postez pe Issue #2 (si afisez) doar TITLU + LINK de download per piesa.
# Linkurile browser_download_url merg in browserul userului (logat pe GitHub) — click = salveaza pe PC.
import json
import os
import urllib.parse
import urllib.request

REPO = "iZentric/AutoEditor"
GH = {"Authorization": "Bearer " + os.environ["GITHUB_TOKEN"], "Accept": "application/vnd.github+json",
      "User-Agent": "autoeditor"}


def gh(u, body=None, method="GET"):
    h = dict(GH)
    if body:
        h["Content-Type"] = "application/json"
    r = urllib.request.urlopen(urllib.request.Request(u, data=json.dumps(body).encode() if body else None,
                                                      headers=h, method=method), timeout=60)
    c = r.read()
    return json.loads(c) if c.strip() else {}


def titlu_din_asset(aid):
    h = dict(GH)
    h["Accept"] = "application/octet-stream"
    try:
        txt = urllib.request.urlopen(urllib.request.Request(
            f"https://api.github.com/repos/{REPO}/releases/assets/{aid}", headers=h), timeout=60).read().decode("utf-8", "replace")
        randuri = txt.splitlines()
        for i, l in enumerate(randuri):
            if l.startswith("TITLU:"):
                t = l.split(":", 1)[1].strip()
                if not t and i + 1 < len(randuri):
                    t = randuri[i + 1].strip()
                return t
    except Exception:
        pass
    return ""


def listeaza(tag="vod-1"):
    rel = gh(f"https://api.github.com/repos/{REPO}/releases/tags/{tag}")
    assets = rel.get("assets", [])
    randuri = ["**TITLU + DOWNLOAD (click -> se salveaza pe PC):**"]
    for a in assets:
        n = a["name"]
        if not n.endswith("_upload.txt"):
            continue
        baza = n[:-11]                       # fara _upload.txt
        titlu = titlu_din_asset(a["id"]) or baza.replace("_", " ")
        vf = [x for x in assets if x["name"].startswith(baza) and x["name"].endswith(".mp4")]
        if not vf:
            continue
        enc = urllib.parse.quote(vf[0]["name"])
        randuri.append(f"- **{titlu}** -> [DESCARCA {vf[0]['name']}]"
                       f"(https://github.com/{REPO}/releases/download/{tag}/{enc})")
    return "\n".join(randuri)


if __name__ == "__main__":
    mesaj = listeaza()
    print(mesaj)
    iss = gh(f"https://api.github.com/repos/{REPO}/issues?state=all&per_page=5")
    n = None
    for i in iss:
        if "EPISOADE GATA" in i.get("title", ""):
            n = i["number"]
            break
    if n:
        gh(f"https://api.github.com/repos/{REPO}/issues/{n}/comments", {"body": mesaj}, "POST")
        print(f"(postat pe Issue #{n})", flush=True)
