# 🎯 CLICKBAIT OVERLAY COMPOSITION & PLACEMENT ENGINE — EXACT POSITIONS (LEGE, 06-10)
> Directivă boss, trimisă de 2×. SE APLICĂ PE FIECARE THUMBNAIL. Fără împrăștiat elemente la întâmplare.

## 1. BULA DE TEXT (Speech Bubble)
- Ancorată DIRECT lângă gura/fețele personajului principal (top-center sau top-stânga, lângă cap).
- Coada bulei arată DIRECT spre gura personajului.
- Stil: bulă albă de comic cu contur exterior gros negru.
- Text: roșu bold (gradient sau solid) cu contur negru: „CE?", „BĂĂ", „FUGI", „NU", „SST!".
  → LA NOI: se folosesc DOAR bulele EXACTE ale lui JH din `elemente_brand/JH_1LA1/TOATE/ALESE/`.

## 2. SĂGEATA ROȘIE 3D
- Pornește DIN bulă sau DIN personaj → arată DIRECT la punctul focal/monstru/misterul din scenă.
- Stil: roșu aprins 3D, contur interior alb curat, umbră neagră GREA (drop shadow).
- Direcție: NICIODATĂ spre exterior; mereu spre entitatea/acțiunea principală.

## 3. CERCUL ROȘU DE EVIDENȚIERE
- Încadrează un detaliu ascuns/misterios/crucial din midground/background (monstru ascuns, obiect secret).
- Legătura cu săgeata: DACĂ există cerc, săgeata arată DREPT în/el.
- Stil: cerc-țintă cu inel dublu roșu aprins, contrast luminescent.
  → LA NOI: `cerc_rosu_golit_JH.png` (inel 1:1 JH, gol pe interior) sau cercurile din ALESE/.

## 4. STIVA DE STRATURI (față→spate)
- STRAT 1 (față): bulă + săgeată + cerc.
- STRAT 2: personajul principal (stânga, față zoom, poză de reacție).
- STRAT 3: subiectul secundar / monstrul / acțiunea (dreapta).
- STRAT 4 (spate): mediul de joc (lume MC / pădure horror / cameră) = ORIGINALUL, neatins.

## 5. INTEGRARE VIZUALĂ & LOGICA POZEI
- Gesturi: dacă personajul arată cu degetul (ex. spre dreapta), săgeata/subiectul ALINIAZĂ cu direcția degetului.
- Bula NU acoperă ochii personajului și NU acoperă fața monstrului. Toate elementele cheie vizibile, fără aglomerație.

## ✅ CHECKLIST ÎNAINTE DE LIVRARE
□ coada bulei = pe gura personajului □ săgeata pornește din bulă/personaj □ săgeata intră în cerc
□ cercul încadrează entitatea din midground □ umbra neagră la săgeată □ straturile 1-4 în ordine
□ originalul neatins în afara personaj+brand (verificare 0 pixeli) □ nimic nu acoperă ochi/fețe cheie

## 🚫 COLLISION & STACKING FIX (LEGE, 06-10, directivă boss)
1. FĂRĂ SUPRAPUNERE între bulă/săgeată/cerc — minim 50px distanță între elementele de overlay.
2. Bula se ancorează la personajul care VORBEȘTE/REACȚIONEAZĂ (cel speriat, stânga);
   coada → gura LUI, niciodată spre monstru.
3. Cercul DOAR pe amenințare (cuțit/fața stalk-erului ascuns). Săgeata PORNEȘTE în afara ariei
   bulei → spre amenințare/cerc; corpul săgeții rămâne ÎN SPATE relativ la text (text 100% lizibil).
4. Centru CURAT între personaje — acțiunea (cuțitul) se vede instant.
   → Validat pe thumbnaili/THUMB_YTARI_FINAL_v6 (0 pixeli original modificați).
