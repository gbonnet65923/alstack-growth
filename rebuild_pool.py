# -*- coding: utf-8 -*-
"""rebuild_pool.py — restore candidates from pool_dropped + current pool, re-filter with new rules."""
import json, os
from pool_filter import is_ai

BASE = r"C:/Users/User/tmp/tg_chat_grow"
os.chdir(BASE)

def load(f):
    try: return json.load(open(f, encoding="utf-8"))
    except Exception: return []

pm = load("pool_merged.json")
dr = load("pool_dropped.json")
seen, cands = set(), []
for e in pm + dr:
    k = e.get("linked_id") or e.get("id") or e.get("channel")
    if k and k not in seen:
        seen.add(k); cands.append(e)

keep = [e for e in cands if is_ai(e)]
drop = [e for e in cands if not is_ai(e)]
json.dump(keep, open("pool_merged.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump(drop, open("pool_dropped.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"candidates: {len(cands)} -> keep {len(keep)}, drop {len(drop)}")
print("--- KEEP ---")
for e in keep[:30]:
    print(" ", e.get("channel"), "|", (e.get("title") or "")[:50])
print("--- DROP sample ---")
for e in drop[:10]:
    print(" ", e.get("channel"), "|", (e.get("title") or "")[:50])
