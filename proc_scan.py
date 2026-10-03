import psutil, time, sys, os
KEYS = ('wave_chain', 'merge_pool', 'harvest_atlas', 'chat_hunter', 'mass_seed.py', 'shard_worker')
rows = []
for p in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
    try:
        nm = (p.info['name'] or '').lower()
        if 'python' not in nm:
            continue
        cl = ' '.join(p.info['cmdline'] or [])
        if 'proc_scan' in cl:
            continue
        for k in KEYS:
            if k in cl:
                age = round((time.time() - p.info['create_time']) / 60)
                exe = os.path.basename(p.info['cmdline'][0])
                rows.append((k, p.pid, age, exe, p.parent().pid if p.parent() else None))
                break
    except Exception:
        pass
rows.sort()
for r in rows:
    print('%-16s pid=%-7s age=%sm exe=%s parent=%s' % r)
print('total:', len(rows))
from collections import Counter
print(Counter(r[0] for r in rows))
