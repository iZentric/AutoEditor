# LIVRARE PE RAND: fiecare episod/short urca pe release IMEDIAT ce e gata,
# ca sa poti descarca EP01 in timp ce se face EP02 (fara asteptare la grămada).
import os
import re
import subprocess
import unicodedata
import tempfile
import shutil


def slug_nume(text, nr=None, ext=".mp4"):
    """Nume de fisier PUBLIC din titlu (fara 'Ep. N' — userul nu vrea EP in nume).
    'CE S-A ÎNTÂMPLAT PE POKECITY?! Ep. 1' + nr=1 -> 'CE_S-A_INTAMPLAT_PE_POKECITY_1.mp4'"""
    t = re.sub(r"\bEp\.?\s*\d+\b", "", str(text))          # scoatem Ep. N din titlu
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode()
    t = re.sub(r"[^A-Za-z0-9]+", "_", t).strip("_").upper()
    if len(t) > 44:
        t = t[:44].strip("_")
    if not t:
        t = "EPISOD"
    if nr:
        t = f"{t}_{nr}"
    return t + ext


def incarca_pe_release(fisier, nume=None):
    """Urca fisierul pe release-ul RELEASE_TAG (daca exista env-ul, adica pe GitHub Actions).
    Nu arunca exceptii: daca esueaza aici, pasul final PUBLISH urca oricum tot."""
    token = os.environ.get("RELEASE_TOKEN", "")
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    tag = os.environ.get("RELEASE_TAG", "")
    if not (token and repo and tag):
        print("   (livrare pe rand inactiva aici — pasul final PUBLISH urca totul)", flush=True)
        return False
    nume = nume or os.path.basename(fisier)
    if not os.path.isfile(fisier):
        print(f"   (livrare pe rand: {nume} nu exista, sarim)", flush=True)
        return False
    env = dict(os.environ, GH_TOKEN=token, GH_REPO=repo)
    try:
        print(f"   LIVRARE PE RAND: {nume} ({os.path.getsize(fisier) // 1048576} MB) -> release {tag} ...", flush=True)
        if os.path.basename(nume) != nume:
            raise ValueError("Release filename must be a basename")
        # gh uses the local basename as the asset name. A label is not a rename.
        with tempfile.TemporaryDirectory(prefix="autoeditor-delivery-") as directory:
            upload_path = os.path.join(directory, nume)
            try:
                os.link(os.path.abspath(fisier), upload_path)
            except OSError:
                shutil.copyfile(fisier, upload_path)
            subprocess.run(["gh", "release", "upload", tag, upload_path, "--clobber"],
                           check=True, env=env, capture_output=True, text=True)
        print(f"   >>> {nume} e GATA DE DESCARCAT ACUM in Releases (restul inca se lucreaza)", flush=True)
        return True
    except subprocess.CalledProcessError as ex:
        print(f"   (livrare pe rand esuata pt {nume}: {(ex.stderr or '')[-300:]} — pasul final il urca oricum)", flush=True)
        return False
