# Cover / thumbnail for day N (locked design, see kvf-video/src/Cover.tsx):
# a frame of his face from the opener + big lime "DAY N" badge + one short hook line.
# script.json needs: "cover": {"hook": "AI swapped my *oats*", "at": 2.7}
#   badge (optional): top block text, default DAY N; weekly Monday covers use "WEEK N"
#   hook: 3 to 5 words, the day's curiosity hook, one key word in *stars* (lime)
#   at:   seconds into the opener proxy (pick a frame with eyes open, mouth closed)
#   zoom, y (optional): enlarge / move the photo (y in px, negative = up) so the face sits between badge and hook
# Output: dayN/dayN_cover.jpg (1080x1920) + dayN/dayN_cover_check.jpg (full + Instagram 3:4 grid crop side by side)
import json, os, subprocess, sys
from PIL import Image
d = sys.argv[1]; s = json.load(open(f'{d}/script.json')); c = s['cover']
src = s.get('opener') or c['clip']  # no filmed opener: give "clip" (a face clip) in the cover block
pub = f'kvf-video/public/{d}'; os.makedirs(pub, exist_ok=True)
subprocess.run(['ffmpeg','-v','error','-y','-ss',str(c.get('at',1.5)),'-i',f'work/{src}.mp4','-frames:v','1','-q:v','2',f'{pub}/cover_bg.jpg'],check=True)
json.dump({'bg':f'{d}/cover_bg.jpg','day':s['day'],'hook':c['hook'],'zoom':c.get('zoom',1),'y':c.get('y',0),**({'badge':c['badge']} if c.get('badge') else {})},open(f'{pub}/cover.json','w'))
subprocess.run(['npx','remotion','still','Cover',f'../{d}/{d}_cover.png',f'--props=public/{d}/cover.json'],cwd='kvf-video',check=True,capture_output=True)
im = Image.open(f'{d}/{d}_cover.png').convert('RGB'); im.save(f'{d}/{d}_cover.jpg', quality=92)
chk = Image.new('RGB',(740,640),'white'); chk.paste(im.resize((360,640)),(0,0)); chk.paste(im.crop((0,240,1080,1680)).resize((360,480)),(380,80))
chk.save(f'{d}/{d}_cover_check.jpg', quality=85)
os.remove(f'{d}/{d}_cover.png'); print('ok', f'{d}/{d}_cover.jpg')