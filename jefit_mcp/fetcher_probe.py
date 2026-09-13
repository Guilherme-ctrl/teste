import re
import requests
from urllib.parse import urljoin

BASE = 'https://www.jefit.com/build-routine'
H = {'User-Agent': 'Mozilla/5.0'}
html = requests.get(BASE, headers=H, timeout=30).text
scripts = []
for src in re.findall(r'<script[^>]+src=["\']([^"\']+)', html, re.I):
    u = urljoin(BASE, src)
    if u not in scripts:
        scripts.append(u)

needles = ['995160', 'postFetcher', 'patchFetcher', 'postEndpoint', 'patchEndpoint']
for idx, u in enumerate(scripts):
    text = requests.get(u, headers=H, timeout=30).text
    if not any(n in text for n in needles):
        continue
    print(f'### CHUNK {idx} {u} len={len(text)}', flush=True)
    for needle in needles:
        pos = 0
        count = 0
        while True:
            i = text.find(needle, pos)
            if i < 0:
                break
            print(f'--- {needle} @{i} ---', flush=True)
            print(text[max(0, i-2500):min(len(text), i+6500)], flush=True)
            pos = i + len(needle)
            count += 1
            if count >= 12:
                break
print('DONE', flush=True)
