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
- A workflow-write permission error needs the GitHub integration updated by the
  owner. Do not request a token or claim that local changes reached GitHub.

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
