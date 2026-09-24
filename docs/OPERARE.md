# AutoEditor — calitate editoriala stricta (25.09.2026)

**Comportamentul curent al modului `--ai` si al fluxului GitHub Actions**
(prioritar fata de istoricul versiunilor de mai jos):

- Citeste transcriptul **intregului live**, in pagini suprapuse. Propune povesti,
  nu doar varfuri de volum. Evalueaza video maximum 12 idei, ordonate dupa scor.
- Fiecare episod are un interval continuu de **150–170 secunde**. Gemini verifica
  segmentul exact cu imagine si sunet: context, actiune, rezultat, un singur joc,
  titlu sustinut de evenimente. Scor minim **7/10**, campuri obligatorii validate.
- Daca cheia/transcriptul/verificarea lipseste, AI-ul nu raspunde sau toate ideile
  sunt slabe: **opreste livrarea**, nu trece automat la selectie dupa zgomot.
  O pagina de transcript esuata opreste selectia, nu este ignorata.
- Dupa aprobare **nu mai taie povestea dupa volumul audio**. Momentul principal
  este cel indicat in verificarea video, nu mijlocul intervalului.
- Sunetele din `sunete_mele/` si `assets/efecte/` primesc identificatori stabili.
  AI-ul poate alege **0–4 accente**, cu secunda, eveniment si motiv. Nu exista
  umplere aleatorie sau sloturi fixe in modul AI; maximum un bonk/bambus, minimum
  12 secunde intre efecte, fara repetarea fisierului. Efectele sunt limitate la 2s,
  normalizate la -24 LUFS inainte de mixaj; masterul episodului tinteste -14 LUFS.
  Originalele creatorului nu sunt sterse sau despicate in acest mod.
- Replicile mari si galbene sunt alese din citate **exacte** ale transcriptului,
  maximum 6/episod, minimum 18s intre ele. Nu se inventeaza subtitrari.
- Shorts-urile de 16s sunt verificate **separat, pe decupajul vertical**. Primesc
  propriul titlu si plan de sunete; pot fi respinse chiar daca episodul e bun.
- Episoadele sunt randate in 2K **inainte** de livrarea pe rand, nu dupa upload.
  Un esec de randare sau de verificare a masterului audio opreste fluxul.
- `episodes/DECIZII_AI.json`, `DECIZII_SHORTS.json` si `RAPORT.md` explica alegerile.
  Deciziile disponibile se pastreaza si ca artifact in Actions la esec.

**Limite oneste:** selectia initiala foloseste vorbirea transcrisa, deci poate rata
actiuni complet mute. Verificarea video este facuta de un model si poate gresi;
nu este echivalenta cu o vizionare umana cadru cu cadru. Sensul sunetelor este dedus
in aceasta versiune din nume/categorie, **nu din ascultarea fiecarui fisier audio**;
cele ambigue ar trebui omise. Miniaturile raman cadre reale editate. Revizia umana
a primei livrari este necesara pentru calibrare. Nicio garantie de vizualizari.

Modul fara `--ai` pastreaza comportamentul euristic vechi pentru utilizare manuala;
nu este folosit de pipeline-ul automat. Modelele Gemini se configureaza prin
`GEMINI_MODEL` (lista separata prin virgule); disponibilitatea lor trebuie verificata
pe contul folosit, nu presupusa din notitele istorice.

### Teste fara video sau chei

```sh
python -m unittest discover -s tests -v
python -m compileall -q .
```

Testele acopera selectia de la finalul unui live lung, refuzul ideilor slabe,
erorile AI, momentele linistite, suprapunerile, efectele invalide/repetate,
subtitrarile exacte, modelele de rezerva, shorts-urile si livrarea fisierelor.
API-urile si randarea sunt simulate: trecerea testelor **nu certifica inca**
calitatea vizuala a unui live real. Procesarea reala se face numai pe GitHub Actions,
la acordul creatorului; niciun VOD nu se descarca in sandbox.

---

## Viteza fara eliminarea verificarilor (25.09.2026)

- Transcrierea exacta este refolosita dupa amprenta continutului sursei, model,
  versiune si parametrii de decodare. Schimbarea sursei sau a modelului invalideaza
  rezultatul; numele fisierului singur NU identifica un live.
