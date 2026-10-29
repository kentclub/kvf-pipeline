#!/usr/bin/env python3
"""
KvF clip worker. Runs on the Mac (launchd, daily 18:30) with no Claude involved.

For every video in the Drive folder `KvF Inbox` (root) and, with --all, in `_library`:
  - skip if already in the catalog (by file id) or already pending
  - md5, ffprobe (duration, size, filming date)
  - contact sheet (4 frames + label) -> _system/sheets/<id>.jpg
  - transcript with whisper.cpp -> speech or null
  - write _system/pending/<id>.json  (the cloud ingest task turns these into catalog lines)
Then housekeeping:
  - Inbox root videos older than KEEP_HOURS move to _library
  - _proxies files older than 1 day are removed (mv to Trash)

Nothing here needs a network, a token or a connector. Pure ffmpeg + whisper.cpp + stdlib.
Paths come from env or the defaults below.
"""
import os, sys, json, subprocess, hashlib, time, re, shutil, datetime as dt

HOME = os.path.expanduser('~')
DRIVE = os.environ.get('KVF_DRIVE', f'{HOME}/Library/CloudStorage/GoogleDrive-kentozcelik@gmail.com/My Drive/KvF Inbox')
LOCAL = os.environ.get('KVF_LOCAL', f'{HOME}/kvf')
WHISPER = os.environ.get('KVF_WHISPER', '/opt/homebrew/bin/whisper-cli')
MODEL = os.environ.get('KVF_MODEL', f'{LOCAL}/models/ggml-small.en.bin')
FONT = '/System/Library/Fonts/Supplemental/Arial Bold.ttf'
KEEP_HOURS = int(os.environ.get('KVF_KEEP_HOURS', '48'))
VIDEO_EXT = {'.mov', '.mp4', '.m4v'}

SYSTEM = f'{DRIVE}/_system'
PENDING = f'{SYSTEM}/pending'
SHEETS = f'{SYSTEM}/sheets'
LIBRARY = f'{DRIVE}/_library'
PROXIES = f'{DRIVE}/_proxies'
CATALOG = f'{SYSTEM}/clips.jsonl'
LOG = f'{LOCAL}/logs/ingest.log'
TMP = f'{LOCAL}/frames'

for d in (PENDING, SHEETS, LIBRARY, TMP, f'{LOCAL}/logs'):
    os.makedirs(d, exist_ok=True)


def log(*a):
    line = time.strftime('%Y-%m-%d %H:%M:%S ') + ' '.join(str(x) for x in a)
    print(line, flush=True)
    with open(LOG, 'a') as f:
        f.write(line + '\n')


