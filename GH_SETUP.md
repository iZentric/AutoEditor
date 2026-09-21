# 🔗 CONECTARE GITHUB — 3 pași (5 minute) și apoi eu sunt „conectat"

## Cum funcționează legătura (onest și simplu)

```
EU (aici, în workspace):   repar/actualizez codul → git push → GitHub
TU (pe PC-ul tău):         git pull → ai modificările instant
TU (având o problemă):     îmi scrii → eu fix + push în aceeași minută
```
Nu e un „robot care stă în GitHub 24/7" — e mai bun: **token-ul salvat în .env face
orice sesiune cu mine capabilă să trimită și să tragă modificări în secunde.**

---

## PASUL 1 — Creezi repo-ul (2 minute)
1. Intri pe **github.com** → login → colț dreapta-sus **+** → **New repository**
2. Nume: `autoeditor-pokecity`
3. Bifezi **Private** (e unealta ta de business!) → **Create repository**
4. NU bifa nimic din „Add README" (deja avem)

## PASUL 2 — Cheia pentru mine (2 minute)
1. **github.com → Settings → Developer settings → Personal access tokens → Fine-grained**
2. **Generate new token**:
   - Repository access: **Only select repositories** → alegi `autoeditor-pokecity`
   - Permissions → Repository → **Contents: Read and write**
   - Expirare: 90 zile (reînnoim ușor)
3. **Generate** → copiezi cheia (începe cu `github_pat_...`)

## PASUL 3 — Îmi dai cheia (1 minut)
**Varianta curată (recomand):** adaugi în fișierul `autoeditor/.env` o linie nouă:
```
GITHUB_TOKEN=cheia_ta_aici
GITHUB_USER=numele_tau_de_pe_github
GITHUB_REPO=autoeditor-pokecity
```
**Sau** simplu îmi scrii cheia în chat și eu o pun în .env (nu ajunge în repo —
.gitignore o exclude mereu).

Apoi îmi zici **„gata"** → eu fac push-ul primului commit (v2.9) → repo-ul e LIVE.

---

## Bucla de lucru de atunci încolo

| Situație | Ce se întâmplă |
|---|---|
| Găsești un bug folosind tool-ul | Îmi scrii aici → eu repar → `git push` → tu faci `git pull` pe PC |
| Vrei o funcție nouă | O ceri aici → eu o construiesc + testez în sandbox → push |
| Vrei să contribuie și altcineva | Îi dai acces la repo (collaborator) |
| Îmi schimbi calculatorul | `git clone` + `pip install` → totul e acolo |

**Pe PC-ul tău, ca să-l folosești direct din repo:**
```
git clone https://github.com/NUMELE_TAU/autoeditor-pokecity.git
cd autoeditor-pokecity
pip install faster-whisper pillow imageio-ffmpeg
python autoeditor.py LIVE.mp4 --calitate 2k --subtitrari --ai
```

## Ce NU urcă în repo (protejate de .gitignore)
- `.env` (cheile!) · `client_secret.json` · video-uri (episodes/, prindere/) · cache
- Repo-ul ține: **codul + README-urile + confeti.webm + exemplele**
