import re
import requests
from urllib.parse import urljoin

BASE='https://www.jefit.com'
URL=BASE+'/build-routine'
H={'user-agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/131 Safari/537.36'}

r=requests.get(URL,headers=H,timeout=30)
print('PAGE',r.status_code,r.url,len(r.text))
html=r.text

# Script sources
scripts=[]
for src in re.findall(r'<script[^>]+src=["\']([^"\']+)["\']',html,re.I):
    u=urljoin(BASE,src)
    if u not in scripts:scripts.append(u)
print('SCRIPTS',len(scripts))
for s in scripts: print('SCRIPT',s)

# Interesting patterns from page itself
patterns=[
    r'https?://[^"\'\s<>]+',
    r'/api/[A-Za-z0-9_?&=./{}:-]+',
    r'(?i)(?:create|save|update|delete)[A-Za-z0-9_]*(?:routine|workout|plan)[A-Za-z0-9_]*',
    r'(?i)(?:routine|workout|plan)[A-Za-z0-9_]*(?:create|save|update|delete)[A-Za-z0-9_]*',
]

def scan(label,text):
    hits=set()
    for p in patterns:
        for m in re.finditer(p,text):
            v=m.group(0)
            if len(v)<300:hits.add(v)
    for h in sorted(hits):
        if any(x in h.lower() for x in ['api/','routine','workout','plan']):
            print(label,'HIT',h[:500])
    # Context around likely endpoint/action words
    keys=['/api/','routine','saveRoutine','createRoutine','updateRoutine','build-routine','server action','action=']
    low=text.lower()
    shown=set()
    for key in keys:
        start=0
        k=key.lower()
        while True:
            i=low.find(k,start)
            if i<0:break
            frag=text[max(0,i-220):min(len(text),i+420)].replace('\n',' ')
            sig=frag[:120]
            if sig not in shown:
                shown.add(sig); print(label,'CTX',frag[:700])
            start=i+len(k)
            if len(shown)>40:return

scan('HTML',html)

for idx,s in enumerate(scripts):
    try:
        x=requests.get(s,headers=H,timeout=30)
        print('FETCH',idx,x.status_code,len(x.text),s)
        if x.ok: scan(f'JS{idx}',x.text)
    except Exception as e:
        print('ERR',s,repr(e))
