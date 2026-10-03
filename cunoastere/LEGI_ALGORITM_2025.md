# LEGILE ALGORITMULUI 2025/2026 — SYNTAXĂ COMPLETĂ (upgrade editor 29.09)

Surse: studiu Paddy Galloway 3.3 mld shorts, YouTube Analytics (post-martie 2025), analize
MrBeast thumbnails, ghiduri retenție-editing. Aplicate canalului PokeCity.

## 1. CE MASURĂ ALGORITMUL LA SHORTS (funnelul real)
| Etapă | Metrică în Studio | Țintă | Ce înseamnă |
|---|---|---|---|
| arătat în feed | Shown in feed | — | reach-ul brut |
| **hook (0–2s)** | **Viewed vs Swiped Away** | **70–90% viewed** | <60% = hook moartă, distribuția se oprește |
| comitment | Engaged views | max | baza de monetizare (nu views!) |
| ținut | APV (avg % viewed) | **>100% (LOOP!)** | fiecare replay = încă un view |
| satisfacție | like/comment/share | ~1 like/160 views | semnale de împins |

- Din martie 2025: ORICE playback = view; fiecare LOOP = view nou. **Shortul care se buclează își triplează singur view-urile.**
- Swipe mediu: ~5.8s. Cine trece de sec 5 are cu 60% mai puține swipe-uri.
- Fețe/reacții în short = +28% engagement.

## 2. LEGILE EDIT-ULUI DE RETENȚIE (aplicat pe 16s)
1. **HOOK 0–1s**: ACȚIUNE sau OBIECT-CHEIE vizibil DIN CADRUL 0 (nu salut, nu context).
   Confirmi clickul: ce promite titlul se VEDE în sec 1.
2. **Pattern interrupt la fiecare 3–5s** (echivalentul 10–15s pe long): tăiere pe moment
   vizibil NOU, zoom, pop, sfx. Atenție la over-editing: editul susține povestea, nu o înlocuiește.
3. **Fără pauze >0.3s fără eveniment** — tăi aerul mort. Tăieturile CAD pe capăt de frază.
4. **Pop-urile cad PE evenimentul VIZIBIL din joc** (nu pe transcript!) — verificare
   cadru-cu-cadru OBLIGATORIE înainte de livrare (filmstrip 1 cadru/s).
5. **SFX pe mișcări/impacturi = cel mai ieftin pattern interrupt.** Max 6/short, niciunul la 0.0s.
6. **LOOP la final**: ultima scenă trebuie să se POATĂ lega de prima (acțiune în mișcare,
   nu "final de poveste static"). Finalul care închide = replay 0.
7. **Capitane galbene sincronizate cuvintele** cresc watch-through ( monitorizezi cu
   verifica_subs_vizibile — sub prag NU se livrează).

## 3. LEGILE THUMBNAIL (MrBeast, 5 patternuri)
1. Un singur subiect clar — se înțelege în 0.3s (attenția umană = 0.3s la primul ochi).
2. Față cu O emoție singură, exagerată; fața ≥40% din înălțimea thumbnail; lizibilă la
   40% luminozitate de la 5m. SURPRIZA = top pentru gaming.
3. Un NUMĂR/miză în cadru, mare (≥80px pe 1280x720), culoare contrastată cu fundalul.
4. Contrast/saturație pentru ecran de telefon; "frumos" pierde în fața "lizibil".
5. Text 2–4 cuvinte MAX, bold sans, contur OBLIGATORIU; textul NU repetă titlul —
   adaugă informație NOUĂ. Dacă nu adaugă → zero text.
+ Safe zone: colțul dreapta-jos e acoperit de timestamp pe mobile — nimic important acolo.
+ Primul thumbnail e aproape niciodată cel final: CTR sub media canalului după 24–48h →
  schimbi (A/B). Test de lizibilitate: redus la 168×94.

## 4. LEGILE TITLU + DESCRIERE + HASHTAG (shorts)
- Titlu: 60–80 caractere, cuvântul-cheie ÎN PRIMELE 30, FĂRĂ hashtag în titlu.
- Descriere: hook în primele 100 caractere, 150–300 caractere total, apoi 3–5 hashtaguri
  la FINAL (primele 3 apar deasupra titlului). #Shorts inclus. Max 60 (sub 60 = OK, 15+ risc).
- Tag-uri (Studio): 5–15 fraze-cheie, 200–400 caractere, broad→nichă→exact.
- Regula noastră JH/iSilent rămâne: CAPS, fără diacritice, persoana I sau întrebare bombă,
  clickbait cu miezul REAL.

## 5. CHECKLIST AUTOMAT (short_qc.py)
durata 16±0.1 | 1080x1920 fps>=30 | LUFS −14±0.5 | subs vizibile pe toate popurile |
pops 3–6, niciuna înainte de 0.2s, gap ≥1.2s | logo vizibil sus-dreapta (cadre salvate) |
primer cadru = hook (salvat pt. verificare vizuală) | potențial de loop (Similaritate
primul/ultimul cadru — raportat).

## 6. CE NU SCHIMBĂM (legile creatorului rămân)
16s exact | logo POKECITY sus-dreapta permanent | pops galbene contur gros jos | −14 LUFS |
1 short/zi | FĂRĂ confetti | FĂRă zoom default | titluri stil JH/iSilent.

## 7. RUNDA 2 (03.10, deep-dive) — COMPLETĂRI
### Hook (5 arhetipuri, primul element la 0.5s)
bold claim / curiosity gap (se închide ABIA la final!) / micro-story / visual shock /
direct question. Combinația câștigătoare (47 teste A/B): pattern interrupt + curiosity
gap DESCHIS + specificitate emoțională = 82% retenție@3s vs 41% cu un singur element.
Poziția: hook arc 3–6s, prim cuvânt/cadru la 0.5s, FĂRĂ intro/muzică/salut.
### Capte animate (KINETIC = standardul industriei)
78.6% din top clips folosesc capte ANIMATE vs 1.6% statice; word-pop = +40–80% AVD;
80–85% din feed privește FĂRĂ sunet → captele nu-s opționale. Stilul nostru: pop-in
fade 120ms + scale bounce 115→100 (implementat în scrie_ass_pops, stil short).
### LOOP (mecanică, nu noroc)
- seam test OBLIGATORIU: ultimele 3s jucate pe rând cu primele 3s — trebuie să curgă.
- final = în MIJLOCUL acțiunii sau mișcare care continuă în cadru 0; ZERO card final,
  zero "thanks for watching", zero CTA vorbit (CTA mergi în descriere).
- audio bridge: beat/sunet care trece peste punctul de buclă (fără tăcere la 15.8s).
- 7–15s = zona de rewatch maxim; noi suntem la 16s — finalul decis în consecință.
### Punch-in (zoom) — disciplină
DOAR pe eveniment (prindere/reveal/explozie), k=0.93, NICIODATĂ pe fiecare replică
(over-editing scade retenția; audiența copil tolerează mai mult ritm, dar nu zoom spam).
Helper: short_qc.punch(). Changere vizibilă la fiecare 3–5s = suficient.
### Fereastră de investitție 3–15s
Confirmi promisiunea hookului în primele 5s; open loop mic la ~8–12s ("dar uite ce-a
făcut după.."); rezoluția doar la final.
