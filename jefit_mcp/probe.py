import re
import requests
from urllib.parse import urljoin

BASE='https://www.jefit.com'
URL=BASE+'/build-routine'
H={'user-agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/131 Safari/537.36'}

r=requests.get(URL,headers=H,timeout=30)
print('PAGE',r.status_code,r.url,len(r.text))
html=r.text
scripts=[]
for src in re.findall(r'<script[^>]+src=["\']([^"\']+)["\']',html,re.I):
    u=urljoin(BASE,src)
    if u not in scripts:scripts.append(u)

TARGETS=[
    'addSetToDayExercise','updateSet','removeSetFromDayExercise',
    'day_exercises/${','/api/v2/day_exercises/','sets:',
    'rest_time','interval_time_enabled','superset',
    'postFetcher)("/api/v2/user/routines"','create_day',
    'postFetcher)(`/api/v2/routines/${','postFetcher)(`/api/v2/days/${',
]

def contexts(label,text):
    low=text.lower()
    emitted=0
    for target in TARGETS:
        pos=0
        needle=target.lower()
        while True:
            i=low.find(needle,pos)
            if i<0: break
            print(f'\n===== {label} TARGET {target} @ {i} =====')
            print(text[max(0,i-1800):min(len(text),i+3200)])
            emitted += 1
            pos=i+len(needle)
            if emitted >= 35: return

contexts('HTML',html)
for idx,s in enumerate(scripts):
    x=requests.get(s,headers=H,timeout=30)
    if not x.ok: continue
    if any(t.lower() in x.text.lower() for t in TARGETS):
        print(f'\n######## CHUNK JS{idx} {s} len={len(x.text)} ########')
        contexts(f'JS{idx}',x.text)
