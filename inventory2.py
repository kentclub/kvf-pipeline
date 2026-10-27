# Inventory clips: date, duration, frames sheet, speech (no hint) -> sheets/inv_*.jpg + inventory.json
import json, subprocess, sys, os, numpy as np
from PIL import Image, ImageDraw, ImageFont
from faster_whisper import WhisperModel
names=sys.argv[1:]
m=WhisperModel('small.en',device='cpu',compute_type='int8')
font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",18)
inv=json.load(open('inventory.json')) if os.path.exists('inventory.json') else {}
for n in names:
    p=f'raw/{n}'
    d=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-of','json',p]))
    dur=float(d['format']['duration']); tags=d['format'].get('tags',{})
    date=tags.get('com.apple.quicktime.creationdate') or tags.get('creation_time')
    raw=subprocess.run(['ffmpeg','-v','error','-i',p,'-vn','-f','s16le','-ac','1','-ar','16000','-'],capture_output=True).stdout
    a=np.frombuffer(raw,np.int16).astype(np.float32)/32768
    text=''
    if len(a):
        segs=[s for s in m.transcribe(a,vad_filter=True,condition_on_previous_text=False)[0] if s.no_speech_prob<0.6]
        text=' '.join(s.text.strip() for s in segs)
    ims=[]
    for k in range(5):
        fp=f'/tmp/inv_{k}.jpg'
        subprocess.run(['ffmpeg','-v','error','-y','-ss',str(dur*(k+0.5)/5),'-i',p,'-frames:v','1','-vf','scale=144:256',fp])
        ims.append(Image.open(fp))
    sheet=Image.new('RGB',(144*5+330,256),'white'); dr=ImageDraw.Draw(sheet)
    for k,im in enumerate(ims): sheet.paste(im,(330+k*144,0))
    dr.text((5,5),n,fill='black',font=font); dr.text((5,30),str(date)[:16],fill='black',font=font); dr.text((5,55),f'{dur:.1f}s',fill='black',font=font)
    y=85
    for i in range(0,len(text[:200]),30): dr.text((5,y),text[i:i+30],fill='blue',font=font); y+=22
    sheet.save(f'sheets/inv_{n}.jpg')
    inv[n]={'date':date,'dur':round(dur,1),'speech':text}
    json.dump(inv,open('inventory.json','w'),indent=1)
    print(n,date,round(dur,1),'|',text or '(no speech)',flush=True)