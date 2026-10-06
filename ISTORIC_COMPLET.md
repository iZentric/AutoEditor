# TOT ISTORICUL PROIECTULUI AutoEditor (de la primul mesaj pana la 24.09.2026)

> Istoric, nu stare live. Pentru actualizarile din 25.09.2026: vezi sectiunile
> recente din MEMORY.md, regulile curente din AGENTS.md si inceputul README.md.

## 1. CINE ESTE USERUL SI CE A VRUT
- Creator YouTube romanesc: canalul **iZentric** (@izentric1), ~1.310 abonati la inceput.
- Continut: Minecraft cu Pokemoni (serverul POKECITY, cu NOCIVANU), Roblox, live-uri cu copiii 8-15 ani.
- Canalele-model pe care vrea sa le copieze: **JocuriHorrorSky** (1,33M subs, avg 12:00) si **iSilent** (1,67M subs, avg 6:42).
- NU e dezvoltator. Vrea: "eu doar sa fac live, AI-ul sa faca TOT restul".
- Vorbeste scurt, in romana, cu greseli de tastare. Vrea raspunsuri SCURTE + tabele + cifre.
- Regula de aur a lui: "frate fii sigur 100%" + sa recunosc greselile + sa ma autocorectez singur.

## 2. TIMELINE-UL PROIECTULUI (ce am construit in ordine)
### Faza 1 — baza (sesiuni 18-22 sept)
- Dashboard canal din API-ul YouTube (fetch_channel.py, data.json).
- OAuth pe canal (oauth_setup.py) — refresh token in .env.
- Transcripte la 40/99 video-uri (get_transcripts.py).
- autoeditor.py: editorul local (scene, povesti, zoomuri, titluri, miniaturi, 2K, -14 LUFS).
- Decizie: GitHub Actions = motorul (user nu poate rula local). Repo: iZentric/AutoEditor.
- REGULA: ZERO video in sandbox; livrarea DOAR prin GitHub Releases.
- t84/t86: episoade din live-ul 0yLhCsn9ZwY (POKECITY 2h18) NU s-au livrat la timp (cookies moarte).

### Faza 2 — creierul (23 sept, t89)
- AI-ul copiaza stilul canalelor model:
  * cunoastere/adn_canale.md = ADN-ul lor (Roberto porcul, Tata Stric, Vicky, ritualuri "Vă urăsc", sunsky.ro)
  * cunoastere/trending_ro.md = invatare zilnica RSS de la canalele top RO (fara chei)
  * context_sursa.txt = oEmbed din linkul din descrierea release-ului
  * titluri_folosite.txt = memorie (nu-si repeta titlurile)
- Linkurile/transcriptele proprii ale userului = context: _FlwpZhugBw (mancare Minecraft + note),
  Hj4tlXv_U9A (skinwalker), IPP2CMGIpks (merch).
- cunoastere/formate_episod.md = formatele dovedite (note X/10, ELEMENT SURPRIZA, abonati pe perete etc.)
- "vreau cel mai bun AI care invata singur, se optimizeaza singur" (runda MAXIM):
  auto-upload YT (gated pe Secrete), notificare Issue, canale_extra.txt.
- Sinceritate impusa: "GPT 6 Astra" nu exista — Gemini 3.x gratis e motorul (azi: gemini-3.6-flash).

### Faza 3 — PRIMA LIVRARE COMPLETA (azi, 24 sept)
- Userul a publicat release vod-1: live 2h18 "AM INTRAT PE POKECITY + ROBLOX CU VOI" (1794 MB) + link YT.
- Run #17: a livrat PE RAND EP01/EP02/SHORT01, apoi a picat pe o virgula lipsa in pip install.
- Run #18 (reprocesare automata): SUCCESS — 13 fisiere. PRIMA LIVRARE cap-coada a functionat.
- Titluri sablon "Ep. 1" (AI-ul nu rulase --ai in CI) — descoperit mai tarziu.

### Faza 4 — cererile DURI ale userului si reparatiile (azi, dup-amiaza/seara)
- "nume fara EP" -> slug_nume() + nume_public.py: fisierele ies cu numele din titlu.
- "urcati-le pe youtube, public eu cand vreau" + "playlist special":
  * upload_acum.py (sandbox): urcare PRIVATA + playlist "FĂCUTE DE AI" (PLWXAjXumcUUU).
  * 3 piese urcate private; EP01 a urcat de 3x (bug duplicat) -> curata_duplicuri() fix.
  * COTA zilnica YT epuizata -> lecție: 1600 units/upload, resetare ~09:00-10:00 RO.
