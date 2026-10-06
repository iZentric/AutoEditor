# FORMULA "1 LA 1" — disecție JH-Sky + iSilent + Dagar + Klorna (+ canal 5 = 404/mort)
## SHORTS (din cadre reale hq1-3):
- DAGAR (3.9-11M views!): Minecraft full-screen vertical, avatarul CENTRAT MARE, captions ALBE
  contur negru SUS-centru PERMANENTE (2-3 cuvinte), text CTA-n-ecran ("DALE LIKE AL VIDEO",
  "PARA VER ME SUB") în primele 1-2s, poveste într-un singur cadru fara taieri.
- JH-SKY (873K, 781K, 400K): FAȚA REALA mare + fundal blur din gameplay + reactions.
  Hook VIZUAL în sec 1 (schelet la volan!). Captions albe mici jos.
- iSILENT (288K, 271K): același: față + blur + captions simple; titluri "CE ARE X?".
- KLORNA (1.7M): față + joc + captions; IRL food = alt niș.
- REGULĂ COMUNĂ: [cuvânt-cap-tare] în titlu + întrebare/curiozitate; primele 2 cadre =
  momentul CEL MAI tare, nu intro.
## VIDEO LUNGI (miniaturi):
- FAȚA reală ȘOCATĂ (gura deschisa) 40% + element de joc 60% + SĂGEATĂ ROȘIE + 1-2 cuvinte
  CAPS ("CE?", "BĂĂ", "EU") + fundal saturat.
- iSilent: personaj cartoon + obiect-real; Dagar: skinuri mari colorate (roșu vs albastru).
## CORECTIE BOSS: subtitrarile JH-Sky = GALBENE (confirmat pe 8 shorturi: "Ce vrei sa devii
## cand", "Fiert sau nu") jos-centru, permanente, max 2-3 cuvinte.
## APLICAT ÎN editor_pro.py (clone 1:1):
1. captions albe->galben-active SUS (y=445) cuvinte-sloturi separate (Dagar-style)
2. "DA UN LIKE!" roșu jos în primele 2s (echo "DALE LIKE")
3. hook SUS + big-word roșu la vârfuri + CTA jos
4. shake+SFX+drone ducked + logo serie dreapta-sus
5. STREAMING renderer (26s/short, memorie constanta - NU ffmpeg 21-input!)
6. INTELIGENTA MAXIMA (autopilot): masoara ENERGIA vocii pe fiecare cuvant -> singur alege
   punch-words (energie >1.45x mediana), BIG-WORD rosu (vârful de energie), hook-ul din
   primele cuvinte, si genereaza KIT-ul de upload. Doar input: video + moment.
7. ffmpeg = autodetect (apt, apoi pip imageio-ffmpeg; NU in workspace - ar fi 77MB!)
## CULORI VIILE (confirmat de cercetare net + disectie 25 shorturi JH):
- GALBEN SATURAT (255,230,0) = baza captions, jos, permanent, contur negru gros (Hormozi
  style = "yellow high-energy"; JH foloseste galben pe ~80% din cuvinte)
- ROSU SATURAT (255,45,35) = cuvintele-PUTERE (energie voce >1.45x mediana + top-2 globale;
  minim 2 pe short) + BIG-WORD la vârf. JH: "SANTA?", "S-A IUBIT" in rosu.
- Marime: 100px baza, active 1.18x, punch 1.22x (standard 70-100px, max cap 100px)
- Emoji mare in cadru la mom. comice (JH: zambet galben mare) = de adaugat la nevoie
- 1396 shorturi are JH total; sample disecat: 25 (toate cu galben/rosu/VIU, niciodata alb plat)
## v5 REGULI NOILE (corectii boss):
- LOGO DOAR daca contentul e din serie (series='pokecity'); NICIODATA logo degeaba
- AUTO-PACING: taie liniile (prag = 1.5x p25 RMS) -> zero secunde moarte (9.6s->8.1s demo)
- find_best_window(): alege fereastra cu energie maxima din clipuri lungi
- BUG FIX istoric: overlay body = bg baza + fg peste (inversul dadea 1030x580 si crack la 72 cadre)

## v7 SUNETE REALE VIRALE (cerere boss: "sunetele din github"):
- sursa: github.com/AVTAVANTTOUT2/meme-sound-effects (37 sunete din compilatia "Modern Meme SFX")
- INSTALATE in pro/: boom=VINE BOOM (cuvantul-putere!), drone=PROWLER (tema fundal), riser=SUSPEND,
  whoosh=YEET + extra: metal_pipe, heheheha, boowomp, bass_drop (pentru shorturi comice)
- M3 "MARIA" = ANULAT de boss (nu se intelege). LECTIE LOCKED: fara poveste clara confirmata, nu montam.
- Doar WAV-urile raman in pro/ (mp3 sterse, buget).
## v6 (cerere boss explicita):
- CTA "EPISOD COMPLET PE CANAL" = SCOS DEFINITIV (arata ieftin; ei nu-l folosesc)
- TITLURI = formula "VREAU SA VAD IN CONTINUU": narațiune întrerupta (JH: "EL M-A RAPIT!",
  "NU te duce in Padurea lui..", "Tatal STRICT are PLANURI cu EMILIA..") = actiune caps +
  puncte de suspension + intrebare in comentarii. KIT-ul autogen foloseste exact asta.
