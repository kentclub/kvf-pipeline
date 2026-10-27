# Caption sync check on the FINAL render: every caption must start when its word is actually spoken.
# Usage: python3 check_sync.py dayN   -> exits 1 if captions drift (median > 0.15 s or any word > 0.5 s off).
import json, re, subprocess, sys, difflib, numpy as np
from faster_whisper import WhisperModel
d=sys.argv[1]; t=json.load(open(f'{d}/timeline.json')); op=t['opener']['durationMs'] if t['opener'] else 0
caps=[(c['text'].strip(),(c['startMs']+op)/1000) for c in t['vo']['captions']]
raw=subprocess.run(['ffmpeg','-v','error','-i',f'{d}/{d}_final.mp4','-f','s16le','-ac','1','-ar','16000','-'],capture_output=True,check=True).stdout
a=np.frombuffer(raw,np.int16).astype(np.float32)/32768
m=WhisperModel('small.en',device='cpu',compute_type='int8')
segs,_=m.transcribe(a,word_timestamps=True,vad_filter=False,condition_on_previous_text=False)
heard=[(x.word.strip(),x.start) for s in segs for x in s.words]
norm=lambda w: re.sub(r'[^a-z0-9]','',w.lower())
diffs=[]
for blk in difflib.SequenceMatcher(None,[norm(c[0]) for c in caps],[norm(h[0]) for h in heard],autojunk=False).get_matching_blocks():
    for k in range(blk.size): diffs.append((abs(caps[blk.a+k][1]-heard[blk.b+k][1]),caps[blk.a+k][0],round(caps[blk.a+k][1],2)))
med=float(np.median([x[0] for x in diffs])); worst=max(diffs)
print(f'{d}: {len(diffs)}/{len(caps)} caption words checked, median off {med:.2f}s, worst {worst[0]:.2f}s ("{worst[1]}" at {worst[2]}s)')
sys.exit(1 if med>0.15 or worst[0]>0.5 or len(diffs)<0.85*len(caps) else 0)