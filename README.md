# 🎬 AUTOEDITOR POKECITY v2.7 — TU DOAR FACI LIVE, TOTUL ALTCEVA E AUTOMAT

## FLUXUL COMPLET (ținta finală)

```
TU: live pe OBS (2K) — cu „Înregistrare" pornită sau cu ia_live.py
EI: python autoeditor.py prindere/live_full.mp4 --subtitrari --ai
    ↓ (găsește momentele · construiește poveștile · AI judecă + titluri garantate
       · sunete potrivite contextului · confeti · texte · 2K · subtitrări)
TU: primești în episodes/:
    📹 EP01.mp4            episodul editat (~2:50)
    🖼 EP01_miniatura.jpg   MINIATURA EDITATĂ din cadru REAL (stil Minecraft:
                            crop, culori tari, logo tău, text mare cu contur —
                            NICIODATĂ generată cu AI, regula canalului)
    📝 EP01_upload.txt      TITLU + DESCRIERE + TAG-URI gata de lipit în Studio
    💬 EP01.srt             subtitrările (dacă --subtitrari)
    📊 RAPORT.md            ce a ales, scoruri AI, PROMIS=LIVRAT, CHECKLIST
    🖼 EP01_cadru1/2/3.jpg   cadre alternative dacă vrei altă miniatură
TU: vizionezi episodul (10 min, filtrul de calitate) → uploadezi + lipești din _upload.txt
```

*Construit+testat 21.09.2026 · verificat și CU OCHII: textele de engagement cad pe ecran la secunda exactă · 0 lei/lună, rulează pe PC-ul tău*

---

## STRUCTURA unui episod (de-asta se înțelege bine!)

Momentele sunt luate DIN TOT LIVE-UL și puse în ordine cronologică = o poveste pe care copiii o urmăresc:

```
0:00  INTRO-REACTIE (8s)   cadru din MIJLOCUL momentului maxim -> „uite ce se intampla!"
0:08  SETUP (55s)          cum a pornit totul (moment din INCEPUTUL live-ului)
1:03  DESFASURARE (55s)    actiunea creste (moment din MIJLOCUL live-ului)
1:58  MOMENTUL MAXIM (52s) explozia completa, cu 15s de hook inainte
2:48  CTA + final BRUSC
```

**Texte de engagement pentru copii, puse automat pe ecran:**
- la **0:12**: „CE CREZI CĂ SE INTÂMPLĂ? Scrie în comentarii!" (alb)
- la **1:48**: „ATENTIE! ACUM VINE MOMENTUL CEL MAI TARE!" (galben — chiar înainte de maxim, ca la desene animate)
- la **final (ultimele 5s)**: „LIKE + scrie în comentarii ce prindem în episodul următor!"
- semnătura canalului în colț tot clipul + logo-ul tău (assets/logo.png) + muzica ta sub voce (assets/muzica.mp3)

## Ce face (în 4 pași)

1. **Ascultă live-ul** — volum pe fiecare secundă; explozia = volum peste baza zonei lui (prinde strigate/râsete, chiar și momente lungi).
2. **Construiește POVESTILE** — moment maxim + setup + desfășurare, cronologic, fără suprapuneri. Plus: 2-3 **sunete comice random** per episod (din pool-ul tău) + **confetti** pe final.
3. **Editează singur** — concatenarea scenelor + logo + texte + muzică, final brusc.
4. **Exportă** — episoade + 3 cadre REALE per episod pt miniaturi + RAPORT.md cu planul fiecărei povești.

Dacă un moment tare nu are setup/desfășurare disponibil, intră în **mod clasic** (o scenă-episod, ca v1) — nimic nu se pierde, nimic nu se reciclează de 2 ori.

## Ce îți trebuie (o dată, 5 minute)

1. **Python** (ai deja dacă rulezi celelalte scripturi ale noastre)
2. **ffmpeg** — pe Windows: `winget install ffmpeg` în CMD (sau `pip install imageio-ffmpeg`)

## Pachetul tău (sunete/muzica/logo) — PLUG-AND-PLAY

