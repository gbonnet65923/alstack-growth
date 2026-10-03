# -*- coding: utf-8 -*-
import json, sys, glob, time, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
BASE = r"C:/Users/User/tmp/tg_chat_grow"
os.chdir(BASE)

print("=== mass_state shard files ===")
for f in sorted(glob.glob('mass_state_*.json')):
    try:
        d = json.load(open(f, encoding='utf-8'))
    except Exception as e:
        print(f, 'ERR', e); continue
    if isinstance(d, dict):
        print(f, 'keys:', list(d.keys())[:15])
        for k in ('log', 'history', 'shards', 'stats', 'started', 'ts', 'progress', 'done', 'accounts'):
            v = d.get(k)
            if isinstance(v, list):
                print('  ', k, 'len', len(v), 'last:', json.dumps(v[-1], ensure_ascii=False)[:200] if v else '')
            elif v is not None:
                print('  ', k, '=', str(v)[:150])
    elif isinstance(d, list):
        print(f, 'list len', len(d), 'sample:', json.dumps(d[0], ensure_ascii=False)[:200] if d else '')

print()
print("=== shill_done.json ===")
sd = json.load(open('shill_done.json', encoding='utf-8'))
print('type', type(sd).__name__)
if isinstance(sd, dict):
    ks = list(sd.keys())
    print('keys', len(ks), 'sample keys:', ks[:5])
    for k in ks[:2]:
        print('  ', k, '->', json.dumps(sd[k], ensure_ascii=False)[:250])
elif isinstance(sd, list):
    print('len', len(sd), 'sample:', json.dumps(sd[:3], ensure_ascii=False)[:300])

print()
print("=== hunter files ===")
for f in ['live_groups_found.json', 'hunter_state.json', 'hunter_progress.json']:
    if os.path.exists(f):
        d = json.load(open(f, encoding='utf-8'))
        if isinstance(d, list):
            print(f, 'list', len(d), 'sample:', json.dumps(d[0], ensure_ascii=False)[:200] if d else '')
        elif isinstance(d, dict):
            print(f, 'dict', len(d), 'keys:', list(d.keys())[:10])
    else:
        print(f, 'MISSING')

print()
print("=== pool files ===")
for f in ['pool_merged.json', 'good_chats.json', 'addlist_resolved.json', 'ai_groups.json', 'target_channels.json']:
    if os.path.exists(f):
        d = json.load(open(f, encoding='utf-8'))
        n = len(d)
        s = json.dumps(d[0] if isinstance(d, list) else next(iter(d.items())), ensure_ascii=False)[:180]
        print(f, n, 'sample:', s)
    else:
        print(f, 'MISSING')

print()
print("=== progress/state files ===")
for f in ['react_progress.json', 'sub_progress.json', 'inviter_state.json', 'spambot_classified.json']:
    if os.path.exists(f):
        d = json.load(open(f, encoding='utf-8'))
        n = len(d)
        s = json.dumps(d[0] if isinstance(d, list) else list(d.items())[:1], ensure_ascii=False)[:180]
        print(f, n, 'sample:', s)

print()
print("=== logs present ===")
for f in sorted(glob.glob('*.log')):
    print(f, os.path.getsize(f), 'mtime', int(time.time() - os.path.getmtime(f)), 's ago')
