# Word timings for opener + voiceover, aligned to the script text.
import json, re, sys, subprocess, difflib, numpy as np
from faster_whisper import WhisperModel
d=sys.argv[1]; s=json.load(open(f'{d}/script.json'))
m=WhisperModel('small.en',device='cpu',compute_type='int8')
def load(p):
    raw=subprocess.run(['ffmpeg','-v','error','-i',p,'-f','s16le','-ac','1','-ar','16000','-'],capture_output=True,check=True).stdout
    return np.frombuffer(raw,np.int16).astype(np.float32)/32768
def norm(w): return re.sub(r'[^a-z0-9.%]','',w.lower().replace(',','')).rstrip('.')
def words(p,hint):
    segs,_=m.transcribe(load(p),word_timestamps=True,initial_prompt=hint,vad_filter=False,condition_on_previous_text=False)
    return [(w.word.strip(),w.start,w.end) for sg in segs for w in sg.words]
def align(script_words,heard):
    a=[norm(w) for w in script_words]; b=[norm(w) for w,_,_ in heard]
    t=[None]*len(a)
    for blk in difflib.SequenceMatcher(None,a,b,autojunk=False).get_matching_blocks():
        for k in range(blk.size): t[blk.a+k]=(heard[blk.b+k][1],heard[blk.b+k][2])
    # fill gaps by interpolation between known neighbours
    known=[i for i,x in enumerate(t) if x]
    for i in range(len(t)):
        if t[i]: continue
        lo=max([k for k in known if k<i],default=None); hi=min([k for k in known if k>i],default=None)
        st=t[lo][1] if lo is not None else 0; en=t[hi][0] if hi is not None else st+0.3
        nl=(hi if hi is not None else len(t))-(lo if lo is not None else -1)
        pos=i-(lo if lo is not None else -1)
        a0=st+(en-st)*(pos-1)/max(nl-1,1); t[i]=(a0,a0+(en-st)/max(nl-1,1))
    return t
dur=lambda p: float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',p]))
out={}
# opener: Kent's own audio; take the transcript as heard (2-pass rule: speech confirmed earlier)
out['opener']=None
if s.get('opener'):
  op=f'work/{s["opener"]}.mp4'
  ow=words(op,s.get('opener_hint',f'Day {s["day"]} of going from this to this with AI as my coach.'))
  # cut dead air: start 0.15 s before his first word, end 0.15 s after his last word
  t0=max(0,ow[0][1]-0.15); t1=min(dur(op),ow[-1][2]+0.15)
  out['opener']={'src':s['opener']+'.mp4','trimMs':int(t0*1000),'durationMs':int((t1-t0)*1000),
    'captions':[{'text':' '+w,'startMs':int((a-t0)*1000),'endMs':int((b-t0)*1000)} for w,a,b in ow],
    'thisMs':[int((a-t0)*1000) for w,a,b in ow if norm(w)=='this']}
# voiceover
sw=[]; owner=[]
for li,l in enumerate(s['lines']):
    for w in l['text'].split(): sw.append(w); owner.append(li)
# Speech recognition with the script as a hint can skip whole sentences (Day 16: it heard only the last 30%,
# so captions were spread evenly and drifted 2.4 s late). Try a plain pass first, use the hint only if it matches better,
# and refuse to continue unless almost every script word was actually heard.
def coverage(heard):
    a=[norm(w) for w in sw]; b=[norm(w) for w,_,_ in heard]
    return sum(blk.size for blk in difflib.SequenceMatcher(None,a,b,autojunk=False).get_matching_blocks())/len(a)
vo_path=f'{d}/vo.wav'
vw=words(vo_path,None); cov=coverage(vw)
if cov<0.95:
    vh=words(vo_path,' '.join(l['text'] for l in s['lines'])); ch=coverage(vh)
    if ch>cov: vw,cov=vh,ch
print(f'voice coverage: {cov:.0%} of script words heard')
if cov<0.9: sys.exit(f'alignment failed: only {cov:.0%} of the script was heard. Heard: {" ".join(w for w,_,_ in vw)}')
tt=align(sw,vw)
lines=[]
for li in range(len(s['lines'])):
    idx=[i for i,o in enumerate(owner) if o==li]
    lines.append({'startMs':int(tt[idx[0]][0]*1000)})
for li in range(len(lines)):
    lines[li]['endMs']=lines[li+1]['startMs'] if li+1<len(lines) else int(dur(f'{d}/vo.wav')*1000)
lines[0]['startMs']=0
bad=[i for i,l in enumerate(lines) if l['endMs']-l['startMs']<300]
if bad: sys.exit(f'alignment failed on lines {bad} (Whisper heard: {" ".join(w for w,_,_ in vw)})')
out['vo']={'src':'vo.wav','durationMs':int(dur(f'{d}/vo.wav')*1000),'lines':lines,
  'captions':[{'text':' '+w,'startMs':int(a*1000),'endMs':int(b*1000),'line':o} for w,(a,b),o in zip(sw,tt,owner)]}
out['heard']=' '.join(w for w,_,_ in vw)
json.dump(out,open(f'{d}/timeline.json','w'),indent=1)
print(json.dumps({'opener_caps':[c['text'] for c in out['opener']['captions']] if out['opener'] else None,'lines':lines,'heard':out['heard']},indent=0))