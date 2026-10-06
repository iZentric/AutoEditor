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

## 👑 REGULA DE AUR (bătută în cuie de boss, 06-10-2026)
„Ai făcut ASTA — a fost PERFECT. Regulile să rămână exact asta."
→ Orice thumbnail de acum înainte trebuie să arate EXACT ca `refs/BRAND_THUMB_MASTER.png`.
**CHECKLIST FINAL înainte de livrare (compari cu masterul, element cu element):**
- [ ] Bula albă cu contur negru gros + text roșu scurt („FUGI!"/„CE?" — UN cuvânt)?
- [ ] Nametag-urile Minecraft (Monocraft, box gri) deasupra FIECĂRUI personaj, pe nume?
- [ ] Cercul roșu gros pe elementul-mister (bebelul/obiectul), centrat?
- [ ] Săgeata roșie groasă din colțul liber, cu coadă rotundă, spre țintă?
- [ ] Logo-ul seriei în colț (POKECITY stânga-jos) — DOAR la serie?
- [ ] Personajele EXACT ale noastre: iZentric (jumătate negru/alb, coarne, yin-yang) + Mocivanu (urs, șapcă roz-albă)?
- [ ] Stil cartoon-Minecraft cu contur negru gros, culori săturate, fețe exagerate = „editat de om"?
Dacă un singur punct lipsește → NU se livrează. Refă.
PNG-urile oficiale sunt în elemente_brand/ — folosești ACELEA, nu improviezi altele.