- `assets/muzica.mp3` — muzica de fundal (sub voce, automat)
- `assets/logo.png` — logo-ul în colț (automat)
- `assets/efecte/` — **efectele sonore: pui fișierele cu nume fixe (`intrare`, `hype`, `explozie`, `victorie`, `final`) și se triggerează SINGURE la momentele corecte din TOATE episoadele. Zero configurare per video.** Detalii: `assets/efecte/README.md`
- `assets/efecte/confeti.webm` — **CONFETTI pentru copii, deja inclus!** Ploaie colorată de 2s care cade automat în ultimele 8 secunde ale fiecărui episod (pe momentul de după maxim, înainte de CTA). Testat vizual ✓. Vrei altul? Înlocuiești fișierul cu orice .webm transparent.
- `assets/efecte/random/` — **SUNETE COMICE, PRECISE PE CONTEXT** (bambus, os rupt, țeavă, bruh, cheer...). Cu faster-whisper activ, editorul CITESTE ce ai zis și potrivește sunetul cu momentul:
  - zici „AM PRINS!" → sunet din `fericit_*` (cheer, ta-da)
  - zici „a căzut!/doare!" → sunet din `cadere_*` (os rupt, boink, țeavă)
  - zici „ce frică!" → sunet din `speriat_*` (stinger)
  - fișiere fără prefix = pool generic (random în puncte sigure)
  - Fără faster-whisper → tot merge, doar aleatoriu. Testat: sunetul cade pe secunda exactă a cuvântului ✓

Testat: toate 5 sloturi de efecte au căzut la secunda exactă (verificat cu analiză de volum pe output).

## CE FOLOSIM (răspuns clar)

**Autoeditorul ăsta** (construit special pentru PokeCity): ffmpeg + analiză audio proprie + regulile noastre validate (MrBeast, Nocivanu playbook). Rulează LOCAL pe PC-ul tău, 0 lei, fără limite.

**De ce NU un AI de chat / AI-video (ChatGPT, Sora, etc.):**
- nu pot „privi" 2-4h de live real (contextul lor e minute, nu ore)
- AI-video GENEREAZĂ imagini false — tu ai nevoie de GAMEPLAY REAL din live-ul tău (regula miniaturilor: nimic fals)
- ar costa zeci de lei/lună; ăsta e gratuit și e al tău
- „inteligența" lui e antrenată pe regulile noastre: explozii = strigate/râsete, hook 15s înainte, momentul maxim la min 2, final brusc

## Comenzile

```
cd autoeditor
python autoeditor.py LIVE.mp4 --calitate 2k              ← RECOMANDAT: episoade 2K
python autoeditor.py LIVE.mp4 --calitate 2k --subtitrari ← 2K + subtitrari AI (.srt per episod)
python autoeditor.py LIVE.mp4 --calitate 2k --pachet halloween  ← 2K cu pachetul de Halloween
python autoeditor.py LIVE.mp4 --momente momente.txt      ← TU zici EXACT momentele
python autoeditor.py LIVE.mp4 --doar-analiza             ← doar planul, rapid
```

## 📥 ACCESUL DIRECT LA LIVE (rezoluție NATIVĂ, fără re-encodare YouTube)

**METODA 1 — OBS „Înregistrare" (CEL MAI SIMPLU, recomandat):**
1. OBS: Settings → Output → Output Mode: Advanced → Recording:
   Type: Standard · Format: MP4 · Encoder: NVENC/AMF · Rate Control: CQP, CQ=18-20
2. La live bifezi și „Start Recording" — înregistrează SIMULTAN cu stream-ul
3. La final ai fișierul local la calitate MAI BUNĂ decât pe YouTube (fără re-encodarea lor)

**METODA 2 — ia_live.py (captură pe alt PC sau în rețea):**
```
python ia_live.py          → așteaptă conexiunea
OBS → Settings → Stream → Custom → Server: rtmp://localhost/live  Key: pokecity
```
- captează BIT PENTRU BIT ce trimite OBS (`-c copy`, zero re-encodare) — testat: stream 2K (2560×1440) → fișier nativ identic
- util când: PC-ul slab → înregistrează al doilea PC din rețea (schimbi `localhost` cu IP-ul lui)

