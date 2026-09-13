import requests

URL='https://www.jefit.com/_next/static/chunks/0hqzp32yun7i1.js'
t=requests.get(URL,headers={'User-Agent':'Mozilla/5.0'},timeout=30).text
needle='964456,e=>{'
p=t.find(needle)
print('POS',p,'LEN',len(t),flush=True)
if p<0:
    raise SystemExit('module not found')
# Find next numeric module boundary. Enough because Turbopack emits },NNNNNN,e=>{
q=p+len(needle)
while True:
    j=t.find('},',q)
    if j<0:
        end=len(t);break
    k=j+2
    d=k
    while d<len(t) and t[d].isdigit(): d+=1
    if d>k and t[d:d+5]==',e=>{':
        end=j+1;break
    q=j+2
module=t[p:end]
print('MODULE_LEN',len(module),flush=True)
print(module,flush=True)
