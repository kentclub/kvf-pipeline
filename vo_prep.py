# Kent's voice memo -> day/vo.wav: keep only the spoken words, shorten every pause, speed 1.1x (same pitch), clean + level.
# Cuts are placed from Whisper word timings (not loudness), so background noise (street, cafe) can't hide pauses.
import subprocess, sys
import numpy as np
from faster_whisper import WhisperModel
src, out = sys.argv[1], sys.argv[2]
SPEED = float(sys.argv[3]) if len(sys.argv) > 3 else 1.1  # playback speed, same pitch (cloned voice: pass 1.1 too unless told otherwise)
MAX_PAUSE = 0.18 # longest pause kept inside a sentence (seconds, before speed-up)
END_PAUSE = 0.30 # pause kept after a full stop
LEAD, TAIL = 0.06, 0.15  # padding before the first word / after a word that ends a phrase

raw = subprocess.run(['ffmpeg','-v','error','-i',src,'-f','s16le','-ac','1','-ar','16000','-'],capture_output=True,check=True).stdout
audio = np.frombuffer(raw,np.int16).astype(np.float32)/32768
dur = len(audio)/16000
m = WhisperModel('small.en',device='cpu',compute_type='int8')
segs,_ = m.transcribe(audio,word_timestamps=True,vad_filter=False)
words = [(w.start,w.end,w.word.strip()) for s in segs for w in s.words]
if not words: sys.exit('no speech found')

# speech spans: words closer than MAX_PAUSE stay together
spans = []  # [start, end, ends_sentence]
for a,b,t in words:
    stop = t[-1:] in '.?!'
    if spans and a - spans[-1][1] <= (END_PAUSE if spans[-1][2] else MAX_PAUSE): spans[-1][1:] = [max(spans[-1][1], b), stop]
    else: spans.append([a,b,stop])
# Whisper word edges can be late/early by ~0.2 s: grow each span until the sound drops to the noise floor
hop = 160  # 10 ms frames
fr = audio[:len(audio)//hop*hop].reshape(-1,hop)
db = 20*np.log10(np.sqrt((fr**2).mean(1))+1e-9)
thr = np.percentile(db,15) + 8   # adaptive: 8 dB above this memo's background noise
def grow(t, step):
    i = int(t*100); k = 0
    while 0 < i < len(db)-1 and db[i+step] > thr and k < 20: i += step; k += 1
    return i/100
spans = [(max(0,grow(a,-1)-LEAD), min(dur,grow(b,1)+TAIL), st) for a,b,st in spans]
merged = []  # padding can make spans overlap: merge again
for a,b,st in spans:
    if merged and a <= merged[-1][1]: merged[-1] = (merged[-1][0], b, st)
    else: merged.append((a,b,st))
gaps = [max(0.01, (END_PAUSE if st else MAX_PAUSE) - LEAD - TAIL) for a,b,st in merged[:-1]]  # silence added between spans

n = len(merged)
fc = f"[0:a]aresample=48000,aformat=channel_layouts=mono,asplit={n}" + ''.join(f"[i{i}]" for i in range(n)) + ";"
fc += ''.join(f"[i{i}]atrim={a:.3f}:{b:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=0.01,afade=t=out:st={b-a-0.01:.3f}:d=0.01[s{i}];" for i,(a,b,_) in enumerate(merged))
fc += ''.join(f"anullsrc=r=48000:cl=mono,atrim=0:{g:.3f}[g{i}];" for i,g in enumerate(gaps))
seq = ''.join(f"[s{i}]" + (f"[g{i}]" if i < n-1 else '') for i in range(n))
fc += seq + f"concat=n={2*n-1}:v=0:a=1,atempo={SPEED},highpass=f=80,afftdn=nf=-25,loudnorm=I=-16:TP=-1.5:LRA=11[o]"
subprocess.run(['ffmpeg','-v','error','-y','-i',src,'-filter_complex',fc,'-map','[o]','-ar','48000','-ac','1',out],check=True)
new = float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',out]))
print(f'{n} speech parts, first word at {words[0][0]:.2f}s, {dur:.1f}s -> {new:.1f}s')