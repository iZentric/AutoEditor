# Token YouTube nou — fara copiere in chat

## Pe Windows

1. Descarca si dezarhiveaza kitul de autorizare.
2. Din [Google Cloud — Credentials](https://console.cloud.google.com/apis/credentials)
   descarca JSON-ul **clientului OAuth de tip Desktop app**, cu secretul nou.
   Pune-l in folderul kitului cu numele `client_secret.json`.
   Nu incarca acest fisier in GitHub si nu il trimite in chat.
3. Ai nevoie de [Python 3.10+](https://www.python.org/downloads/) si
   [GitHub CLI](https://cli.github.com/), daca nu sunt deja instalate.
4. Dublu-click pe **CONFIGUREAZA_YOUTUBE.bat**. Daca este nevoie, te conectezi
   la GitHub in browser. Apoi se deschide **pagina oficiala Google**.
5. Alege contul/canalul iZentric si aproba accesul. Revino la fereastra scriptului,
   verifica numele canalului afisat si scrie **DA** numai daca este canalul corect.

Scriptul salveaza direct cele trei valori potrivite intre ele in repository-ul
`iZentric/AutoEditor`: `YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN`.
**Nu afiseaza tokenul, nu il scrie intr-un .env si nu cere sa copiezi vreun cod in chat.**
Dupa salvarea tuturor valorilor, porneste variabila `YT_UPLOAD_ENABLED=true`.
Nu porneste randari si nu incarca un video in timpul configurarii.

## Alte sisteme / comanda manuala

Din folderul kitului, dupa instalarea Python si GitHub CLI:

```sh
python -m venv .venv-oauth
# Linux/macOS:
. .venv-oauth/bin/activate
python -m pip install -r requirements-oauth.txt
gh auth login --web --hostname github.com
python oauth_setup.py auth --repo iZentric/AutoEditor --enable-upload
```

Ruleaza pe PC-ul tau, unde este browserul. **Nu in sandbox/Actions**: redirectionarea
OAuth este locala si nu ar ajunge la serverul din alt calculator. Scriptul foloseste
fluxul oficial cu redirectionare locala si protectie PKCE, nu varianta veche de
copiere manuala a unui cod de autorizare.

## Daca apare o eroare

- Client Web in loc de Desktop: descarca/creeaza clientul de tip Desktop.
- Aplicatie in Testing: contul tau trebuie adaugat in Test users; tokenul poate
  necesita reinnoire, in functie de configurarea Google.
- YouTube Data API v3: trebuie activata in proiectul Google al clientului.
- GitHub refuza Secrets/Variables: contul conectat local trebuie sa poata administra
  aceste setari pentru repository. Scriptul nu afiseaza corpurile erorilor cu date sensibile.
- Daca salvarea este partiala, upload-ul ramane dezactivat. Corecteaza accesul si
  reia configurarea; nu presupune ca mesajul de succes din browser inseamna ca
  secretul a fost deja salvat in GitHub.

Daca secretul clientului a fost expus anterior, trebuie inlocuit si el, nu doar
tokenul revocat. Nu reutiliza valori trimise in chat.

**Separat:** acest kit nu repara permisiunea Workflows a integrarii GitHub din Arena.
Aceea se acorda din setarile integrarii. Actualizarea secretelor nu publica automat
modificarile de cod ale proiectului.
