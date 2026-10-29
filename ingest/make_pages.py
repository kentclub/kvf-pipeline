#!/usr/bin/env python3
"""
Stack pending clip sheets into review pages (6 clips per page) so a reviewer can
describe many clips from one image. Output: _system/pages/page_NN.jpg + page_NN.json
(the pending entries on that page, in order). Used for the backlog; the daily
ingest task can read the per-clip sheets directly when there are only a few.
"""
import os, json, subprocess, sys

HOME = os.path.expanduser('~')
DRIVE = os.environ.get('KVF_DRIVE', f'{HOME}/Library/CloudStorage/GoogleDrive-kentozcelik@gmail.com/My Drive/KvF Inbox')
SYSTEM = f'{DRIVE}/_system'
PENDING = f'{SYSTEM}/pending'
PAGES = f'{SYSTEM}/pages'
PER = int(os.environ.get('KVF_PER_PAGE', '6'))
os.makedirs(PAGES, exist_ok=True)

for f in os.listdir(PAGES):
    os.remove(f'{PAGES}/{f}')

entries = []
for f in sorted(os.listdir(PENDING)):
    if f.endswith('.json'):
        d = json.load(open(f'{PENDING}/{f}'))
        if d.get('sheet'):
            entries.append(d)
entries.sort(key=lambda d: (d.get('shot') or '', d['id']))

for n in range(0, len(entries), PER):
    chunk = entries[n:n+PER]
    inputs = []
    for d in chunk:
        inputs += ['-i', f'{SYSTEM}/{d["sheet"]}']
    k = len(chunk)
    fc = ''.join(f'[{i}:v]' for i in range(k)) + (f'vstack=inputs={k}[o]' if k > 1 else 'copy[o]')
    out = f'{PAGES}/page_{n//PER:02d}.jpg'
    subprocess.run(['ffmpeg', '-v', 'error', '-y'] + inputs + ['-filter_complex', fc, '-map', '[o]', '-q:v', '6', out])
    json.dump([{'id': d['id'], 'shot': d['shot'], 'dur': d['dur'], 'speech': d['speech'], 'folder': d['folder']} for d in chunk],
              open(out[:-4] + '.json', 'w'), ensure_ascii=False, indent=1)
    print(out, k, flush=True)
print('pages:', (len(entries) + PER - 1) // PER)
