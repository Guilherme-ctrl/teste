import re
import requests

URLS = [
    'https://www.jefit.com/_next/static/chunks/0hqzp32yun7i1.js',
    'https://www.jefit.com/_next/static/chunks/1cpodm8jo6dh7.js',
]
H={'User-Agent':'Mozilla/5.0'}
TERMS=[
 'changeRoutineRemote','addDayToRoutine','changeDayRemote','deleteDayFromRoutine',
 'copyDayToRoutine','handleDayExerciseReorder','handleDayIndexUpdate',
 'addDayExerciseToDay','changeDayExerciseRemote','addSetToDayExercise',
 'removeSetFromDayExercise','deleteDayExercise','toggleSuperset','updateSet',
 'makeNewPrivateRoutine','/api/v2/user/routines'
]
for fi,u in enumerate(URLS):
    t=requests.get(u,headers=H,timeout=30).text
    print('FILE',fi,len(t),u,flush=True)
    # Find likely module(s) defining/exporting the routine functions.
    for term in TERMS:
        start=0
        n=0
        while True:
            p=t.find(term,start)
            if p<0: break
            n+=1
            # nearest module boundary before occurrence
            left=max(0,p-10000)
            frag=t[left:min(len(t),p+14000)]
            # Only print contexts with actual API helper usage or exports; avoid UI call-sites.
            low=frag.lower()
            interesting = any(x in frag for x in ['postFetcher','postEndpoint','patchEndpoint','putEndpoint','deleteEndpoint','e.s(['])
            if interesting:
                print('\n=== TERM',term,'OCC',n,'POS',p,'===',flush=True)
                print(frag,flush=True)
            start=p+len(term)
            if n>=5: break
    # Print every relevant API literal and nearby helper invocation.
    seen=set()
    for m in re.finditer(r'/api/v2/[A-Za-z0-9_?&=./${}:~-]+',t):
        s=m.group(0)
        if any(k in s.lower() for k in ['routine','day','exercise','set']):
            key=(m.start(),s)
            if key in seen: continue
            seen.add(key)
            print('\n=== API',s,'POS',m.start(),'===',flush=True)
            print(t[max(0,m.start()-1800):min(len(t),m.start()+3000)],flush=True)
print('DONE',flush=True)
