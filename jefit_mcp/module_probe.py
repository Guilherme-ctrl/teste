import re
import requests

URLS = [
    'https://www.jefit.com/_next/static/chunks/0hqzp32yun7i1.js',
    'https://www.jefit.com/_next/static/chunks/1cpodm8jo6dh7.js',
    'https://www.jefit.com/_next/static/chunks/2su1k-5ex2ps7.js',
]
TERMS = [
    'addDayToRoutine','changeRoutineRemote','changeDayRemote','deleteDayFromRoutine',
    'copyDayToRoutine','handleDayExerciseReorder','handleDayIndexUpdate',
    'addDayExerciseToDay','changeDayExerciseRemote','addSetToDayExercise',
    'removeSetFromDayExercise','deleteDayExercise','toggleSuperset','updateSet','useRoutine'
]
H={'User-Agent':'Mozilla/5.0'}

# Turbopack module boundaries look like: },123456,e=>{
BOUNDARY = re.compile(r'\},(\d+),e=>\{')

for url in URLS:
    text = requests.get(url, headers=H, timeout=30).text
    print(f'FILE {url} {len(text)}', flush=True)
    bounds = [(m.start()+1, m.group(1)) for m in BOUNDARY.finditer(text)]
    starts = [x[0] for x in bounds]
    seen = set()
    for term in TERMS:
        for hit in [m.start() for m in re.finditer(re.escape(term), text)]:
            # preceding module boundary
            prev = None
            for pos, mid in bounds:
                if pos <= hit:
                    prev = (pos, mid)
                else:
                    break
            if not prev:
                start, mid = 0, 'HEAD'
            else:
                start, mid = prev
            end = len(text)
            for pos, _ in bounds:
                if pos > hit:
                    end = pos
                    break
            module = text[start:end]
            key=(url,mid)
            # We want the defining module, not UI call-sites.
            has_export = ('e.s([' in module and term in module)
            has_http = any(k in module for k in ['postFetcher','postEndpoint','patchEndpoint','putEndpoint','deleteEndpoint','getEndpoint'])
            has_fn_defs = sum(t in module for t in TERMS) >= 4
            if key not in seen and (has_export or (has_http and has_fn_defs)):
                seen.add(key)
                print(f'\n=== MODULE {mid} TERM {term} LEN {len(module)} ===', flush=True)
                print(module[:50000], flush=True)
    print('END_FILE', flush=True)
print('DONE', flush=True)