**Dacă tot vrei de pe YouTube:** `yt-dlp -f "bv*+ba/b" LINK` (1080p60 ≈ 17,5 GB / 6h; 2K ≈ 27 GB)

## 2K — adevărul complet (2 capete)

**Capul 1 — LIVE-UL (cel mai important):** 2K real se naște în OBS, la live:
| Setare OBS | Valoare |
|---|---|
| Canvas + Output | 2560x1440 |
| Bitrate | 13000–20000 Kbps (1440p60) |
| Encoder | NVENC (NVIDIA) / AMF (AMD) — nu x264 pe procesor |
| Keyframe | 2s |

Dacă PC-ul nu duce 1440p60 la bitrate-ul ăsta → live 1080p60 liniștit (calitatea conținutului bate rezoluția).

**Capul 2 — EXPORTUL:** `--calitate 2k` scalează cu LANCZOS + sharpen subtil și encodează la CRF 20. De ce ajută chiar și peste un live 1080p: YouTube dă bitrate MAI MARE la 1440p → imaginea ta supraviețuiște mai bine re-encodării lor. Dacă live-ul e deja 1440p+ → pastră nativ, fără upscalare.

## Pachete actualizabile în timp (sunete noi, sezoniere)

- `assets/` = pachetul de bază
- Orice pachet nou: faci folder `assets_halloween/` (aceeași structură: muzica.mp3, logo.png, efecte/) și rulezi cu `--pachet halloween`
- Exemplu gata în workspace: `assets_halloween/`
- **Schimbi un fișier → următorul run îl folosește. Nimic de configurat per video, niciodată.**

## Subtitrări AI locale (opțional, gratuit)

```
pip install faster-whisper     ← o singură dată
python autoeditor.py LIVE.mp4 --calitate 2k --subtitrari
```
- AI-ul transcrie live-ul o SINGURĂ dată și remapează replicile pe scenele fiecărui episod (chiar dacă scenele sar prin live — testat: replica din minutul 100 cade corect la 0:10 în episod)
- De ce subtitrări: mulți copii se uită FĂRĂ sunet + transcriptul ajută la căutare
- PC slab? `WHISPER_MODEL=base` sau `tiny` înainte de comandă (implicit: small)
- Fără faster-whisper instalat → tot merge, doar sare pasul (te anuntă)

## Modul MANUAL — tu zici momentele exacte (fisier momente.txt)

Ai văzut live-ul și știi TU unde a fost cel mai tare? Scrii momentele în `momente.txt` (uită-te la `momente_EXEMPLU.txt`):
```
# un moment pe linie — minut:secunda sau ora:minut:secunda
2:30
13:20
1:45:10
```
Apoi: `python autoeditor.py LIVE.mp4 --momente momente.txt`
→ fiecare moment al tău devine MOMENTUL MAXIM al unui episod, iar tool-ul construiește în jurul lui intro-reactia + setup + desfășurare (dacă există material). Tu ești șeful: în modul ăsta poarta de elită nu se aplică.

## Poarta de ELITĂ + MOTIV DE EXISTĂ (regula ta, implementată dublu)

