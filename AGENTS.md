# AGENTS.md — AutoEditor (read me FIRST)

You are taking over an existing project. Read this + MEMORY.md, then verify state yourself.

## What this repo is
An autonomous AI video editor for the YouTube channel **iZentric** (RO, Minecraft/Pixelmon
server "PokeCity" + Roblox, audience kids 8-15). It turns raw live-stream VODs into
story-driven YouTube episodes + vertical shorts, publishes them as GitHub release assets,
and can auto-upload them to YouTube (private) into the "FĂCUTE DE AI" playlist.

Owner (the user) is NOT a developer. He talks in Romanian, wants short answers with tables,
numbers, and no abbreviations. He decides WHAT, you decide HOW.

## Golden rules (learned the hard way, do not violate)
1. ALWAYS answer in Romanian. Code/comments/git commits: English.
2. Max autonomy: pick the variant, execute, report. Do not ask the user to choose.
3. Self-correct after EVERY change: run, read logs, fix, re-run until green.
4. 5 failures on the same error -> change the approach entirely.
5. Verify before claiming "done" (API state, file listing, log lines).
6. >3 steps -> post a short plan first.
7. NEVER guess API shapes; check the docs / probe with a test call.
8. NO secrets in the repo or chat: keys live in `.env` (sandbox) and repo Secrets (CI).
9. After every big task append to MEMORY.md and push.
10. YouTube cookies (COOKIES_YT secret) die fast: 1 export = max 1 full download.
    Ask for a fresh Studio export when downloads start failing.

## Architecture (who does what)
- `.github/workflows/episod.yml` — the engine (GitHub Actions, ubuntu runner):
  * Triggers: `release published` (the user attaches the VOD file + YouTube link in the
    release description), `workflow_dispatch` (inputs: live_url, max_episoade, max_shorts,
    release_tag to reprocess an existing release without re-uploading), push on declansa/live.txt.
  * Steps: install deps (yt-dlp FRESH master build, google-genai, pillow, imageio-ffmpeg,
    faster-whisper, scenedetect) -> learn RO trending (RSS, no keys) -> cookies from secret
    -> locate source (release asset via ASSET_TOKEN, or direct YouTube URL in the release
    body; yt-dlp first, Studio download-my-video token fallback) -> `pipeline_github.py`
    -> publish release assets -> memory (used titles) -> Issue notification with
    TITLE + download links.
- `pipeline_github.py` — orchestrates: source download (cache-skip), oEmbed context,
  `autoeditor.py --ai --subtitrari` (WHISPER_MODEL=base for speed), `shorts.py`
  (MAX_SH env, "auto" = AI picks), YouTube auto-upload block (non-fatal), `urca_2k.py` (2K).
- `autoeditor.py` — the editor brain (~1600 lines): scene cutting, story episodes
  (4 acts: cold-open teaser -> setup -> rising action -> CLIMAX, all scenes within the
  same game session +-12 min around the peak), AI scoring/titles (Gemini), zoom OFF by
  default (AE_ZOOM=1 to enable), watermark OFF by default (AE_LOGO=1), confetti OFF
  (AE_CONFETI=1), POP subtitles (AE_POPS, big yellow on-screen quotes at key moments,
  max 6/episode), .srt per episode, thumbnails A/B/C from real frames, -14 LUFS,
  upload.txt kit (title/description/tags), RAPORT.md, plan.json, memory writes.
- `idei_ai.py` — 2026-level video understanding: Gemini File API (resumable upload,
  1 FPS sampling), each episode idea is VERIFIED by letting Gemini WATCH the actual
  segment (ok / single game / corrected title / hook second). Model fallback chain:
  requested model -> gemini-3.6-flash -> gemini-3.5-flash (aliases often 503).
- `shorts.py` — 16s vertical shorts cut exactly at the strongest moment (MAX_SH env).
- `invata_trending.py` — daily learning from RO channels via YouTube RSS (no keys).
- `nume_public.py` — renames EPxx.* to public names derived from titles (no "Ep." numbers).
- `auto_upload_yt.py` — CI YouTube upload (needs YT_CLIENT_ID/SECRET/REFRESH_TOKEN
  secrets; default privacy PRIVATE, notifySubscribers=false, adds to playlist).
- `upload_release.py` — per-piece immediate release upload ("livrare pe rand").
- `livreaza_linkuri.py` — TITLE + direct download links posting (Issue #2).

## User requirements (standing, all confirmed repeatedly — do NOT undo)
- Titles in the style of RO channels iSilent + JocuriHorrorSky (see cunoastere/adn_canale.md),
  NO "Ep. N" in titles or file names, titles must mean exactly what the video shows.
- Every episode = one STORY with meaning (beginning-rising-climax), single game per episode
  (never mix Minecraft and Roblox inside one episode), only in-game moments (menus/settings
  = score 1, discard), ~3 min (150-170s), shorts are 16 seconds.
- NO on-screen channel watermark, NO confetti, NO random zooms (zoom only if he asks).
- POP subtitles: big + yellow, ONLY at key moments (AI picks). Full .srt ships separately.
- 2K upscale mandatory, -14 LUFS audio, thumbnails from REAL frames (3 variants).
- Delivery: per-piece release uploads + final Issue comment with TITLE + download link
  per piece. The user clicks, file lands on his PC.
- YouTube: auto-upload PRIVATE (user publishes manually when he wants) into playlist
  "FĂCUTE DE AI" (id in cunoastere/ai_playlist_id.txt). Daily quota 10k units resets
  ~09:00 Europe/Bucharest; each upload costs ~1600 units.
- The AI learns daily: trending RO channels (RSS), its own used titles (never repeat),
  transcripts saved to cunoastere/transcripte/.

## Sandbox specifics (this machine)
- Repo at /home/user/autoeditor, origin remote uses x-access-token with GITHUB_TOKEN from
  /home/user/autoeditor/.env (also GEMINI_API_KEY, YOUTUBE_REFRESH_TOKEN, GEMINI_MODEL).
- Sandbox loses git identity + remote between sessions: re-set them before every push
  (user.email agent@autoeditor.local, user.name AutoEditor Agent, remote URL with token).
- OAuth for YouTube works from sandbox: /home/user/.env + /home/user/client_secret.json
  (installed client). Quota may be exhausted -> HTTP 403 with "quota" in body.
- Long-running background processes must use the platform process tools (nohup dies).
- When editing episod.yml with fuzzy editors, VERIFY with grep afterwards (edits reported
  success without effect twice); prefer python read->replace with asserts.
- `python script.py | head -N` kills the process (SIGPIPE) — redirect to a file instead.
- urllib raises on HTTP 308 (YouTube resumable uploads) — catch HTTPError, read Range.
- GitHub release asset content: Accept "application/octet-stream" (raw/json return JSON).

## Current state & next steps
See MEMORY.md (top sections = freshest). Verify with:
  git -C /home/user/autoeditor fetch origin && git status
  curl -s -H "Authorization: Bearer $GITHUB_TOKEN" https://api.github.com/repos/iZentric/AutoEditor/actions/runs?per_page=1
The work loop for a new VOD: user creates a GitHub release (tag vod-N) with the video file
attached and the YouTube VOD link in the description -> workflow does everything ->
you monitor runs (gh api), fix failures by reading job logs, and deliver TITLE + download
links to the user in Romanian, short, with tables.
