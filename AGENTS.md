# AGENTS.md — AutoEditor (read first)

## Handoff

Read this file, the latest dated sections of MEMORY.md, and ISTORIC_COMPLET.md.
The latter is historical, not live state. Verify `git status`, `gh run list --limit 3`
and the release assets before claiming anything is delivered. Follow the checkout
and branch assigned by Arena; never use historic paths/credentials from MEMORY.md.

The owner is a Romanian-speaking creator, not a developer. Answer briefly in
Romanian; choose implementation details yourself, test changes, explain blockers.
For larger tasks, give a short plan. Never promise perfection or unmeasured speedups.

## Standing editorial requirements

- Episodes: 150–170 seconds, one understandable story, one game, actual in-game
  events. No menu/settings filler, no forced weak episode, no false title claims.
- Shorts: 16 seconds, separately reviewed on the actual portrait crop.
- No channel watermark, confetti or random zooms. Yellow POP captions only at
  key moments; verbatim transcript quotes, full SRT delivered separately.
- 2K output, verified audio mastering targeting -14 LUFS, real-frame thumbnails.
  Do not imply upscaling restores source detail. No AI-generated thumbnails.
- Use creator-supplied sounds in sunete_mele/. No random filler, no downloads of
  new effects/music/memes without authorization. Preserve every original file.
- YouTube uploads must be private; the creator publishes manually.
- Deliver titles and download links through GitHub Releases/Issues.
- Never download/render real VODs in the sandbox. Heavy work is GitHub Actions.
  Do not start a new VOD run without the creator's go-ahead.

## Active architecture

- `.github/workflows/episod.yml`: configuration preflight, dependencies/caches,
  source selection/download, editor, shorts, delivery and optional private upload.
- `pipeline_github.py`: orchestrator. 2K is rendered BEFORE any delivery, not as
  a second video encode after upload. Source YouTube download allows up to1440p.
- `autoeditor.py --ai`: strict continuous-story mode. No energy fallback; no
  post-approval energy cuts. Full transcript, proposal, exact video review.
- `idei_ai.py`: overlapping full-transcript pages; up to12 candidate ideas; review
  exact segments via Gemini. Models are configurable, not presumed available.
- `editorial.py`: strict review validation, non-overlap, sound event validation,
  exact quote IDs for captions. API failure/invalid response cannot approve a clip.
- `sunete_mele/catalog.json`: explicit usage rules for the10 supplied sound files.
  The pumm effect belongs to falling/impact, not victory. These rules come from
  creator descriptions/filenames, NOT acoustic listening or license verification.
- `shorts.py`: independent portrait review and title/sound plan for each short.
- `performance.py`: exact-input JSON cache, atomic writes, stage timings. Transcript
  keyed by full source fingerprint/model/settings; approved reviews expire after24h
  and include prompt/model/crop/catalogue. Cache hits are revalidated. Failures and
  rejected reviews are not cached as approvals. Never weaken checks for speed.
- `nume_public.py` / `upload_release.py`: public filenames remain in episodes/;
  upload aliases are respected without moving originals. Publish files, not temp dirs.
- `auto_upload_yt.py`: opt-in private upload, only with YT_UPLOAD_ENABLED=true plus
  YT_CLIENT_ID/YT_CLIENT_SECRET/YT_REFRESH_TOKEN from Actions Secrets.
- `preflight.py`: checks configuration presence only, NOT actual API authentication.
- `invata_trending.py`, `cunoastere/`: channel context and editorial memory.

<<<<<<< HEAD
Local legacy CLI scripts remain for compatibility. They are not the primary
production workflow. Old README documentation lives in docs/ISTORIC_README.md.

## Security and source protection

- Use Arena's configured git/gh authentication. Never request GitHub tokens in
  chat, embed credentials in remote URLs, or assume old local OAuth files exist.
- Credentials pasted in chat on2026-09-25 must be revoked/rotated by the owner.
  Never copy, store or use those values. Record only the incident, not the values.
- Upload is disabled by default. The owner sets fresh OAuth Secrets and then
  explicitly enables YT_UPLOAD_ENABLED=true. See SECURITY.md and GH_SETUP.md.
- Never delete, split or recode creator originals. The old destructive sound
  organizer is now a compatibility no-op. Generated output belongs in episodes/.
- Run `python tools/check_secrets.py`. It prints paths/types, never matching
  secrets; it is a limited guard, not a complete audit or a scan of chat/history.
- A workflow-write permission error requires checking the app permission request,
  installation approval and effective connection permissions. The app publisher
  requests permissions; the installing account approves them. Reconnecting alone
  does not guarantee a fix. Never request tokens or claim a failed push succeeded.

## Validation and operational lessons

- `python -m unittest discover -s tests -v`
- `python -m compileall -q .`
- Validate workflow YAML/shell syntax and inspect the actual diff after edits.
- Unit tests mock API/media processing. Passing them does NOT certify real-VOD
  editorial quality or runtime. First real delivery still needs watching/listening.
- Same-size writes can have identical timestamps: stat-only digest memoization
  failed a regression test. Hash all source bytes; pass the fingerprint explicitly
  within a process working on an immutable downloaded VOD.
- Long-lived processes use platform process tools, not nohup. Do not pipe long
  processes into head. GitHub asset downloads require application/octet-stream.