- Shorturi reale: SHORT_M7_LOBBY (8.1s). M3 MARIA = ANULAT de boss (nu se intelege povestea!) - LECTIE din nou: fara context clar de la boss, nu montam

## v8 FORMAT LUNGI JH (disectie 16 videolungi) + SUNET INTELIGENT:
- SET JH long-form: helmet-cam STANGA (fata lui mereu vizibila 20-25%) + joc full + subtitrari
  GALBENE in zona de jos a jocului + POP-OUTuri (badge ALB rotit, elemente care IES din video)
  doar la momentele tari + etichete ECHIPA ROSU/ALBASTRU la competitii
- POP-OUT implementat: badge alb rotit -4grade, contur negru, umbra dura — DOAR pe big-word
  (unul singur/short, nu imprastiat — regula boss: "elementele cand trebuie, inteligent")
- SUNET INTELIGENT (nu random): boom=cuvant-putere | riser=build-up | whoosh=start |
  metal_pipe=cadere energie (fail detect de audio!) | heheheha=moment comic | boowomp=strange |
  bass_drop=dupa tensiune. Fiecare efect are CONTEXt semantic.
- fail-detect audio: caderi bruste de energie (>65% drop) = fail in joc -> metal_pipe
## v9 PROIECT boss GitHub (iZentric/AutoEditor): REPO NU EXISTA public (404) - dupa ce-l
## face public, il sincronizam cu editorul de aici.

## v9 MOTOR NOU (cererea boss: proiectul auto-editor):
- auto-editor (WyattBlue, 5.4K stars) = MOTORUL de taiere (inlocuieste RMS-ul meu):
  `auto-editor seg.mp4 --edit (audio:threshold=6%) --margin 0.12sec` + RE-WHISPER pe clipul
  taiat (timpii direct in timeline). Cazut pip: `pip install auto-editor faster-whisper` la reset.
- CAPTIONS ORDONATE (regula boss "nu dezordonat"): sloturi FIXE, zero scale/zoom — DOAR
  culoarea + grosimea conturului difera: GALBEN=rest, ALB=cuvantul vorbit, ROSU=putere.
  Exact ca la JH (de-asta ale lui nu sar prin ecran).
- Token cleanup whisper: fragmente cu '-' lipite la cuvantul anterior, litere singure aruncate.
- BUG FIX: streaming reader = probe_dims() (dimensiuni REALE, nu prezumate) — altfel broken pipe.

## v10 DISIECTIE CU NUMARATOARE (3 TOP shorturi JH descarcate + masurate):
- 1prBeHAc9rE SPIDERMAN 1.2M: 17.5s, 3 taieri, vorba continua RMS 0.17-0.46, ~9 schimbari vizuale
- EbmHbIGDX7c GHICIT 1M:      18.2s, 1 TAIE,     RMS 0.11-0.39, 12 schimbari (caption/zoom ~1/1.5s)
- lNZg0SLqPMw MASINA 874K:    12.4s, 5 taieri,   RMS 0.04-0.44, 8 schimbari
## LEGI MASURATE: DURATA 12-18s | UN PLAN CONTINUU (0-5 taieri) | VOCEA NU TACE NICIODATA |
## 1 schimbare vizuala la ~1.5-2s | punch-urile lor cad pe RMS peaks (0.36-0.46)
## REPRODUCERE: SHORT_REPRODUCERE_78.mp4 = M7+M8 (19s brut) -> auto-editor 5% -> 12.66s
## (in intervalul lor!), pop-out MAXIMUL! pe vârf de energie, vorba continua 0 goluri.

## v11 REPRODUCERE FINALA 1:1 (dupa script+cadru disectat de la JH MASINA 874K):
- STRUCTURA lui: sec0-2 GOL (fara text!) -> captions MICI intrebare (Ce e aia frate?) ->
  ZOOM detalii -> REVEAL (schelet). Captions lui = 64px MICI, 3-4 cuvinte, contur subtire.
- APLICAT: captions 64px sp18, hook OPTIONAL ('' = incepe gol ca la el), auto-editor retry
  5/8/12% + sintaxa corecta '--edit VAL' (= sparge parser!)
- REPRODUCERE: 19s -> 12.66s, incepe gol, captions mici, MAXIMUL! = singura explosie (pop-out)
- BUGURI FIX: auto-editor se dezinstaleaza la reset (pip install auto-editor) + silent fallback

## v12 REGULA #1 ABSOLUTA: NICIODATĂ ACELAȘI SHORT/MATERIAL DE 2 ORI.
- Shorturile vechi deja-livrate = ȘTERSE din workspace ca sa nu mai pot re-livra (boss a primit
  aceleași shorturi repetat = EROARE GRAVĂ). Vezi REGULI_BOSS.md (lista live + materiale epuizate).
- /momente/ = EPUIZAT complet. Fără materiale noi de la boss = ZERO shorturi noi.
