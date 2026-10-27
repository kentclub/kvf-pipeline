# Clean + enhance Kent's voice memo with Resemble Enhance (free, CPU, ~6 min per 50 s). Run setup_enhance.sh once per session first.
# Usage: /home/claude/dfenv/bin/python enhance_vo.py dayN/memo_cut.wav dayN/memo_clean.wav   (then vo_prep.py on memo_clean.wav)
import sys, torch, torchaudio, numpy as np, subprocess
from pathlib import Path
from resemble_enhance.enhancer.inference import enhance
src, out = sys.argv[1], sys.argv[2]
raw = subprocess.run(['ffmpeg','-v','error','-i',src,'-f','s16le','-ac','1','-ar','44100','-'],capture_output=True,check=True).stdout
a = torch.from_numpy(np.frombuffer(raw,np.int16).astype(np.float32)/32768)
torch.set_num_threads(2)
wav, sr = enhance(a, 44100, 'cpu', nfe=32, solver='midpoint', lambd=0.9, tau=0.5, run_dir=Path('/home/claude/re_model/enhancer_stage2'))
x=(wav.numpy().clip(-1,1)*32767).astype(np.int16)
subprocess.run(['ffmpeg','-v','error','-y','-f','s16le','-ar',str(sr),'-ac','1','-i','-',out],input=x.tobytes(),check=True)
print('ok', sr, len(x)/sr)