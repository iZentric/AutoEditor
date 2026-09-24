# LIVRARE PE RAND: fiecare episod/short urca pe release IMEDIAT ce e gata,
# ca sa poti descarca EP01 in timp ce se face EP02 (fara asteptare la grămada).
import os
import subprocess


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
        subprocess.run(["gh", "release", "upload", tag, fisier, "--clobber"],
                       check=True, env=env, capture_output=True, text=True)
        print(f"   >>> {nume} e GATA DE DESCARCAT ACUM in Releases (restul inca se lucreaza)", flush=True)
        return True
    except subprocess.CalledProcessError as ex:
        print(f"   (livrare pe rand esuata pt {nume}: {(ex.stderr or '')[-300:]} — pasul final il urca oricum)", flush=True)
        return False
