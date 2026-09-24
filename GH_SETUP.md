# Configurare unica, fara chei in chat

## 1. Conectarea GitHub in Arena

Foloseste integrarea GitHub din Arena pentru `iZentric/AutoEditor`.
Aceasta trebuie sa permita modificarea codului si a **Workflows**.
Daca GitHub refuza push-ul cu `without workflows permission`, actualizeaza
permisiunile instalarii/conexiunii GitHub din interfata Arena/GitHub.

**Nu crea si nu trimite un token GitHub in chat.** Agentul foloseste autentificarea
configurata de platforma. Nu pune credentiale in URL-ul remote-ului Git.

## 2. Setarile editorului

In repository: **Settings → Secrets and variables → Actions**.

| Sectiune | Nume | Continut |
|---|---|---|
| Secrets | `GEMINI_API_KEY` | Cheia contului tau pentru verificarea video |
| Variables, optional | `GEMINI_MODEL` | Modelele disponibile contului, separate prin virgule |

Verificarea initiala confirma prezenta setarilor, nu validitatea cheii sau
calitatea rezultatului. Acestea se confirma prin apelul API si proba reala.

## 3. OPTIONAL: incarcare privata pe YouTube

Mai intai citeste [SECURITY.md](SECURITY.md) daca ai publicat vreodata credentialele
in chat. **Nu refolosi valorile expuse.** Rotirea secretului clientului singur nu
inlocuieste revocarea tokenului de autorizare.

Pentru a genera si salva tokenul nou fara copiere manuala, foloseste
[kitul local de autorizare](docs/AUTORIZARE_YOUTUBE.md):
`CONFIGUREAZA_YOUTUBE.bat` pe Windows sau `python oauth_setup.py auth --enable-upload`
pe PC-ul tau, cu client_secret.json nou. Scriptul confirma canalul si trimite
valorile direct in Secrets; nu ruleaza in sandbox.

Alternativ, adauga valori noi in **Secrets**, fiecare separat:
- `YT_CLIENT_ID`
- `YT_CLIENT_SECRET`
- `YT_REFRESH_TOKEN`

Dupa revocare/reautorizare si salvarea valorilor noi, activeaza o singura data
variabila din sectiunea **Variables**: `YT_UPLOAD_ENABLED` = `true`.
Implicit este `false`: editorul livreaza prin Releases, fara sa acceseze canalul.

Upload-urile automate raman **private**. Publicarea pe YouTube o decizi tu.
Nu este nevoie sa dai agentului valorile secretelor. Agentul nu poate deduce
ca sunt configurate doar pentru ca numele lor apar in cod.

## 4. Folosire obisnuita

Live nou → release cu tag `vod-N` si inregistrarea originala atasata → Actions
proceseaza → primesti titlul si linkul de download. Pentru proba initiala exista
sursa `vod-1` si sunetele tale, deci nu trebuie sa le retrimiti.

Nicio randare noua de VOD nu se porneste de agent fara acordul tau.