- Append meaningful progress, validation and blockers to MEMORY.md. Commit and
  push only the assigned session branch. Confirm push succeeded before saying so.
=======
## Current state & next steps
See MEMORY.md (top sections = freshest). Verify with:
  git -C /home/user/autoeditor fetch origin && git status
  curl -s -H "Authorization: Bearer $GITHUB_TOKEN" https://api.github.com/repos/iZentric/AutoEditor/actions/runs?per_page=1
The work loop for a new VOD: user creates a GitHub release (tag vod-N) with the video file
attached and the YouTube VOD link in the description -> workflow does everything ->
you monitor runs (gh api), fix failures by reading job logs, and deliver TITLE + download
links to the user in Romanian, short, with tables.

## CE SA CITESTI CA SA "INVEȚI TOT" (checklist preluare, in ordine)
1. ISTORIC_COMPLET.md  — cine e userul, ce a cerut, de la primul mesaj
2. AGENTS.md           — cum lucrezi (reguli de fier, capcane sandbox)
3. MEMORY.md           — toate detaliile tehnice per sesiune
4. cunoastere/*        — ADN canale (iSilent/JocuriHorrorSky + legile MrBeast), formate episod,
   canal (linkuri reale), titluri folosite, trending RO
5. in cod (autoeditor.py): cauta "MrBeast", "PROTECTIA RETENTIEI", "FINAL ELASTIC",
   "COMPRIMARE stil-JOH", "PRIMELE 3 CUVINTE" — aceleasi legi, aplicate in cod
>>>>>>> 01b1a86 (learning pack: MrBeast laws + onboarding checklist)

## LEGI VIDEO V3 (t119, 25.09) #SUBTITRARI-DOAR-POPS #ANTI-MARIA #NUME-UNIC-UPLOAD
1. pe VIDEO: subtitrari DOAR la POP-uri (momente tari, max 10, min 10s intre ele) — FARA dialog continuu.
2. subtitrari OBLIGATORIU sincronizate: montaj multi-scena → harta scena→live ÎNAINTE de ASS (live_to_ep(t) = off + (t - start)).
3. EPISOD/SHORT: FARA replici catre o persoana din chat care NU apare in joc (ex "Maria") — _NUME_CHAT in autoeditor.py (lista extensibila) respinge la selectie SI la pops.
4. curatenie periodica: Release (fisier vechi/prost sters pe ID explicit) + /tmp golit la final.
5. RE-UPLOAD mereu cu nume NOU unic — același nume = CDN cache servește fișierul vechi.
6. upload asset >8MB: http.client stream (body=open(f,'rb')) — POST cu Content-Range trunchiază la primul chunk!
7. randare 2K in sandbox: pre-taie scenele separat (RAM!) sau randeaza 1080p — sursa live e 720p, calitate identica.
8. logo PNG in ffmpeg: OBLIGATORIU -loop 1 -t DUR — altfel dispare dupa primul frame!

## LEGI POSTĂRI/TITLURI (creator, 25.09) #JH-ISILENT-MEREU
- TOATE titlurile + postările de comunitate + descrieri = stil JH/iSilent, ÎNTOTDEAUNA (creator: "mereu vreau JH/iSilent").
- Rețeta: începe cu literă mică sau verb la pers. I; „.." (două puncte) la mijloc; CAPS pe cuvântul de șoc; cuvinte-bombă: „a înnebunit", „NEBUNIE", „fata nebună", „am supraviețuit", „de 100 de ori"; emoji max 2 (😱🔥😂).
- FĂRĂ ton formal, FĂRă formulări de scamător, FĂRĂ „EP".
- Post comunitate abonat: video-ul LUI pe primul loc + LIKE pentru el + sondaj scurt.

## REGULA PROZENT (ordin user 2026-10-04, PERMANENT)
La FIECARE discuție strategică: pârghiile se exprimă ÎN % impact pe canal, ordonate MAXIM-FIRST.
Categorii obligatorii: DOVEDIT pe datele canalului / PROBABIL (estimat cu sursă) / NEGARANTABIL.
Obiectiv declarat user: maxima audiență de copii RO + Moldova + diaspora (limba română le acoperă pe toate).
Egoist = agentul dă singur comenzile pregătitoare; public = doar cu DA explicit.

## [ADĂUGAT 06-10-2026] PROTOCOLUL DEMIURGE — MINIATURI (citește OBLIGATORIU)
Orice agent care lucrează în acest repo respectă: DEMIURGE_SYSTEM_PROMPT.md (protocolul complet),
PROTOCOL_MINIATURI_BRAND.md (legile esenței), FORMULE_TOP_DECODATE.md (formulele din 14.824 video),
tools/thumb_brand.py (stratul uman). Pe scurt: scena generată FĂRĂ text cu personajele fixe
(iZentric + Mocivanu) în stilul din refs/BRAND_THUMB_MASTER.png → nametag-uri Minecraft (Monocraft)
→ bulă scurtă + cerc + săgeată roșie (sau contur întrerupt + inimi, formula Cadres 31M) → logo serie
doar la serie → finisaj uman. Smart Matching: Minecraft → dagar/nacho/Cadres/Knoxy; alt joc →
top youtuberul acelui joc. Bossul nu explică niciodată workflow-ul: dă tema, primește livrarea.