- Ideile si verificarile video aprobate se pot refolosi maximum 24h, numai cu
  aceleasi date, prompt, model, interval, decupaj si catalog de sunete. Regulile
  editoriale sunt validate si pe rezultatul din cache. Erorile, raspunsurile
  incomplete si verificarile respinse NU devin aprobari memorate.
- Analiza RMS separata a intregului live este eliminata in modul AI: nu participa
  la selectia editoriala. Durata vine din metadate; transcrierea completa ramane.
- La reluarea unui Actions, cache-ul mic de analize, modelul Whisper si pachetele
  descarcate sunt reutilizate. Nu se reduc modelul, pragurile sau numarul de cadre
  al exportului ca scurtatura de viteza. Fara randari grele paralele care risca sa
  epuizeze memoria runnerului.
- Pentru YouTube se solicita sursa pana la 1440p, nu 1080p urmat artificial de 2K.
  Pentru fisierele originale atasate in Releases, rezolutia nativa >=1440p ramane
  pastrata. Upscale-ul NU inventeaza detalii lipsa dintr-o sursa mica.
- Exportul AI foloseste CRF20/preset medium inclusiv pentru surse deja 2K;
  `AE_USOR=1` nu forteaza 30 cadre/s pe episoadele verificate.
- `PERFORMANTA_editor.json` si `PERFORMANTA_shorts.json` arata timpii etapelor si
  ce s-a refolosit. Nu exista inca un benchmark real al noii versiuni pe un VOD.

Setari optionale pentru depanare: `AE_CACHE=0` opreste reutilizarea;
`AE_REANALYZE=1` forteaza reanalizarea; `AE_CACHE_DIR` schimba folderul de cache.
`.cache/` nu se comite in Git. In Actions, rezultatele complete sunt salvate si
cand o etapa ulterioara esueaza; un nou live nu anuleaza automat randarea curenta.

### Sunetele pe care le avem deja

`sunete_mele/catalog.json` descrie cele 10 fisiere existente, fara a modifica audio:
- `pumm`: impact/cadere a personajului (indicatia creatorului);
- `faaa`: sperietura;
- Bamboo/bonk: lovitura comica, rar;
- metal: impact de obiect;
- anime wow: descoperire/victorie;
- vine boom: revelatie/esec surprinzator;
- awkward: pauza comica reala;
- pop: aparitie de obiect;
- basina: numai un gag explicit potrivit, nu umplutura.

Planul AI trebuie sa declare tipul evenimentului permis de catalog. Un sunet de
cadere propus la o victorie este respins. Aceste asocieri folosesc indicatiile
creatorului/numele fisierelor, **nu certifica o ascultare acustica sau o licenta**.
Nu descarcam automat sunete de la alti creatori; folosim fisierele oferite.

### Configurare minima

1. Integrarea GitHub din Arena trebuie sa poata modifica **Workflows** pentru a
   publica aceasta versiune. Daca push-ul este refuzat, reconecteaza/actualizeaza
   integrarea; niciodata tokenuri in chat.
2. In GitHub Actions: Secret `GEMINI_API_KEY`; variabila optionala `GEMINI_MODEL`
   cu modelele disponibile contului. Verificarea initiala confirma doar prezenta
   setarilor; disponibilitatea reala a modelului se confirma la apelul API.
3. Live-ul si sunetele din `vod-1` / `sunete_mele/` sunt suficiente pentru proba.
   Pentru un live nou, publica un release `vod-N` cu inregistrarea originala.
4. OPTIONAL, doar pentru incarcare privata direct pe YouTube: configureaza in
   GitHub Secrets `YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN` din
   autorizarea propriului canal. Dupa configurarea sigura a valorilor noi, seteaza
   variabila `YT_UPLOAD_ENABLED=true`. Implicit upload-ul este oprit; livrarea
   prin Releases continua. Vezi [securitate](../SECURITY.md).

Prima livrare ramane de vizionat/ascultat pentru calibrare. Cache-ul economiseste
munca repetata; nu garanteaza viteza unui serviciu cu GPU si nici editare perfecta.

---