def sh(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def clip_id(name):
    # 81490370418__197F531C-....MOV -> 81490370418 ; otherwise the stem
    m = re.match(r'^(\d+)__', name)
    return m.group(1) if m else os.path.splitext(name)[0]


def known_ids():
    ids = set()
    if os.path.exists(CATALOG):
        for line in open(CATALOG):
            line = line.strip()
            if not line:
                continue
            try:
                ids.add(json.loads(line)['id'])
            except Exception:
                pass
    for f in os.listdir(PENDING):
        if f.endswith('.json'):
            ids.add(f[:-5])
    return ids


def known_md5():
    out = {}
    if os.path.exists(CATALOG):
        for line in open(CATALOG):
            try:
                d = json.loads(line)
                if d.get('md5'):
                    out[d['md5']] = d['id']
            except Exception:
                pass
    for f in os.listdir(PENDING):
        if f.endswith('.json'):
            try:
                d = json.load(open(f'{PENDING}/{f}'))
                if d.get('md5'):
                    out[d['md5']] = d['id']
            except Exception:
                pass
    return out


def md5(path):
    h = hashlib.md5()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def probe(path):
    r = sh(['ffprobe', '-v', 'error', '-show_format', '-show_streams', '-of', 'json', path])
    d = json.loads(r.stdout or '{}')
    fmt = d.get('format', {})
    dur = float(fmt.get('duration', 0) or 0)
    tags = fmt.get('tags', {})
    shot = tags.get('com.apple.quicktime.creationdate') or tags.get('creation_time') or ''
    v = next((s for s in d.get('streams', []) if s.get('codec_type') == 'video'), {})
    a = next((s for s in d.get('streams', []) if s.get('codec_type') == 'audio'), None)
    w, h = int(v.get('width', 0) or 0), int(v.get('height', 0) or 0)
    rot = 0
    for sd in v.get('side_data_list', []) or []:
        if 'rotation' in sd:
            rot = int(sd['rotation'])
    if rot in (90, -90, 270):
        w, h = h, w
    return dur, shot[:16], w, h, a is not None


def sheet(path, cid, dur, shot, label):
    """4 frames at 10/35/60/85 percent, 180x320 each, text column on the left -> 1000x320 jpg."""
    out = f'{SHEETS}/{cid}.jpg'
    frames = []
    for k, pct in enumerate((0.10, 0.35, 0.60, 0.85)):
        fp = f'{TMP}/{cid}_{k}.jpg'
        sh(['ffmpeg', '-v', 'error', '-y', '-ss', f'{dur*pct:.2f}', '-i', path, '-frames:v', '1',
            '-vf', 'scale=180:320:force_original_aspect_ratio=increase,crop=180:320', '-q:v', '5', fp])
        if os.path.exists(fp):
            frames.append(fp)
    if not frames:
        return None
    tf = f'{TMP}/{cid}_label.txt'
    with open(tf, 'w') as f:
        f.write(f'{cid}\n{shot}\n{dur:.0f}s\n{label}\n')
    inputs = []
    for fp in frames:
        inputs += ['-i', fp]
    n = len(frames)
    fc = (''.join(f'[{i}:v]' for i in range(n)) + f'hstack=inputs={n}[s];') if n > 1 else '[0:v]copy[s];'
    fc += f"[s]pad=iw+280:ih:280:0:color=white,drawtext=fontfile='{FONT}':textfile='{tf}':x=8:y=8:fontsize=18:fontcolor=black:line_spacing=6[o]"
    r = sh(['ffmpeg', '-v', 'error', '-y'] + inputs + ['-filter_complex', fc, '-map', '[o]', '-q:v', '5', out])
    if r.returncode:
        log('sheet error', cid, r.stderr[:200])
    for fp in frames + [tf]:
        try: os.remove(fp)
        except OSError: pass
    return f'sheets/{cid}.jpg' if os.path.exists(out) else None


def transcribe(path, cid):
    if not (os.path.exists(WHISPER) and os.path.exists(MODEL)):
        return None, 'whisper missing'
    wav = f'{TMP}/{cid}.wav'
    sh(['ffmpeg', '-v', 'error', '-y', '-i', path, '-vn', '-ac', '1', '-ar', '16000', '-f', 'wav', wav])
    if not os.path.exists(wav) or os.path.getsize(wav) < 16000:
        return None, None
    r = sh([WHISPER, '-m', MODEL, '-f', wav, '-nt', '-np', '-l', 'en', '-t', '4'], timeout=300)
    try: os.remove(wav)
    except OSError: pass
    txt = ' '.join(l.strip() for l in r.stdout.splitlines() if l.strip())
    txt = re.sub(r'\[[^\]]*\]|\([^)]*\)', '', txt).strip()   # [BLANK_AUDIO], (music)
    txt = re.sub(r'\s+', ' ', txt)
    return (txt if len(txt) > 3 else None), None


def process(path, folder):
    name = os.path.basename(path)
    cid = clip_id(name)
    t0 = time.time()
    h = md5(path)
    dups = known_md5()
    dur, shot, w, h_, has_audio = probe(path)
    entry = {
        'id': cid, 'name': name, 'folder': folder, 'md5': h,
        'shot': shot, 'dur': round(dur, 1), 'w': w, 'h': h_,
        'size_mb': round(os.path.getsize(path) / 1e6, 1),
        'flag': None, 'speech': None, 'sheet': None,
        'ingested': dt.datetime.now().strftime('%Y-%m-%dT%H:%M'),
    }
    if h in dups and dups[h] != cid:
        entry['flag'] = f'dup_of:{dups[h]}'
    elif dur < 2:
        entry['flag'] = 'junk_short'
    else:
        entry['sheet'] = sheet(path, cid, dur, shot, folder)
        if has_audio:
            entry['speech'], err = transcribe(path, cid)
            if err:
                entry['note'] = err
    json.dump(entry, open(f'{PENDING}/{cid}.json', 'w'), ensure_ascii=False, indent=1)
    log(f'pending {cid} {dur:.0f}s flag={entry["flag"]} speech={"y" if entry["speech"] else "n"} {time.time()-t0:.1f}s')
    return entry


def videos(folder):
    try:
        names = sorted(os.listdir(folder))
    except FileNotFoundError:
        return []
    out = []
    for n in names:
        if n.startswith('.') or re.match(r'(?i)^day\d+_', n):
            continue
        if os.path.splitext(n)[1].lower() in VIDEO_EXT and os.path.isfile(f'{folder}/{n}'):
            out.append(f'{folder}/{n}')
    return out


def merge_described():
    """Cloud tasks cannot append to clips.jsonl in place (the Drive connector only
    creates files), so they drop one-off files into _system/described/*.jsonl.
    This merges them into the catalog, then removes the pending json of every
    cataloged id. Last line per id wins when reading the catalog."""
    desc_dir = f'{SYSTEM}/described'
    os.makedirs(desc_dir, exist_ok=True)
    files = sorted(f for f in os.listdir(desc_dir) if f.endswith('.jsonl'))
    added = 0
    with open(CATALOG, 'a') as cat:
        for f in files:
            p = f'{desc_dir}/{f}'
            for line in open(p):
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                    assert 'id' in d
                except Exception:
                    log('bad described line in', f, line[:80]); continue
                cat.write(json.dumps(d, ensure_ascii=False) + '\n'); added += 1
            os.remove(p)
    if added:
        log(f'merged {added} described lines from {len(files)} files')
    # prune pending entries that are now in the catalog
    ids = set()
    if os.path.exists(CATALOG):
        for line in open(CATALOG):
            try: ids.add(json.loads(line)['id'])
            except Exception: pass
    pruned = 0
    for f in os.listdir(PENDING):
        if f.endswith('.json') and f[:-5] in ids:
            os.remove(f'{PENDING}/{f}'); pruned += 1
    if pruned:
        log(f'pruned {pruned} pending entries already in the catalog')


def housekeeping():
    now = time.time()
    moved = 0
    for p in videos(DRIVE):
        if now - os.path.getmtime(p) > KEEP_HOURS * 3600:
            dest = f'{LIBRARY}/{os.path.basename(p)}'
            if not os.path.exists(dest):
                shutil.move(p, dest); moved += 1
    if moved:
        log(f'moved {moved} old inbox clips to _library')
    if os.path.isdir(PROXIES):
        trash = f'{HOME}/.Trash'
        for n in os.listdir(PROXIES):
            p = f'{PROXIES}/{n}'
            if os.path.isfile(p) and now - os.path.getmtime(p) > 86400:
                try:
                    shutil.move(p, f'{trash}/{n}__{int(now)}')
                except Exception as e:
                    log('proxy cleanup failed', n, e)


def main():
    args = sys.argv[1:]
    do_all = '--all' in args
    no_house = '--no-housekeeping' in args
    limit = None
    for a in args:
        if a.startswith('--limit='):
            limit = int(a.split('=')[1])
    if not os.path.isdir(DRIVE):
        log('ERROR drive folder missing', DRIVE); sys.exit(1)
    merge_described()
    known = known_ids()
    todo = [(p, 'inbox') for p in videos(DRIVE)]
    if do_all:
        todo += [(p, 'library') for p in videos(LIBRARY)]
        todo += [(p, 'library') for p in videos(f'{DRIVE}/_done')]
    todo = [(p, f) for p, f in todo if clip_id(os.path.basename(p)) not in known]
    if limit:
        todo = todo[:limit]
    log(f'start: {len(todo)} new clips (known {len(known)})')
    for p, f in todo:
        try:
            process(p, f)
        except Exception as e:
            log('ERROR', p, repr(e))
    if not no_house:
        housekeeping()
    log('done')


if __name__ == '__main__':
    main()