**„Dacă e doar 1 chestie faină, să nu facă altele."** Exact așa merge:
1. **Poarta absolută**: intră doar momentele cu scor ≥ jumătate din scorul celui mai tare moment (+ minim 7dB)
2. **MOTIV DE EXISTĂ (nou)**: după selecție, fiecare episod trebuie să aibă scor ≥ 55% din cel mai tare episod al live-ului. **Un live de 4h cu 1 poveste excelentă + 5 mediocre = 1 EPISOD.** (Confirmat de MrBeast: „1 video insanely good > 10 medii" — nu posta doar ca să ai orar.)
- testat: live cu 7 momente → doar 3 au trecut → 1 poveste; live cu 1 moment bun → EXACT 1 episod
- dacă niciun moment nu e suficient de tare: refuză să facă episoade slabe (mesaj clar)

## MAXIMUL PENTRU UN EPISOD DE 3 MIN (ce face fiecare secundă să conteze)

| Strat | Ce face | Cine l-a inspirat |
|---|---|---|
| Poartă de elită + motiv de există | doar momentele din clasa de vârf | regula ta + MrBeast |
| Poveste cronologică | intro→setup→dezf→maxim | MrBeast re-engagement |
| **Comprimare stil-JOH** | taie golurile ≥12s din mijloc (zero dead-air) | Jocuri Horror (narare continuă) |
| **Final elastic** | taie când povestea s-a terminat | MrBeast |
| **Normalizare voce -16 LUFS** | volum constant, indiferent de microfon | standard streaming |
| Sunete pe context + random + confetti | comic + sărbătoare | cultura nișei (iRaffael 499K) |
| 4 texte pe ecran la secunde exacte | întrebare→hype→LIKE→ABONARE | engagement copii |
| AI: 6 cadre + in_joc + titlu promis=livrat | înțelege jocul, nu înșală | regula ta |
| 2K nativ + subtitrări + miniatură editată | max calitate pe toate suprafețele | YouTube 2026 |

## 🛡️ PROTECȚIA COPIILOR (zero pierderi — implementată)

De-aia nu pierzi copii din clip:
1. **FINALUL ELASTIC**: editorul urmărește energia și TAIĂ episodul când povestea s-a terminat (nu la cronometru). Zonă moartă la final ≥12s → episodul se scurtează automat (min 90s). Mesaj în log: „FINAL ELASTIC 170→140s". (MrBeast: „tăierea bruscă protejează retenția".)
2. **Structura anti-pierdere**: hook la 0:00 din mijlocul maximului (nișa din primele 30s — acolo mor ~30% din spectatori, confirmat de MrBeast) + momentul maxim la ~2 min (re-engagement) + final brusc.
3. **Audit de retenție pe viitor**: zona moartă din episod e măsurată; următorul pas (Faza 3) = jump cuts pe liniștile din mijloc.

Live-ul îl descarci de pe canalul tău (Studio → conținut → live-uri → descarcă) sau cu yt-dlp.

## Ce primești în `episodes/`

| Fișier | Ce e |
|---|---|
| `EP01.mp4`, `EP02.mp4`… | Episoadele gata editate (~2:50) |
| `EP01_cadru1/2/3.jpg` | 3 cadre reale din MOMENTUL MAXIM → alegi 1 + pui logo în Canva = miniatura |
| `RAPORT.md` | Planul fiecărei povești: de unde e intro-ul, setup-ul, desfășurarea, momentul maxim |

## ⚠️ Regula de AUR: tu ești filtrul de calitate

Vizionezi TOATE episoadele înainte de upload (10 min/episod). De ce nu sari peste:
- în live se pot spune lucruri de verificat (secret de familie, dată personală, cuvinte care nu merg la copii)
- tool-ul aude ENERGIA, nu înțelege CONȚINUTUL — poate alege o explozie plictisitoare pe dinafară
- titlul e ȘABLON (`CE S-A ÎNTÂMPLAT PE POKECITY?! Ep. X`) — îl personalizezi tu după ce s-a întâmplat

## Câte episoade iese dintr-un live?

- **3h de live → tool-ul propune maximum 8; după filtrul tău rămân de obicei 4-8 tari.**
- NU le încarci pe toate deodată! Intră în sloturi: duminică 15:00 (slotul fix) + restul pe zilele de short / săptămâna următoare. Consistența > frecvența (confirmat 2026 oficial).
- Asta e piesa care lipsea din playbook-ul Nocivanu: el face 7,4 clip/săpt din volum; tu acum ai robinetul același, dar din live-urile pe care oricum le faci.

## De ce ~2:50 și nu fix 3:00

Ținta e 170s (2:50), elastic 2:45–3:15: MrBeast zice **taie când s-a terminat povestea, nu când s-a terminat cronometrul** — finalul brusc protejează retenția (a ta la lungi e 12,1%; tot ce facem aici țintește să o urce). Dacă vrei altă durată: schimbi `DURATA` în capul scriptului.

