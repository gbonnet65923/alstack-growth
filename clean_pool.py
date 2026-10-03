# -*- coding: utf-8 -*-
"""clean_pool.py — purge non-AI chats from pool_merged.json using pool_filter."""
import json, os
from pool_filter import is_ai

BASE = r"C:/Users/User/tmp/tg_chat_grow"
os.chdir(BASE)

pm = json.load(open("pool_merged.json", encoding="utf-8"))
keep = [e for e in pm if is_ai(e)]
drop = [e for e in pm if not is_ai(e)]
json.dump(keep, open("pool_merged.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
prev = []
try: prev = json.load(open("pool_dropped.json", encoding="utf-8"))
except Exception: pass
json.dump(prev + drop, open("pool_dropped.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"pool: {len(pm)} -> {len(keep)} AI-only, dropped {len(drop)}")
for e in drop[:20]:
    print("  DROP:", e.get("channel"), "|", (e.get("title") or "")[:45])
print("--- KEPT sample ---")
for e in keep[:15]:
    print("  KEEP:", e.get("channel"), "|", (e.get("title") or "")[:45])
