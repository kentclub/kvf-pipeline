# kvf-pipeline

Build manual for the daily "Kent vs Fat" Short (1080x1920, 30 fps). Input is one approved episode row in the Notion table "KvF · Content & Analytics". Output is `dayN/dayN_final.mp4` and `dayN/dayN_cover.jpg`. This repo does not decide what the video says; the script, the shot list and the cover come from the Notion row.

## Setup

```
git clone https://github.com/kentclub/kvf-pipeline && cd kvf-pipeline && bash setup.sh
```

Needs ffmpeg, python3, node 20+. Fonts are in `kvf-video/public/fonts`. Resemble Enhance (own-voice cleanup) is a separate `bash setup_enhance.sh`, only when a voice memo exists.

## Inputs

- Clips: Google Drive folder "KvF Inbox", id `1XWR-6tQkJRUD0FrMcbpdEdl2HKrFUOlh`, shared "anyone with the link: viewer". `python3 sync.py` lists it through `drive.google.com/embeddedfolderview` and downloads with `drive.usercontent.google.com`, no Mac or connector needed. `ONLY=name1,name2 python3 sync.py` fetches only those files. Finished videos (`dayN_*`) and subfolders are skipped. Older clips live in `KvF Inbox/_done` and are only reachable through the Mac.
- Raw names look like `<id>__<UUID>.MOV`. Symlink each to `raw/<id>.MOV` before `proxy.sh`.
- `IMG_0624.JPG` in the inbox root is the "last year" photo used by the opener. Keep it there.
- Episode row page body (written by the scriptwriter task):
  - `## Script`: one spoken line per bullet, in order. Voiced exactly as written.
  - `## Shot list`: table with start s, end s, spoken line, clip id, visual type, on-screen text. One row per segment.
  - `## Cover`: hook text (3 to 5 words, one word in *stars*), clip id, second.
  - `## Guardrails`: things this episode must not do. Hard rules.

## Daily build

1. `python3 sync.py` (or `ONLY=...`) → `raw/`
2. `python3 inventory2.py <files>` → filming date, duration, speech, frame sheet in `sheets/`. Use it to confirm a clip is what the shot list says, not to go looking for clips.
3. `./proxy.sh NAME [start] [dur]` → `work/NAME.mp4`. Normalize a filmed opener's audio to -16 LUFS.
4. Write `dayN/script.json` from the row. Format below.
5. Voice → `dayN/vo.wav`:
   - Own memo in the inbox: cut stutters (keep the last take), `bash setup_enhance.sh` once, `/home/claude/dfenv/bin/python enhance_vo.py dayN/memo_cut.wav dayN/memo_clean.wav`, compare its transcript with the script, then `python3 vo_prep.py dayN/memo_clean.wav dayN/vo.wav`.
   - Clone: ElevenLabs connector `creative_generate_speech`, voice_id `m4AXYCDpSPbU0yO1bNi1`, model `eleven_multilingual_v2`, generations_count 1, text = the VO lines joined (no opener line). Save as `dayN/clone_vo.mp3`, then `python3 vo_prep.py dayN/clone_vo.mp3 dayN/vo.wav`.
   - vo_prep: cuts on Whisper word timings, 0.18 s pauses inside sentences, 0.30 s after a full stop, 1.1x, -16 LUFS.
6. `python3 align.py dayN` → `dayN/timeline.json`. Prints voice coverage and stops under 90%. Never hand-fix timings around a low-coverage alignment.
7. `python3 make_props.py dayN` → `kvf-video/public/dayN/props.json`
8. Render: `cd kvf-video && npx remotion render Day ../dayN/dayN_final.mp4 --props=public/dayN/props.json --concurrency=2 --crf=22`. Over 30 MB: re-render with `--crf=24`.
9. `python3 check_sync.py dayN` must pass (median under 0.15 s, no word over 0.5 s, 85%+ words matched).
10. `python3 make_cover.py dayN` → `dayN/dayN_cover.jpg` and `dayN_cover_check.jpg` (full frame and Instagram 3:4 crop side by side). Face clear, badge and hook readable in both.
11. Final checks: frame sheet (`node kvf-video/stills.mjs public/dayN/props.json <frames...>` from `kvf-video/`), plain transcript of the render has every word, gap between a filmed opener and the narration under 0.5 s, no black last frame, peak under -1 dB (else `ffmpeg -i in.mp4 -c:v copy -af alimiter=limit=0.89 out.mp4`).

## script.json

See `examples/script.json`. Fields:

