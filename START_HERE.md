# 🚨 START HERE — CITESTE PRIMUL (protocol de preluare, 06-10-2026)

## CINE ESTE BOSSUL ȘI CINE EȘTI TU
- Bossul = **Overlordul** (canalul **iZentric**, handle aprobat: **@iZentric-Minecraft**).
- Tu = **Demiurgul**: agentul autonom care lucrează 1000 de pași înaintea lui.
- Misiunea: canalul la potențial maxim. Shorturi (v11 stil JH), episoade lungi, thumbnail-uri
  cu brand, research continuu. El aprobă, tu execuți tot.

## CONECTARE (primii pași, în ordine)
1. Bossul îți dă un token GitHub în chat → salvează-l: `mkdir -p /home/user/.secrets &&
   echo "TOKEN" > /home/user/.secrets/gh_token && chmod 600 /home/user/.secrets/gh_token`
2. Clonează: `git clone https://x-access-token:$(cat /home/user/.secrets/gh_token)@github.com/iZentric/AutoEditor.git /tmp/ae`
   (ține clonele în /tmp — .git/config cu token nu trebuie să intre în snapshot-uri!)
3. Instalează unelte: `pip install imageio-ffmpeg auto-editor faster-whisper yt-dlp pillow &&
   sudo apt-get install -y ffmpeg` (sandboxul le pierde la fiecare reset)
4. Citește ÎN ACEASTĂ ORDINE: `CONVERSATIE_COMPLETA_06-10.md` (tot ce s-a vorbit
   cu bossul, verbatim) → `AGENTS.md` → `DEMIURGE_SYSTEM_PROMPT.md` →
   `PROTOCOL_MINIATURI_BRAND.md` → `PROTOCOL_THUMB_SWAP.md` (⚠️ inclusiv BIBLIOTECA 1:1) →
   `FORMULE_TOP_DECODATE.md` → `REGULI_BOSS.md` (în workspace_migrat/) → `MEMORY.md`

## LEGILE CARE NU SE ÎNCALCĂ NICIODATĂ (pe scurt; detaliile în fișierele de mai sus)
1. NICIODATĂ același short/material de 2 ori (REGULI_BOSS #1 + REGISTRU_SHORTURI.md)
2. Short: 16s țintă (banda măsurată 12-18s), o singură explozie, captions sloturi FIXE
   64px, FĂRĂ CTA „episod complet", titlu cliffhanger, livrare COMPLETĂ (MP4+kit)
3. Thumbnail: swap pe modelele EXACTE din `refs/brand_1la1/` (61 originale + INDEX.csv) —
   NU regenera; schimbi DOAR personajele; bulele/cercurile/săgețile rămân CE SUNT în model
4. Personajele fixe: iZentric + Mocivanu (`refs/BRAND_THUMB_MASTER.png` = sursa de adevăr)
5. Sunete: `sunete_mele/` (creatorul) au prioritate; apoi `sunete_virale/` (autorizate
   EXPLICIT de boss în chat 06-10-2026)
6. Logo de serie DOAR la serie. -14 LUFS obligatoriu. QC-ul blochează sub prag.
7. Răspunsuri scurte și directe. Explicații simple cu %. Verifică, nu ghici.

## STAREA MISIUNII (ce e gata / ce urmează)
GATA: Editorul Suprem (editor_pro.py v11 + suprem.py, testat, LUFS+QC), Demiurg Thumb
(tools/demiurg_thumb.py — demo complet „bebe dragon"→dagar 12M), Biblioteca 1:1 (61 thumb-uri
originale), elemente_brand/ (PNG oficiale), miniaturi.py, formule decodate din 14.824 video,
sunete_virale autorizate, baza 3.413+6.573 video scanate.
URMEAZĂ: ① EPISODUL 1 — titlu+thumb APROBATE de boss (workspace_migrat/THUMB_EP1_GATA.jpg,
KIT_EP1_UPLOAD.txt) — DE POSTAT ② reanimare vctn6 (check stats, țintă >871 views)
③ LUNGI: builder-ul de episoade NU e implementat (următorul livrabil mare)
④ PostsYT SECRET nelivrat ⑤ redesign canal (banner+trailer după EP1).
/minutele/ locale sunt EPUIZATE: short nou DOAR cu materiale noi de la boss.

## HARTA RAPIDĂ
- Motor shorturi: `editor_pro.py` + `suprem.py` | Thumbnail: `tools/demiurg_thumb.py`
  (cauta/finalizeaza) + `tools/thumb_brand.py` + `miniaturi.py`
- Brand: `refs/BRAND_THUMB_MASTER.png`, `elemente_brand/`, `refs/brand_1la1/`+INDEX.csv
- Cunoștințe: `cunostinte/` (scan canale), `MEMORY.md` (145KB istoric), `ISTORIC_COMPLET.md`
- Migrat din workspace: `workspace_migrat/` (REGULI_BOSS, REGISTRU, KIT-uri, pro/ SFX,
  transcripts, thumbs EP1) | Fonturi: `assets/Monocraft.ttc`, `assets/Anton.ttf`
- Istoricul acestei sesiuni: finalul lui `ISTORIC_COMPLET.md`

## SECURITATE
- NU cere tokenul în mod repetat; NU-l scrie nicăieri în fișiere/loguri.
- Tokenul lipit în chat trebuie ROTIT de boss la final (GitHub → Settings → Developer settings).
- Nu șterge/recodeza originalele creatorului. Upload YouTube doar PRIVAT.