## Setările pe care le poți schimba (în capul `autoeditor.py`)

| Setare | Defaut | Ce face |
|---|---|---|
| `DURATA` | 170s | Lungimea episodului |
| `MAX_EPISOADE` | 8 | Plafon de siguranță calitate |
| `HOOK_INAINTE` | 15s | Cât înainte de explozie începe clipul |
| `MUZICA_VOLUME` | 0.12 | Volum muzică de fundal |
| `CTA_TEXT` | LIKE + comentarii | Textul de final |
| `NUME_CANAL` | iZentric | Semnătura în colț |

## 🎵 SUNETELE TALE — arunci cu nume normal, EU le aranjez (`sunete_mele/`)

Arunca fisierul .mp3/.wav DIRECT in `sunete_mele/` cu nume natural in romana — atat:
| Nume fisier | Unde ajunge |
|---|---|
| teava care cade, oase rupte, am cazut... | la CADERI (automat pe evenimentele reale) |
| bambus hit, lovitura, pumn... | la LOVITURI — dar MAX 2/episod ca sa ramana surpriza |
| l-am prins yay, am reusit... | la BUCURII |
| sting, frica... | la TENSIUNE |
| orice altceva | comice random (viata in episod) |
Optional/avansat: folder sau nume INTRARE/HYPE/EXPLOZIE/VICTORIE/FINAL = loc fix in episod.
Detalii in `sunete_mele/CITESTE-MA.txt` · Secretile de editare MrBeast: `SECRETE_EDITARE.md`.

## 🔊 CALIBRARE AUDIO YOUTUBE + 🎬 ZOOM-URI MrBeast (automate, pornite)

- **AUDIO**: fiecare episod e MASURAT si adus la **-14 LUFS** (standardul YouTube 2026 —
  YouTube normalizeaza la -14 si NU amplifica ce e linistit; masterul la -16 = episod prea incet
  fata de restul feed-ului). Metoda de studio: loudnorm liniar in 2 treceri (zero pompare),
  varfuri sub -1.5 dBTP. In consola/RAPORT vezi: „CALIBRARE YOUTUBE: -16.0 -> -14.0 LUFS". (AE_LUFS=0 opreste)
- **FLOW MrBeast (v3.13, calibrat pe JocuriHorror: 178 schimbari vizuale/19.8 min = una la 6.7s)**:
  cadrul „respira" permanent (oscilatie discreta) + punch-in la cold-open, HYPE, CLIMAX
  si la FIECARE varf real de energie (max 4) + aerul mort se taie de la 9s (inainte 12s).
  Frame-ul nu se mai opreste niciodata din miscare — ca la el.

## 🛡️ VEGHEAZA — isi ia live-ul SINGUR de pe canal (`vegheaza.py`)

```
python vegheaza.py            <- il lasi deschis; verifica la 10 min
python vegheaza.py --odata    <- o singura verificare (test)
```
Urmareste canalul tau (yt-dlp, FARA API key). Orice video nou mai lung de 15 min
(shorts ignorate) -> luat automat -> FLUX -> episoade in episodes/.
ATENTIE: prima rulare ia cel mai recent video lung existent = test perfect cu material real!
(ia deja testat pe canalul real: gaseste ultimul video, respecta memoria celor procesate)

## 📦 SETUP PE PC-UL TAU (3 minute, FARA GitHub)
1. Descarca `autoeditor_pokecity.zip` si dezarhiveaza-l (click dreapta -> Extract)
2. Deschide Command Prompt in folderul dezarhivat: `pip install yt-dlp`
3. Creeaza fisierul `.env` in `autoeditor/` cu o linie: `GEMINI_API_KEY=cheia_ta` (aistudio.google.com/apikey)
4. Atol:
   - `python vegheaza.py` lasat deschis = totul automat dupa fiecare live
   - sau `python flux.py <link-youtube>` cand vrei tu
