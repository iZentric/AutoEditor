# Credentiale si protectia materialelor creatorului

## Daca ai trimis chei sau tokenuri in chat

Considera credentialele expuse, chiar daca repository-ul este privat.
Stergerea mesajului sau mutarea aceleiasi valori in Secrets NU anuleaza expunerea.

1. In [Contul Google — conexiuni](https://myaccount.google.com/connections), revoca
   accesul aplicatiei OAuth folosite pentru AutoEditor/YouTube. Aceasta revoca
   autorizarea veche; va trebui refacuta autorizarea canalului.
2. In [Google Cloud Console](https://console.cloud.google.com/), la clientul OAuth
   al aplicatiei (Google Auth Platform → Clients sau APIs & Services → Credentials),
   inlocuieste/reseteaza secretul. Daca interfata nu permite rotirea lui, creeaza
   un client nou si reconfigureaza autorizarea.
3. Reautorizeaza propriul canal prin fluxul OAuth de incredere folosit pentru
   configurare si obtine un token nou. Nu trimite tokenul, codul de autorizare
   sau fisierul clientului in chat.
4. In GitHub → repository → Settings → Secrets and variables → Actions,
   actualizeaza `YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN`.
5. Numai dupa pasii de mai sus: `YT_UPLOAD_ENABLED=true` in **Variables**.

ID-ul clientului nu este secret in sine. Secretul clientului si tokenul de
reimprospatare necesita protectie. Agentul nu poate sterge mesajul sau revoca
accesul Google in numele tau doar citind conversatia.

## Reguli pentru cod si diagnostic

- Credentialele reale nu intra in cod, Git, memoria proiectului, loguri sau chat.
- Exemplele contin numai substituenti; autentificarea GitHub vine din integrarea Arena.
- `.env*`, exporturile OAuth si cookies sunt ignorate de Git. Aceasta regula
  nu protejeaza automat un fisier care era deja urmarit de Git.
- `python tools/check_secrets.py` scaneaza fisierele versionate/candidate pentru
  cateva formate cunoscute de credentiale. Raporteaza numai calea si tipul,
  NICIODATA valoarea gasita. Nu este un audit complet si nu scaneaza conversatia.
- Daca o valoare a ajuns in istoricul Git, revoc-o intai; curatarea istoricului
  necesita o actiune separata, nu un simplu commit de stergere.

## Materialele creatorului

Sunetele originale si momentele furnizate de creator nu sunt sterse, mutate,
despartite sau recodate automat. Catalogul editorial este separat de fisierele
originale. Curatenia vizeaza rezultate temporare si artefacte de test, nu surse.
Nu se descarca automat noi efecte, melodii sau meme-uri de la alti creatori.
