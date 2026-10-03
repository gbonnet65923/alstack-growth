# merge_pool.py — idempotent pool merge, run in loop
import json, time, os
from pool_filter import is_ai
os.chdir(os.path.dirname(os.path.abspath(__file__)))

def load(f, d=None):
    try: return json.load(open(f, encoding="utf-8"))
    except Exception: return d if d is not None else []

DROP_KW = ["знаком","девуш","парн","chatting","dating","billieeilish","airbnb","взаимн","подписк","пиар","реакц","реферал","накрут","чат-знаком"]

def junk(entry):
    t = (entry.get("title") or "").lower()
    c = (entry.get("channel") or "").lower()
    return any(k in t or k in c for k in DROP_KW)

def norm(e):
    if not e.get("channel"):
        u = str(e.get("username") or "").replace("@", "").strip()
        if not u:
            return None
        e = {**e, "channel": u}
    return e

def key(e):
    return e.get("linked_id") or e.get("id") or e.get("channel") or e.get("username")

while True:
    pm = load("pool_merged.json", [])
    seen = set(key(e) for e in pm)
    added = 0
    # harvest groups
    for e in load("ai_groups.json", []) + load("ai_groups_new3.json", []):
        k = key(e)
        if k and k not in seen and not junk(e) and is_ai(e) and norm(e):
            pm.append({**norm(e), "direct": bool(e.get("direct")) or not e.get("linked_id"), "recent_human": None, "recent_senders": None, "src": "harvest"})
            seen.add(k); added += 1
    # tgstat validated
    for e in load("tgstat_valid.json", []):
        k = key(e)
        if k and k not in seen and not junk(e) and is_ai(e) and norm(e):
            pm.append({**norm(e), "src": "tgstat"})
            seen.add(k); added += 1
    # atlas harvest
    for e in load("atlas_groups.json", []):
        k = key(e)
        if k and k not in seen and not junk(e) and is_ai(e) and norm(e):
            pm.append({**norm(e), "direct": False, "src": "atlas"})
            seen.add(k); added += 1
    # hunter found (both)
    for e in load("live_groups_found.json", []) + load("live_groups_found2.json", []):
        k = key(e)
        if k and k not in seen and not junk(e) and is_ai(e) and norm(e):
            pm.append({**norm(e), "src": "hunter"})
            seen.add(k); added += 1
    if added:
        tmp = "pool_merged.json.tmp"
        json.dump(pm, open(tmp, "w", encoding="utf-8"), ensure_ascii=False)
        os.replace(tmp, "pool_merged.json")
        print(f"[merge] +{added} -> pool {len(pm)}", flush=True)
    else:
        print(f"[merge] no new, pool {len(pm)}", flush=True)
    time.sleep(900)
