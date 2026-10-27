# Mirror the public KvF Inbox folder into raw/ (no Mac, no connector).
import re, html, subprocess, os, sys, urllib.request
FOLDER='1XWR-6tQkJRUD0FrMcbpdEdl2HKrFUOlh'
RAW=os.path.join(os.path.dirname(os.path.abspath(__file__)),'raw'); os.makedirs(RAW,exist_ok=True)
s=subprocess.run(['curl','-sSL','--max-time','30',f'https://drive.google.com/embeddedfolderview?id={FOLDER}'],capture_output=True,text=True).stdout
items=[(i,html.unescape(t)) for k,i,t in re.findall(r'href="https://drive.google.com/(file/d|drive/folders)/([\w-]+)[^"]*".*?flip-entry-title">([^<]+)<',s,re.S) if k=='file/d']
first=sys.argv[1:]  # names to fetch first
ONLY=set(os.environ.get('ONLY','').split(','))-{''}
items.sort(key=lambda x:(x[1] not in first, x[1]))
for fid,name in items:
    if re.match(r'(?i)^day\d+_', name): continue  # finished videos Kent re-uploads
    if ONLY and name not in ONLY: continue
    out=f'{RAW}/{name}'
    if os.path.exists(out): continue
    r=subprocess.run(['curl','-sSL','--max-time','1800','-o',out+'.part','-w','%{http_code} %{content_type}',
        f'https://drive.usercontent.google.com/download?id={fid}&export=download&confirm=t'],capture_output=True,text=True)
    if r.stdout.startswith('200') and 'html' not in r.stdout:
        os.rename(out+'.part',out); print('ok',name,os.path.getsize(out)//1000000,'MB',flush=True)
    else:
        os.remove(out+'.part') if os.path.exists(out+'.part') else None; print('FAIL',name,r.stdout,r.stderr[:200],flush=True)
print('SYNC DONE',flush=True)