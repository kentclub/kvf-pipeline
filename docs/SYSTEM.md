# Kent vs Fat: how the system works

Read this first. It is the map. The other docs are the manuals for one part each.

Kent vs Fat is a daily Short (YouTube Shorts + Instagram Reels), series line "Day N of following AI until I reach 10% body fat". Day 1 = Mon 28 Sep 2026, +1 per calendar day (Europe/Istanbul). Posted at 20:00 Istanbul. Kent approves the script and the finished video; nothing is published without his explicit yes.

## The parts

| Part | What it is | Where |
| --- | --- | --- |
| Phone | Kent films clips all day, auto-upload to Google Drive | iPhone → Drive folder "KvF Inbox" |
| Drive | Storage and transport. Root = today's clips. `_library` = every older clip. `_finals` = rendered shorts. `_proxies` = builder scratch. `_system` = the clip catalog | Google Drive, folder id `1XWR-6tQkJRUD0FrMcbpdEdl2HKrFUOlh`, public "anyone with the link: viewer" |
| Mac (mac-home) | Always on at Kent's home. Runs Google Drive desktop (KvF Inbox pinned offline), ffmpeg, whisper.cpp, the clip worker. Also the place the builder writes finals through and makes proxies on | `~/kvf/` (repo clone, models, logs). Drive mounted at `~/Library/CloudStorage/GoogleDrive-kentozcelik@gmail.com/My Drive/KvF Inbox` |
| Clip worker | Local launchd job, no Claude: frames, transcript, pending entry per new clip; merges descriptions into the catalog; housekeeping | `com.kvf.ingest`, 06:30 and 18:30, `ingest/kvf_ingest.py`. See `docs/catalog.md` |
| Food and workout chats | Kent logs meals and gym sessions in two chats in the "workout channel" Claude project. They write memory files (cut-log, workout-log) | Claude project memory |
| Logger task | Copies yesterday's food, workout, weight and AI verdict from memory into Notion | "KvF: Daily Meal/Workout Logger to Notion", 04:39 |
| Scriptwriter task | Writes the episode row: script, shot list, cover, caption, guardrails. Describes new clips into the catalog. Waits for Kent's yes | "KvF: Daily Scriptwriter", 09:09. Prompt: `docs/scriptwriter-task.md` |
| Builder task | Builds the video from the approved row (voice, align, Remotion render, cover), sends it to Kent, schedules it in Metricool after his OK, files the clips | "KvF: Daily Short Creator v3", 18:55, bound to the Mac. Prompt: `docs/short-creator-task.md`. Manual: `README.md` |
| Analytics task | Fills views, watch time and URLs at 2 and 7 days; flips Scheduled → Posted | "KvF: Analytics Check", 23:16 |
| Notion | The running data. Three tables | Daily Life Log `collection://1b074723-f172-4b16-81bf-4d1cd4447e05`, Content & Analytics `collection://d77ad7ef-88c0-466a-8380-fc9458830eac`, Operations `collection://73f203a3-68c5-49b7-bb57-9ec5675887a3` |
| Metricool | Scheduling and posting to YouTube and Instagram | brand 7360889, timezone America/New_York |
| Repo | All code, prompts and docs | github.com/kentclub/kvf-pipeline, public |

## A day, in order (Istanbul time)

```
all day   phone → Drive root            Kent films, uploads land in KvF Inbox
04:39     Logger                        yesterday's Life log row in Notion (Draft or Final)
06:30     Mac worker                    new clips → sheets + transcripts → _system/pending
09:09     Scriptwriter                  describes pending clips → _system/described; writes the episode row (Draft); messages Kent
          Kent: "yes"                   row → Script ready
18:30     Mac worker                    merges described lines into clips.jsonl; evening clips → pending; root clips older than 48 h → _library
18:55     Builder                       catalog → proxies on the Mac → voice → render → sends video to Kent (Ready to publish)
          Kent: "yes"                   schedule in Metricool for 20:00 → row Scheduled; clips → _library, final → _finals; used lines → described
20:00     Metricool                     posts to YouTube and Instagram
23:16     Analytics                     Scheduled → Posted, URLs, 2d/7d numbers on the right days
```

Weekends get no separate video; Monday's video is the weekly recap (scan day).

## Where state lives

- Rules and identity: Claude project memory (channel rules, pipeline map, meal plan, recipes). Agents read, only the chats write.
- Running data: Notion. Episode status flow: Draft → Script ready → Ready to publish → Scheduled → Posted, or Blocked.
- Clips: Drive. Folder = state (root today, `_library` cataloged). Catalog = description (`_system/clips.jsonl`, one JSON line per clip, append only, last line per id wins). Nobody renames originals.
- Problems: every problem an agent hits becomes a row in "KvF · Operations" (Issue, Component, Status, Symptoms, Fix, Prevention). Check there before debugging anything twice.
- Code and prompts: the repo. The live prompt of a scheduled task is the source of truth; the `docs/*-task.md` copies are kept in sync by hand when a prompt changes.

## Hard rules every agent follows

- Nothing is scheduled or published without Kent's explicit OK on the finished video.
- Scripts say "my wife", never her name. No dates, weekdays or city names in a reel.
- Numbers come from the Life log row. Estimates stay labeled as estimates. No invented feelings, coach instructions or footage.
- A clip is what its catalog line says it is. If the shot list claims otherwise, the catalog wins and the clip is treated as missing.
- Agents never write to a Notion table they do not own, never message anyone but Kent, never edit the repo from a scheduled run (put the fix in an Operations row).
- When a brief conflicts with a guardrail, the guardrail wins; log it in Operations and say so to Kent.

## When it breaks

| Symptom | Likely cause | Check |
| --- | --- | --- |
| Builder says "Mac unreachable" | Mac asleep, Claude desktop app closed, or the folder grant lapsed | Mac on and app open; the task's attached folders |
| Clips missing from the catalog for yesterday | Worker did not run or could not read Drive | `~/kvf/logs/ingest.log` on the Mac; `launchctl list \| grep kvf`; the Python binary needs Full Disk Access (System Settings → Privacy & Security) |
| Scriptwriter cannot find a clip the phone uploaded | Drive upload lagging, or clip is under 2 s (flag junk_short), or a duplicate (flag dup_of) | Drive on the phone; the pending or catalog line for that id |
| Builder cannot find a file by id | It is in `_library`, not root (worker moves root clips after 48 h) | `ls "KvF Inbox"/*<id>* "KvF Inbox/_library"/*<id>*` |
| Public link download fails | The file was recreated and has a new id | List the parent folder with embeddedfolderview and take the current id |
| Post not live at 20:00 | Metricool rejected the media, or the Scheduled row was never confirmed | Metricool planner; Operations row "Scheduled post not live" |
| Captions out of sync | Whisper skipped a sentence | `check_sync.py` output; README "Known traps" |
| Disk full on the Mac | Proxies or frames not cleaned, or something unrelated | `df -h`; `_proxies` on Drive; `~/kvf/frames` |

## Reading order for a new agent

1. This file.
2. `docs/catalog.md` if you touch clips.
3. `README.md` if you build video.
4. Your own task prompt (`docs/*-task.md`).
5. The Operations table for anything that already went wrong.
