# Build Remotion props for one day: copy media into public/<day>/ and merge script + timeline.
import json, sys, shutil, subprocess, os
from PIL import Image
import pillow_heif; pillow_heif.register_heif_opener()
d=sys.argv[1]; s=json.load(open(f'{d}/script.json')); t=json.load(open(f'{d}/timeline.json'))
pub=f'kvf-video/public/{d}'; os.makedirs(pub,exist_ok=True)
dur=lambda p: float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',p]))
clips={}
names=({s['opener']} if s.get('opener') else set())|{c for l in s['lines'] for c in ([l['visual']['clip']] if 'clip' in l['visual'] else l['visual'].get('clips',[]))+([l['visual']['over']['clip']] if 'over' in l['visual'] else [])}
for n in names:
    shutil.copy(f'work/{n}.mp4',f'{pub}/{n}.mp4'); clips[n]=dur(f'work/{n}.mp4')
shutil.copy(f'{d}/vo.wav',f'{pub}/vo.wav')
im=Image.open(f'raw/{s.get("before_image","IMG_0624.JPG")}').convert('RGB'); im.thumbnail((900,1600)); im.save(f'{pub}/before.jpg',quality=90)
props={'dir':d,'day':s['day'],'goalText':s.get('goal_text','10% BODY FAT'),'clips':clips,'lines':s['lines'],**t}
json.dump(props,open(f'{pub}/props.json','w'),indent=1)
print('ok',clips)