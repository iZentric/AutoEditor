# Caută melodiile, efectele și meme-urile dintr-un video

`sunete_referinta.py` primește un **link direct la un videoclip YouTube** sau un fișier local și creează un raport Markdown cu:

- evenimente audio descrise de Gemini, cu timpi aproximativi — muzică de fundal, SFX, meme-uri și ambianță;
- identificări de melodii prin amprentă audio AudD, dacă este configurat tokenul opțional;
- potriviri orientative cu efectele audio aflate deja în `sunete_mele/`, `sunete_virale/` și bibliotecile locale;
- căutări YouTube pentru etichetele găsite și linkuri către căutări Freesound/Pixabay;
- linkuri Spotify/Apple Music/YouTube pentru piesele recunoscute.

## Pornire

```sh
python -m pip install -r requirements.txt
python sunete_referinta.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

Raportul apare în `episodes/SUNETE_<id>_<data>.md`, folder ignorat de Git. Pentru un fișier local:

```sh
python sunete_referinta.py "C:\Video\referinta.mp4"
```

Opțiuni utile:

```sh
python sunete_referinta.py URL --output raport.md
python sunete_referinta.py URL --max-ai-chunks 240 --max-music-checks 180
python sunete_referinta.py URL --no-web-search
```

Căutarea automată YouTube citește doar titluri și linkuri prin `yt-dlp`; nu descarcă fișierele rezultate.

## Configurare pentru identificare

1. **Etichete audio / efecte:** setează `GEMINI_API_KEY` local, în variabila de mediu sau în fișierul `.env` ignorat de Git. Se poate configura `GEMINI_AUDIO_MODEL`; în lipsă sunt folosite modelele din `GEMINI_MODEL`.
2. **Numele exacte ale melodiilor:** setează opțional `AUDD_API_TOKEN` în mediul local sau în `.env`. Obține tokenul direct de la [AudD](https://audd.io/); verifică acolo condițiile și limitele actuale ale planului.
3. Nu pune chei în cod, în GitHub Issues, în chat sau într-un fișier comis. **Nu urca `.env` în Git.**

Fără `GEMINI_API_KEY`, raportul nu are descriere AI a efectelor. Fără `AUDD_API_TOKEN`, nu se poate confirma automat titlul exact al piesei: modelul poate doar descrie ce fel de muzică aude. Căutările web și linkurile sunt separate de recunoașterea exactă.

## Ce înseamnă „exact” aici

- AudD compară probe audio de maximum 20 de secunde cu catalogul său și poate întoarce artistul/piesa. Timpii indică probele în care a fost recunoscută melodia, nu începutul garantat la milisecundă.
- Pentru SFX/meme-uri, instrumentul compară amprenta fragmentului cu fișierele locale din bibliotecă. Un rezultat este doar o **potrivire probabilă** și trebuie ascultat. Nu există o bază universală care să permită identificarea garantată a oricărui efect de pe internet.
- Când efectul nu este în biblioteca locală, raportul descrie sunetul și caută rezultate similare. Titlul/thumbnail-ul unui rezultat sau asemănarea numelui nu dovedesc că este același fișier.

## Acoperire, confidențialitate și licențe

- Sursa YouTube este limitată la un singur videoclip public; yt-dlp ia doar pista audio. Video-urile private, restricționate sau indisponibile pot eșua.
- Audio-ul este normalizat pentru a scoate în evidență pasajele liniștite și analizat în fragmente de 60s cu suprapunere de 10s. Se procesează cel mult 180 de fragmente Gemini implicit. Recunoașterea muzicii folosește probe suprapuse de 20s, cel mult 120 implicit. La clipuri foarte lungi, folosește plafoane mai mari și verifică acoperirea din raport.
- Fragmentele audio sunt trimise către Google/Gemini pentru etichetare. Dacă ai setat AudD, probe audio de până la 20s sunt trimise și către AudD pentru recunoașterea pieselor. Videoclipul complet nu este trimis acestor servicii de către acest script.
- Nicio piesă/efect găsit online nu este descărcat automat. Rezultatele YouTube, Freesound și Pixabay **nu au licența verificată**. Deschide pagina sursei și verifică dreptul de folosire înainte de a-l pune într-un video public.
- Normalizarea ajută în pasaje liniștite, dar nu poate separa perfect muzica foarte încetă de voce sau de alte sunete. AI-ul și serviciul de recunoaștere pot rata, confunda sau descrie greșit sunete. Ascultă manual pasajele indicate.
- Fișierele audio intermediare sunt temporare și se șterg după rulare; fișierele originale din biblioteci rămân nemodificate.
