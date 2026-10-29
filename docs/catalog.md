# Clip catalog

One line per clip, so no task has to watch a clip twice. The catalog lives in the Drive folder `KvF Inbox/_system/`. The Mac fills it with the mechanical parts (frames, transcript), a Claude task adds the one-line description, and from then on every task reads text.

## Drive folder layout

```
KvF Inbox/              phone uploads land here (root). Today's clips. IMG_0624.JPG stays here.
  _library/             every cataloged original, flat, raw iPhone names. Nothing is renamed.
  _finals/              dayN_final.mp4 and dayN_cover.jpg
  _proxies/             scratch for the builder (device_bash can only write inside attached folders). Cleaned nightly.
  _system/
    clips.jsonl         the catalog. Append only. Last line per id wins.
    pending/<id>.json   clips the Mac has processed but nobody has described yet
    sheets/<id>.jpg     4-frame contact sheet per clip (1000x320), used to write the description
    described/*.jsonl   lines written by cloud tasks, merged into clips.jsonl by the Mac on its next run
    pages/              review pages for the backlog (6 sheets stacked), optional
```

Folder = state (root: today, `_library`: cataloged). The catalog = description. Nothing else encodes anything.

The clip id is the number before `__` in the iPhone file name (`81490370418__197F….MOV` → `81490370418`). Find a file by id with `ls "KvF Inbox"/*<id>* "KvF Inbox/_library"/*<id>*`.

## Who does what

- Mac, launchd job `com.kvf.ingest` at 06:30 and 18:30 (`ingest/kvf_ingest.py`, plist in `ingest/`, installed in `~/Library/LaunchAgents`; the Python binary needs Full Disk Access or the Drive folder reads fail with EPERM), no Claude, no tokens:
  merge `described/*.jsonl` into `clips.jsonl`, drop pending entries that are now cataloged, then for each new video in the root (and in `_library` with `--all`): md5, ffprobe, contact sheet, whisper.cpp transcript, write `pending/<id>.json`. Then housekeeping: root videos older than 48 h move to `_library`, `_proxies` files older than a day are trashed.
- Scriptwriter (cloud, 09:09): reads `clips.jsonl` and `pending/*.json`. For pending clips it looks at the sheets and writes one description line each into `described/<timestamp>.jsonl` (Drive connector `create_file`, parent = the `described` folder). Uses the catalog to pick the day's clips and any older B-roll by `loc` and `desc`.
- Builder (cloud, 18:55): reads `clips.jsonl` to confirm what a clip shows (no inventory2 pass needed for cataloged clips). After scheduling, writes `{"id": "...", "used": [N]}` lines into `described/` for the clips it cut in.

Folder ids: root 1XWR-6tQkJRUD0FrMcbpdEdl2HKrFUOlh, _library 1elH-0SsafL5ucmxOtn19IgRjdDYJX3qs, _finals 11_aagq0MihGCpWBQvcy84E1tzq1CiS_A, _system 1pNNpsnM1Q5LzkFz9eb6DJZv2yXqbUBPf, pending 1Jd8iUbuHyDg7PoBxsw3iR5GWaBuoqYDb, sheets 1zTFwR7FaJj2QjYfg2ksesHGprGKlQ6H-, described 1vintE3bzlXlkaVDMb9fwBVAdmyiXdK8Z. The catalog file itself gets a new id if it is ever recreated; list `_system` to find it.

Cloud tasks read `_system` files through the public folder links (same pattern as `sync.py`: list with `https://drive.google.com/embeddedfolderview?id=<folder id>`, download with `https://drive.usercontent.google.com/download?id=<file id>&export=download&confirm=t`), or through the Google Drive connector. They write only into `described/`.

## Line format

Written by the Mac (pending json, copied into the catalog line):

```
id, name, folder (inbox|library), md5, shot (ISO minute, from the clip's own metadata), dur (s), w, h, size_mb,
flag (null | junk_short | dup_of:<id>), speech (transcript or null), sheet (sheets/<id>.jpg), ingested
```

Added by the describing task:

```
loc    gym | kitchen | home | street | car | other
desc   one line, what is visible: subject, action, angle, anything a shot list would need ("barbell row, side angle, 3 reps visible, dark gym")
face   true if Kent's face is clearly visible
q      good | usable | junk
used   [day numbers] (appended later by the builder as its own line: {"id": ..., "used": [31]})
```

Example:

```
{"id":"81490370418","name":"81490370418__197F531C-CD1E-4547-AC5C-A5160F95F8F7.MOV","folder":"inbox","md5":"…","shot":"2026-10-28T21:08","dur":14.2,"w":1080,"h":1920,"size_mb":10.4,"flag":null,"speech":"I'm not a teacher, I'm a student.","sheet":"sheets/81490370418.jpg","ingested":"2026-10-29T09:10","loc":"home","desc":"Kent talking to camera on the sofa, lamp light, selfie angle","face":true,"q":"good"}
{"id":"81490370418","used":[31]}
```

Reading the catalog: group lines by `id`, merge in order (later keys overwrite, `used` lists concatenate). A clip with `flag` set or `q = junk` is never picked.

## Rules

- Never rename or move originals by hand. The Mac moves root → `_library`; nothing else moves.
- Never edit `clips.jsonl` from the cloud. Write a line into `described/`, the Mac merges it.
- A description describes what is visible, not what the script wants it to be.
- Transcripts are whisper.cpp `small.en` on phone audio: good enough for "he says something about X", not for quoting.