- "luati de pe youtube direct live-ul" -> pipeline: yt-dlp primul -> Studio token fallback -> asset plan B.
- Captura user: watermark "iZentric" pe ecran + confetti + meniu shader + amestec Minecraft/Roblox:
  * AE_LOGO=0 (watermark off), AE_CONFETI=0, meniu=setari scor 1, poveste un singur joc.
- "editor AI 2026, sa stie ce se intampla pe video": idei_ai.py — Gemini File API, modelul
  VEDE segmentul real (1 FPS+timestamps), confirma ideea/un_joc/titlu/hook. TEST REAL VERDE.
- "rapid, fara zoom-uri degeaba, sa faca poveste": AE_ZOOM=0 default, whisper base,
  poveste in 4 acte cu scenele din acelasi joc (setup -7.5min, dez -4min fata de varf).
- "subtitrari mari si galbene in anumite momente, sa decida AI-ul":
  SUBTITRARI-POP implementate (max 6/episod, >=18s intre ele, 2.6s pe ecran, galben Arial 88).
  .srt complet separat pt YouTube. TEST VERDE.
- "vreau doar titlul si linkul de download": livreaza_linkuri.py + NOTIFICARE cu TITLU + DESCARCA.
- "muta proiectul pe alt agent": AGENTS.md scris (manual de preluare) + checklist in MEMORY.md.

## 3. ARHITECTURA FINALA (cum functioneaza ACUM)
- DECLANSARE: user face release GitHub (tag vod-N) cu fisierul live atasat + linkul YT in descriere.
- WORKFLOW episod.yml: deps (yt-dlp fresh master, scenedetect, faster-whisper) -> invata trending
  RSS -> cookies din Secret -> sursa (yt-dlp direct / Studio / asset) -> pipeline_github.py:
  * autoeditor.py --ai --subtitrari (WHISPER_MODEL=base):
    - transcriere whisper base (~10 min pe 2h18)
    - poarta de calitate: doar momentele cu scor >= max(7.0, 0.6*max)
    - MOD IDEI: 2-3 idei cu poveste; VERIFICARE VIDEO cu Gemini (ok/un_joc/titlu_corectat/hook)
    - randare: poveste 4 acte (~170s), FARSA zoom (default), watermark OFF, confetti OFF,
      sunete_mele plasate semantic, subtitrari-POP galbene, .srt complet, -14 LUFS, 2K
    - miniaturi A/B/C din cadre reale + kit upload (titlu/desc/tags)
  * shorts.py: 16s verticale, MAX_SH=auto (doar scor>=0.75*max, max 6)
  * upload YT (gated Secrete): PRIVAT + playlist FĂCUTE DE AI
  * urca_2k.py: 2560x1440
- LIVRARE PE RAND: fiecare piesa urca imediat pe release; la final NOTIFICARE Issue cu TITLU+LINK.
- MEMORIE: titluri folosite + transcripte salvate + trending actualizat.

## 4. REGULILE DE FIER ALE USERULUI (nu se anuleaza)
1. Romana in raspunsuri; scurt, tabele, cifre. Cod/commits in engleza.
2. Autonomie maxima: alegi, faci, raportezi. Nu intreba ce ai putea decide singur.
3. Autocorectare dupa FIECARE schimbare: testezi, citesti logul, repari, re-testezi.
4. 5 esecuri pe acelasi eror -> schimbi abordarea complet.
5. Verifici inainte sa zici "gata" (API, fisiere, loguri).
6. FARA secrete in repo/chat. Cheile doar in .env / Secrets.
7. Fara watermark pe video, fara confetti, fara zoom-uri random.
8. Titluri: stil iSilent+JocuriHorrorSky, FARA "Ep. N", titlul = exact ce se vede.
9. Episoade: poveste cu sens, ~3 min, un singur joc, doar faze din joc.
10. Shorts: 16 secunde.
11. Subtitrari-POP galbene mari doar la momente-cheie + .srt separat.
12. 2K obligatoriu, -14 LUFS, miniaturi din cadre reale (3 variante).
13. Urcare pe YouTube PRIVATA (userul publica) in playlistul FĂCUTE DE AI.
14. Livrare: TITLU + LINK de download (click = pe PC).
15. Sinceritate totala: daca ceva nu e facut, se zice; daca gresesti, se recunoaste si se repară.

