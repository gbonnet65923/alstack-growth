# -*- coding: utf-8 -*-
"""good_filter.py — strict re-filter of ALL harvested candidates.
Gate: STRONG_AI hit, no HARD_DROP, no SOFT_DROP, not already shilled, members>=MIN.
Writes good_chats.json sorted by members desc.
"""
import json, glob, os, sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
from pool_filter import STRONG_AI_RE, HARD_DROP_RE, SOFT_DROP_RE

MIN = int(sys.argv[1]) if len(sys.argv) > 1 else 200

done = set(json.load(open(os.path.join(BASE, 'shill_done.json'), encoding='utf-8')))

cands = {}

def add(src, items):
    for e in items:
        if not isinstance(e, dict):
            continue
        ch = (e.get('channel') or e.get('username') or '').lstrip('@')
        if not ch:
            continue
        try:
            m = int(e.get('members') or e.get('member_count') or 0)
        except Exception:
            m = 0
        t = str(e.get('title') or '')
        hay = (t + ' ' + ch).lower()
        prev = cands.get(ch)
        if prev is None or m > prev[0]:
            cands[ch] = (m, t, src, hay)

for f in sorted(glob.glob(os.path.join(BASE, 'hunter_candidates_*.json'))):
    try:
        add('hunter', json.load(open(f, encoding='utf-8')))
    except Exception as ex:
        print('ERR', f, ex)

for name in ['atlas_groups.json','ai_groups.json','ai_groups_live.json','tgstat_all.json','tgstat_valid.json','pool_merged.json','live_groups_found.json','live_groups_found2.json','donors_ai.json',
             'pool_filtered.json', 'ai_groups_live.json', 'tgstat_pool.json']:
    p = os.path.join(BASE, name)
    if not os.path.exists(p):
        continue
    try:
        d = json.load(open(p, encoding='utf-8'))
        items = d if isinstance(d, list) else (d.get('items') or d.get('groups') or [])
        add(name, items)
    except Exception as ex:
        print('ERR', p, ex)

print('all candidates:', len(cands))

good = []
for ch, (m, t, src, hay) in cands.items():
    if ch in done:
        continue
    if HARD_DROP_RE.search(hay):
        continue
    if SOFT_DROP_RE.search(hay):
        continue
    if not STRONG_AI_RE.search(hay):
        continue
    if m < MIN:
        continue
    good.append((m, ch, t, src))

good.sort(reverse=True)
print('strict good NEW (members>=%d): %d' % (MIN, len(good)))
for m, ch, t, src in good:
    print('%7d  @%-30s %-45s [%s]' % (m, ch, t[:45], src))

json.dump([{'channel': ch, 'title': t, 'members': m, 'src': src} for m, ch, t, src in good],
          open(os.path.join(BASE, 'good_chats.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('saved -> good_chats.json')
