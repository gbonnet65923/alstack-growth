import json, glob, re

pairs = replies = 0
bans = 0
for i in range(6):
    f = f'mass_{i}.log'
    try:
        txt = open(f, encoding='utf-8', errors='ignore').read()
    except FileNotFoundError:
        continue
    m = re.findall(r'DONE: pairs=(\d+) replies=(\d+)', txt)
    if m:
        pairs += int(m[-1][0]); replies += int(m[-1][1])
    bans += txt.count('fail: banned')

# merge state files for shill registry check
merged = {}
for sf in glob.glob('mass_state_*.json'):
    try:
        d = json.load(open(sf, encoding='utf-8'))
        if isinstance(d, dict):
            merged.update(d)
    except Exception:
        pass

print(f'pairs={pairs} replies={replies} bans={bans} state_entries={len(merged)}')