## 5. SECRETE & ACCES (unde sunt)
- In repo Secrets: COOKIES_YT (fresh 16:36 azi), GEMINI_API_KEY.
- In sandbox .env (de mutat de user la nevoie): GITHUB_TOKEN, GEMINI_API_KEY, GEMINI_MODEL, YOUTUBE_REFRESH_TOKEN.
- client_secret.json (OAuth desktop, app PRODUCTION) in sandbox.
- LIPSA in repo Secrets (pt upload din CI): YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN.
- Playlist FĂCUTE DE AI: PLWXAjXumcUUU (in cunoastere/ai_playlist_id.txt).

## 6. STAREA CHIAR ACUM (18:49, 24.09)
- Run #27 in lucru (pachetul complet cu subtitrari-POP). Estimare gata ~19:10.
- YouTube: curat (piesele vechi proaste sterse), playlist FĂCUTE DE AI gol dupa stergeri,
  cota zilnica probabil epuizata (resetare ~09:00-10:00 RO).
- vod-1 pe release: doar sursa (piesele vechi sterse dupa feedback).
- Urmatorul pas: livrarea TITLU+LINK de la run #27 + urcarea privata de catre robot/sau la resetarea cotei.

## Sesiunea 2026-10-06 — AGENTUL (Arena) — EDITORUL SUPREM + FĂCĂTORUL DE MINIATURI
1. **GitHub conectat PERSISTENT** (PAT salvat în sandbox `.secrets/gh_token`). Repo-ul privat
   `iZentric/AutoEditor` confirmat și clonat; bossul a ordonat: „de data asta nu mai te deconecta".
2. **EDITORUL SUPREM (commit 5455a5e)** = combinarea cerută de boss: creierul repo (legi AGENTS:
   16s, -14 LUFS, QC blocant, titluri JH, `sunete_mele/` prioritate) + motorul nou (auto-editor
   taie liniștea, captions karaoke sloturi FIXE galben/alb/roșu, SFX inteligent cu fail-detect,
   pop-out JH). Intrare: `suprem.py` (puntea) + `editor_pro.py`. Doc: `EDITOR_SUPREM.md`.
   Testat: randare ✓, LUFS ✓, QC BLOCANT pe dummy (4/8) ✓, titluri JH ✓.
3. **`sunete_virale/` autorizate EXPLICIT de boss în chat 06-10-2026** („trebuie suntele din
   github"): vine_boom/prowler/suspend/yeet/metal_pipe/heheheha/bass_drop/boowomp. Regula:
   `sunete_mele/` (creatorul) au întâietate; pachetul acoperă doar evenimentele rămase.
4. **FĂCĂTORUL DE MINIATURI `miniaturi.py`** — exact cum am vorbit (formula DNA JH):
   cadru REALE non-AI din jurul vârfului de energie (auto), săgeata roșie groasă OBLIGATORIE,
   text max 1-2 cuvinte (tăiat automat), logo serie DOAR la serie, boost culori, avatar stânga,
   CHECKLIST 8 legi cu BLOCARE sub 6/8 + test 120px telefon. Test pe material vechi: 7/8.
5. **SECURITATE**: PAT-ul a fost lipit în chat de boss → la final de sesiune bossul ÎL ROTEȘTE
   (GitHub → Settings → Developer settings → Fine-grained tokens → Regenerate).
6. Whispers pe sandbox 2GB: model `tiny` automat (pe mașina/Actions: `WHISPER_MODEL=small`).

## 06-10-2026 (cont.) — PROTOCOLUL DE BRAND MINIATURI (fixarea finală)
- Bossul a validat esența: refs/BRAND_THUMB_MASTER.png (nametag-uri Minecraft Monocraft,
  bula FUGI!, cercul roșu, săgeata, logo serie, stil cartoon-Minecraft contur gros).
- Regula de ALEGERE INTELIGENTĂ: la Minecraft → referințe @dagar-minecraft (top 6.3M) și
  UC8EkcHOycB94lHDkbAPSnQA (top 3.2M); la ALT joc → cel mai viral youtuber al acelui joc.
- Textul/bula/cercul/săgeata NICIODATĂ în generarea AI — se lipesc pe strat (claritate 100%).
- Unealtă: tools/thumb_brand.py. Primul thumbnail pe noul protocol: refs/THUMB_FINAL.jpg.

## 06-10-2026 (final) — DEMIURGE_FIXAT
Bossul a lipit conversația completă cu Gemini (agentul Demiurg). Salvat VERBATIM în
DEMIURGE_SYSTEM_PROMPT.md + secțiune obligatorie adăugată în AGENTS.md. Implementarea reală
din repo: BRAND_THUMB_MASTER.png + thumb_brand.py + miniaturi.py + FORMULE_TOP_DECODATE.md.
Nume (decizie cu date): canal afișat iZentric, handle @iZentric-Minecraft (SEO 276.8K/lună).