- `day`, `date`
- `opener`: clip id of the filmed "Day N" selfie, or `null`. `opener_hint`: his exact words, for Whisper. With `null`, line 1 is the series line over a clip and gets the big badge.
- `before_image`: optional, defaults to `IMG_0624.JPG`.
- `cover`: `hook` (one word in *stars*), `at` (seconds into the opener), optional `clip` when there is no opener, `badge` (default `DAY N`; Monday recaps use `WEEK N`), optional `zoom`, `y`.
- `lines[]`: `text` and `visual`. Visual is one of:
  - `{clip, start?, tag?}`: one clip, start in seconds, optional corner tag like `GYM DAY`.
  - `{clips[], starts[]?, tags[]?}`: several clips in a row.
  - `{card: "meal", label, items[], over?}`
  - `{card: "totals", kcal, protein, deficit, over?}`: counts up on the spoken numbers.
  - `{card: "progress", kg, of, pct, over?}`: fat lost toward the goal only.
  - `{card: "week", days: [{d, v}], over?}`: Monday recap bars, lime = deficit, red = over.
  - `{card: "balance", saved, savedLabel, lost, lostLabel, net, over?}`
  - `{card: "scan", label, rows: [{k, a, b}], over?}`
  - `over: {clip, start?}` puts the card as a panel on a clip so a human stays visible. Full dark card only when there is no clip at all.

## Style rules (locked)

- Inter Black, lime `#D4FF3A`, dark `#0E0F0C`. Captions uppercase, word by word, active word in lime, at y 1290. Captions on every line, cards included.
- Opener: big `DAY N` badge. "from this" = `IMG_0624` with `LAST YEAR`, "to this" = `10% BODY FAT` card.
- No clip below ~0.7x speed. Split a long line into sentence lines, each with its own clip.
- Each clip once. Him eating at most once per video. No second selfie right after the opener. The teaser may use a clip from the next day.
- Last clip holds through the tail. No black frame at the loop point.
- Numbers a card shows are not read aloud.
- Screenshots: build a 1080x1920 still on `#0E0F0C`, content between y 200 and 1200, 80 px side margins, `ffmpeg -loop 1 -i still.png -t 8 -vf fps=30,format=yuv420p work/NAME.mp4`.
- Monday video = weekly recap, scan to scan, with the `week` card, badge `WEEK N` (week 1 = 28 Sep to 4 Oct). See the `week`, `balance`, `scan` cards.
- Cover: face frame, `DAY N` badge top, hook bottom, all inside y 240 to 1680.

## Posting (Metricool, brand 7360889, brand timezone America/New_York)

- Final and cover go into `KvF Inbox` (device_commit_files to `/Users/kent/Library/CloudStorage/GoogleDrive-kentozcelik@gmail.com/My Drive/KvF Inbox/` through the Mac). Read their ids from the folder page, media = `https://drive.usercontent.google.com/download?id=<id>&export=download&confirm=t`, `videoThumbnailUrl` = the cover link.
- YouTube Short: public, not for kids, PEOPLE_BLOGS, tags `skinny fat, fat loss, cutting, AI coach`. Instagram Reel on feed. `instagramData.isAiGenerated` and `youtubeData.isAiGeneratedContent` stay false.
- Caption:
  ```
  Day N of following AI until I reach 10% body fat.
  <Gym day|Rest day>. <kcal> kcal, <protein>g protein, <deficit> kcal deficit.
  Fat lost so far: <kg> kg. <10.4 - kg> kg to go.
  Tomorrow: <teaser>.
  #skinnyfat #fatloss #cutting #fitnessjourney #aicoach
  ```
  "kg to go" = 10.4 minus fat lost so far, never the 10.4 total. Numbers come from the row's related Daily Life Log entry.
- Mac unreachable: Notion uploads cap at 20 MiB. Re-encode if needed (`-b:v 3900k`, two-pass), upload the final and the cover to the episode row with `notion-create-file-upload`, embed them, get signed links with `notion-get-file-download-urls`, schedule within 5 minutes. Metricool copies the media at creation.
- After scheduling: move that day's clips, memo, final and cover into `KvF Inbox/_done` (finals in `_done/finals`). Metricool already has its copy.

## Known traps

- Hinted Whisper passes can skip whole sentences (Day 16 captions ran 2.4 s late). `align.py` tries plain first and refuses under 90% coverage; `check_sync.py` is the second guard.
- faster-whisper cannot open file paths with the installed `av`. The scripts pass numpy arrays.
- Rebuilt voices (Resemble Enhance) can change a word. Compare the transcript with the script before aligning.
- Staging a 30 MB+ MOV from `_done` through the Mac times out. Make short proxies on the Mac first.
