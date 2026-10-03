# LEGI ALGORITM SHORTS 2026 — cercetat 30.09 (surse: nexora-ai, vexub, clipiq, shortimize, vidiq, capcut, automateed, shortzly, quso, creamate/blitzcut safe-zones, flowshorts/thumbnailmakerr/conbersa frecventa, kreateflo/inbeat/zebracat statistici)

## 1. CUM DISTRIBUIE ALGORITMUL (test-and-expand)
- Fiecare Short e testat pe o AUDIENȚĂ-SĂMÂNȚĂ mică; fereastra de decizie: **primele 30–60 min**.
- Semnalul #1: **SWIPE-RATE** ("Viewed vs Swiped away"). Nu există click/thumbnail — totul e decizia „swipe sau stay" din **primele 1–3 secunde**.
 Țintă: **≥75% viewed**; sub 50% = hook-ul a murit, distribuția se oprește.
- Apoi **hook retention** (primii 30% din video urmăriți) și **avg % viewed**: >60% = distribuție continuă; **>80%** = Suggested/shelf.
- **REWATCH (loop)** = cel mai puternic semnal pozitiv. Vârf de retenție la final = loop reușit.
- Engaging ulterior (like/coment/sub) cântărește; **74% din views vin de la non-abonați**.
- Din ian 2026 Shorts apar în **SEARCH** separat → cuvinte-cheie în titlu/descriere = canal nou de descoperire.
- Conținut cu watermark de altă platformă / inautentic = demote/demonetizat (noi: gameplay original = OK).
- Medie de retenție pe Shorts: **73%** — tot ce livrăm trebuie să țintească ≥70%.

## 2. LEGI DE MONTAJ SHORT (din cercetare, aplicate în motor)
1. **HOOK ≤1.5s**: prima valoare/acțiune vizibilă până la 1.5s; primul pop ≤0.6s; **≤7 cuvinte** pe primul pop.
2. **Prima secundă = MIȘCARE** (subiect/actiune, nu peisaj) — automat în motor: `verifica_hook()` (refuză short static).
3. **MICRO-CUTuri** 0.4–1.2s în primele 2–3 cadre, apoi tăieturi la 3–5s; **pattern-interrupt la 5–8s** (sfx nou, zoom pe acțiune, pop).
4. **FARĂ AER MOART**: J/L-cuturi, whoosh între idei; niciodată tăcere >1s fără eveniment.
5. **LOOP ENGINEERING**: ultimul 0.5s să semene cu cadrul 1 (oglindă vizuală) SALE tăi cu o bătaie ÎNAINTE de rezolvare (mijloc de frază la comedie) → rewatch. Vârful de retenție la final = loop bun.
6. **PAYOFF la 60–80%** din durată (la 16s: între 10–13s); „SE DĂ..." nu se anunță, se vede.
7. **TESTUL MUT**: privești primele 5s fără sunet — trebuie să înțelegi subiectul (pop + acțiune vizibilă).
8. **SAFE-ZONE 1080×1920**: jos ~320px (titlu+canal), dreapta ~150px (rail), sus ~160px (iconițe), stânga ~60px.
   → pops pe **MarginV 340** (impl. în `scrie_ass_pops`), logo la **y=170, dreapta 40** (impl. în `shorts.py`).
9. Captions dinamice = +15–25% watch time (noi: pops galbene la momente-cheie — regula creatorului rămâne, NU captimi tot dialogul).
10. Trending audio în primele 5s = +21% reach (noi: sting-ul „Awkward" la 0.3s = echivalentul nostru).

## 3. PUBLARE
- **1/zi** minim pentru creștere; 2/zi = accelerare (subiecte diferite); >3/zi = canibalizare; 10+/zi = spam-flag.
- Intervale RO (audiența locală): **12–15 și 19–21**; weekend dimineață 9–11. **Consistența aceeași oră bate ora optimă**.
- Prima oră după post: răspunzi la comentarii (viteza de engagement alimentează testul).
- Fiecare Short = O idee; hashtag 3–5 max; cuvinte-cheie căutare în titlu („minecraft", „pokemon", „nether" etc).

## 4. CHECKLIST ÎNAINTE DE LIVRARE (motorul refuză singur)
- [ ] `filmstrip()` privit — fiecare tăietură are un eveniment VIZIBIL (LEGE t126)
- [ ] `verifica_hook()` trece (prima secundă = mișcare)
- [ ] `verifica_subs_vizibile()` trece pe TOATE popurile
- [ ] 16.0s / 1080×1920 / −14 LUFS / logo în safe-zone / pops MarginV 340
- [ ] Loop: finalul se leagă de început SALE se taie înainte de rezolvare
- [ ] Titlu: pers. I / întrebare bombă, 2–5 cuvinte + „ ?"/„ !", fără diacritice, cuvinte-cheie de căutare

## 5. KPI DE URMĂRIT ÎN YT STUDIO (după fiecare post)
- Viewed vs Swiped ≥75% | Retenție medie ≥70% | Rewatch (vârf final) | Like/view, comentarii în prima oră.
- Dacă swipe <75% → schimbi HOOK-ul (altă primă secundă), nu restul. Dacă retenția cade la mijloc → aer moart/taieturi.
