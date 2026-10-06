# PROTOCOL MINIATURI — BRANDUL iZentric (LEGE, nu se încalcă niciodată)
> Stabilit cu bossul 06-10-2026. Sursa de adevăr: `refs/BRAND_THUMB_MASTER.png` (aprobat de boss).
> Referințe de stil canale: @dagar-minecraft + UC8EkcHOycB94lHDkbAPSnQA + @nacho-minecraft.

## CE TREBUIE SĂ ARATE ORICE MINIATURĂ (esența de brand, la ORICE joc)
1. **Stil**: desen cartoon-Minecraft cu CONTUR GROS negru, cel-shading lucios, culori
   hiper-saturate (cer cyan, iarbă neon), fețe expresive exagerate — „editat de om, nu AI".
2. **PERSONAJELE CANALULUI** (aceleași în fiecare thumbnail):
   - **iZentric** = băiat Minecraft cu păr jumătate negru/jumătate alb, coarne roșii mici,
     hanorac alb cu yin-yang negru.
   - **Mocivanu** = personaj urs Minecraft cu șapcă roz-albă, echipament roz/alb.
3. **NAMETAG-URI Minecraft** deasupra capului FIECĂRUI youtuber: box gri semi-transparent
   + text alb pixelat (Monocraft) cu numele canalului. Nu acoperă fețele.
4. **BULA cu text SCURT** (elipsă albă, contur negru gros, text roșu bold): „FUGI!", „CE?",
   „NU!", „SST!", „BĂĂ" — un cuvânt, exact ca la master.
5. **CERCUL roșu gros** pe elementul-mister + **SĂGEATA roșie groasă** dinspre un colț.
   ÎNTOTDEAUNA. (Varianta Cadres 31M: contur roșu întrerupt în jurul personajului + inimioare,
   FĂRĂ text.)
6. **Logo-ul SERIEI** într-un colț curat — DOAR când e din serie.
7. **Finisaj uman**: saturație +10%, contrast +5%, claritate +25%, test 120px telefon.

## 📍 REGULI DE PLASARE (lege de la boss, 06-10-2026 — „să pară editat de om")
1. **BULA stă LÂNGĂ caracter, NICIODATĂ pe fața lui.** Se pune în dreptul capului, pe o parte
   (stânga sau dreapta, în funcție de spațiul liber), și se ÎNTOARCE cu coada spre caracter —
   să pară că el zice cuvântul. Dacă e nevoie: `:stanga` la `--balon` o întoarce.
2. **CERCUL se pune MEREU PE FAȚA / PE OBIECTUL care trebuie arătat** — centrat pe el, nu
   pe lângă, nu „aproximativ". Comanda `--cerc-pe x0,y0,x1,y1` îl centrează singur pe casetă.
3. **SĂGEATA vine dintr-un COLȚ și arată spre subiect** (caracter sau obiect), rotită singură
   cu `--sageata-spre CALE:tx,ty:latime:colt` (colț: sj / dj / ss / ds).
4. Săgeata, cercul și bula sunt **luate 1:1 de la JocuriHorrorSky** (`elemente_brand/JH/`),
   niciodată desenate și niciodată regenerate. **Singurul lucru generat = personajele.**
5. Dacă un element nu e „exact ala de la el", NU-l folosi: se cere altul din hartă
   (`preview/harta.html` → bossul arată căsuța) și se taie din original.

## FLUXUL (agentul îl face singur, fără să întrebe)
1. **Alege referința inteligent** (SMART MATCHING): Minecraft → canalele campionilor
   (dagar/nacho/Cadres/Knoxy, baza în cunostinte/); alt joc → top youtuberul ACELUI joc
   (horror → JocuriHorrorSky). Alege viralul cel mai potrivit temei.
2. **Swap pe modelul 1:1** din refs/brand_1la1/ — NU regenera (vezi PROTOCOL_THUMB_SWAP.md):
   schimbi DOAR personajele, bulele/cercurile/săgețile rămân CE SUNT în model.
3. Dacă totuși scena se generează: FĂRĂ TEXT în AI — elementele se lipesc pe strat
   din `elemente_brand/` (PNG oficiale) sau tools/thumb_brand.py.
4. **Verifică**: toate elementele 1-7 prezente? Test 120px? Dacă lipsește ceva → refă.

## ELEMENTELE OFICIALE (folderul elemente_brand/)
bula_FUGI.png · bula_GOLA.png (fără text) · nametag_iZentric.png · nametag_Mocivanu.png ·
cerc_rosu.png · sageata_rosie.png · inimi_rosii.png — extrase din masterul aprobat.