Update-uri: cand zic ca am imbunatatiri, descarci zip-ul nou peste cel vechi (1 min). GitHub optional.

## 🚀 FLUX — AUTOPILOT COMPLET, o singura comanda (`flux.py`)

```
python flux.py https://www.youtube.com/watch?v=XXXX      <- VOD-ul tau de pe canal
python flux.py prindere/live_full.mp4                     <- sau fisierul local
```
1. INGHITE live-ul (descarca singur VOD-ul cu yt-dlp / sau ia fisierul local)
2. VIDEAZA TOT: Gemini analizeaza materialul intreg (sau selectie pe energie cu --fara-ai)
3. ALEGE singur momentele (regula ta: doar cele cu motiv de exista, 3-8 max)
4. SCRIE momente_auto.txt si LANSEAZA autoeditorul (2K + subtitrari + AI)
5. PRIMESTI in episodes/: episoade editate + titluri + miniaturi + kit upload

TU ai facut live-ul. De aici incolo e automat. (echivalentul „Ask Studio"-ului
din YT Studio — dar care SI CONSTRUIESTE episoadele, nu doar le analizeaza)
Testat E2E: o comanda -> moment ales -> episod randat ✓

## 👁️ PRIVESTE — Gemini VIDEAZA tot materialul (`priveste.py`)

```
python priveste.py https://www.youtube.com/watch?v=XXXX   <- VOD-ul tau de pe canal (zero descarcare!)
python priveste.py live_comprimat.mp4                     <- fisier local (pana la 2GB, File API)
```
Primești analiza COMPLETA (in `cunoastere/analize/` + consola):
- DESPRE CE e vorba · CE SE VEDE in joc (cu minute) · CE SE SPUNE (pe sectiuni)
- TOP momente pentru episoade: minut start + explozie + ce se vede/spune + scor + motiv de exista
- TITLURI per moment (doar ce se vede) + RISCURI de verificat (minute exacte)
- creierul canalului + regulile tale invatate sunt in prompt = analiza „ca un editor care te cunoaste"

Limita onesta: 2GB la fisier (File API) — dar VOD-ul tau public de pe YouTube merge DIRECT prin link,
deci live-urile lungi NU au nevoie de descarcare pentru analiza.

## 📱 PAL TELEGRAM — AI-ul canalului in telefon, oriunde esti (`pal_telegram.py`)

```
SETARE (3 min, o data):
1. Telegram -> @BotFather -> /newbot -> TOKEN -> in autoeditor/.env:
   TELEGRAM_TOKEN=...     TELEGRAM_USER_ID=...   (ID-ul tau: @userinfobot)
2. pe PC: python pal_telegram.py   (fereastra deschisa)
3. din TELEFON, oriunde in lume:
   „ce momente are live-ul?"  -> iti arata minutele + scorurile
   „vreau clip cu caderea"    -> recomandari concrete
   /momente · /randeaza · /status  -> controlezi randarea de la distanta
```
Botul raspunde NUMAI tie (filtru pe ID-ul tau). Foloseste acelasi creier
(autoeditor + Gemini). Testat: endpoint + taiere mesaje lungi ✓

### 🎓 /invata — AI-ul INVATA de la tine in timp real
```
TU (din telefon):  /invata titlurile sa aiba max 5 cuvinte
PAL:               INVATAT ✓ «titlurile sa aiba max 5 cuvinte»
                   Aplic de la URMATORUL clip.
```
- regula ta intra in `cunoastere/reguli.md` (cu data)
- autoeditorul o CITESTE la fiecare randare si o injecteaza in Gemini cu prioritate
- /reguli = vezi tot ce a invatat
- INVATA-TI BOTUL cat vrei — cu fiecare regula devine mai mult AL TAU. Testat cap-coada ✓

## 💬 PAL — vorbesti cu AI-ul inainte de randare (`pal.py`)

