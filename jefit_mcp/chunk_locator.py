import re, requests
from urllib.parse import urljoin
H={'User-Agent':'Mozilla/5.0'}
base='https://www.jefit.com'
html=requests.get(base+'/build-routine',headers=H,timeout=30).text
scripts=[]
for src in re.findall(r'<script[^>]+src=["\']([^"\']+)["\']',html,re.I):
    u=urljoin(base,src)
    if u not in scripts: scripts.append(u)
print('SCRIPTS',len(scripts),flush=True)
for u in scripts:
    try:
        t=requests.get(u,headers=H,timeout=30).text
        if '964456' in t or 'addDayExerciseToDay' in t or 'changeRoutineRemote' in t:
            print('MATCH',u,'LEN',len(t),'964456',t.find('964456'),'addDay',t.find('addDayExerciseToDay'),'change',t.find('changeRoutineRemote'),flush=True)
            for needle in ['964456','addDayExerciseToDay','changeRoutineRemote']:
                p=t.find(needle)
                if p>=0:
                    print('CTX',needle,t[max(0,p-2500):min(len(t),p+12000)],flush=True)
    except Exception as e:
        print('ERR',u,repr(e),flush=True)