```
python pal.py prindere/live_full.mp4
TU:  vreau clip cu caderea din casuta, aia cu rasete
PAL: am gasit caderea la minutul 1:08 (scor mare) si cea de la 2:36.
     Recomand 1:08 — acolo zici „AM MAJORAT!" si rade toata echipa.
     Comanda: python autoeditor.py live.mp4 --momente momente.txt
TU:  fa asa
```
- PAL stie regulile canalului (creierul din cunoastere/), vede momentele cu scoruri
- cu faster-whisper activ, iti si CITEȘTE ce ai zis in jurul fiecarui moment
- îi ceri ce clip vrei, el îți arată minutele exacte + îți dă comanda gata

## 🧠 MODUL AI (cel mai bun) — `--ai`

```
python autoeditor.py LIVE.mp4 --calitate 2k --subtitrari --ai
```

**Ce face AI-ul în plus** (Gemini, gratis):
1. Pentru fiecare moment ales de „urechi", AI-ul **PRIVEȘTE 2 cadre + citește ce s-a vorbit** și dă scor 0-10: e cu adevărat tare pentru copii? sau doar zgomot?
2. Momentele slabe **cad** — rămâne mereu cel puțin cel mai bun (regula ta)
3. **Generază TITLUL personalizat** pentru fiecare episod (vezi `episodes/titluri.txt` + RAPORT)

**Setare (1 dată, 1 minut, GRATUIT):**
1. Intri pe `aistudio.google.com/apikey` → „Create API key" → copiezi
2. Creezi fișierul `autoeditor/.env` cu linia: `GEMINI_API_KEY=cheia_ta`
   (exemplu gata: `.env.example` — doar redenumești și lipești)

**Arhitectura (de ce e cel mai bun combo):** „urechile" locale (fast, nelimitate, gratuite) găsesc TOATE momentele → „creierul" AI (Gemini) le judecă semantic → tu ești filtrul final. Niciun tool plătit nu face asta pe nișa ta.

**GARANȚIA TITLULUI (promis = livrat):** AI-ul generează titlul DOAR din ce chiar se vede/se aude în moment + listează ce promite + confirmă că tot e în material. Dacă promite ceva ce nu apare → **recalibrează singur titlul** (al doilea apel, mai strict). În RAPORT vezi „PROMIS=LIVRAT OK" + un **CHECKLIST** per episod: titlu · scor moment · sunete puse · confeti · texte engagement · durată exactă. Nicio promisiune neplinită către copii.

**Comparație onestă (09.2026):**
| | Al nostru + AI | Eklipse.gg | Opus Clip |
|---|---|---|---|
| Preț | 0 lei | $0 cu FILIGRAN+720p / $15-25/lună | $19+/lună |
| Pentru gaming/copii RO | Da — antrenat pe regulile tale | Da, dar generic | Nu (vorbit/cast) |
| Structura-POVESTE + textele de engagement | Da | Nu (taie doar) | Nu |
| 2K la export | Da | 1080p max la platit | Da |
| Titluri AI personalizate | Da | Nu | Scor de viralitate |
| Limite | PC-ul tău | clip-uri/lună la gratuit | 60 min/lună gratuit |

## Faza 3 (după 2-3 live-uri cu v2.3)

1. ~~Efecte sonore pe sloturi~~ ✅ GATA (v2.2)
2. ~~Subtitrari AI~~ ✅ GATA (v2.3)
3. **Tăieturi pe liniști** (jump cuts) — ritm mai rapid
4. **Titlu + descriere + tag-uri generate din transcript** — per episod
5. **Boost din chat-ul live** — minutele cu chat furios cântăresc mai mult
6. **Pachete sezoniere pre-făcute**: halloween/craciun cu sunete + logo schimbat (folderul exemplu există deja)

## Limite oneste (ca să știi)

- **Nu încarcă singur pe YouTube** — upload-ul prin API arde cota zilnică întreagă (1.600u/episod). Tragi fișierele în Studio, 1 minut.
- Aude energia, nu înțelege umorul — de-aia review-ul tău rămâne obligatoriu.
- Pe un PC normal: analiza ~1-2 min/oră de live; randarea durează cam cât episodul (un episod de 3 min ≈ 3-5 min de așteptare).
