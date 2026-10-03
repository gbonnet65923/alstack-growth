# -*- coding: utf-8 -*-
"""Merge addlist_resolved.json -> pool_merged.json (mass_seed format)."""
import json, os, sys
BASE = r"C:/Users/User/tmp/tg_chat_grow"
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

pool = json.load(open(os.path.join(BASE, "pool_merged.json"), encoding="utf-8"))
have = {(g.get("channel") or "").lower() for g in pool}
have |= {str(g.get("linked_id")) for g in pool if g.get("linked_id")}

data = json.load(open(os.path.join(BASE, "addlist_resolved.json"), encoding="utf-8"))
chs = data["channels"]

SKIP = {"alstack"}  # Vlad's own channel - forbidden target
added, skipped = [], []
for c in chs:
    if "err" in c:
        continue
    un = c.get("username")
    cid = c.get("id")
    if not un and not cid:
        continue
    key = (un or "").lower() or str(cid)
    if key in SKIP or str(cid) in SKIP:
        skipped.append((un, "own-channel"))
        continue
    members = c.get("members") or 0
    if members < 20:
        skipped.append((un, "tiny"))
        continue
    mega = bool(c.get("megagroup"))
    linked = c.get("linked_id")
    if not mega and not linked:
        skipped.append((un, "no-comments"))  # broadcast w/o comment group: nowhere to post
        continue
    if key in have or (linked and str(linked) in have):
        skipped.append((un, "dupe"))
        continue
    if mega:
        chan = un or str(cid)
        rec = {"channel": chan, "title": c.get("title", ""), "linked_id": None,
               "members": members, "recent_human": 0, "recent_senders": 0, "direct": True}
    else:
        chan = un or str(cid)
        rec = {"channel": chan, "title": c.get("title", ""), "linked_id": linked,
               "members": members, "recent_human": 0, "recent_senders": 0, "direct": False}
    rec["source"] = "addlist_1R6yXdAEgokxZTcy"
    pool.append(rec)
    have.add(key)
    added.append(rec)

json.dump(pool, open(os.path.join(BASE, "pool_merged.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"added={len(added)} skipped={len(skipped)} pool_total={len(pool)}")
for r in added:
    print(" +", r["channel"], r["members"], "direct" if r["direct"] else f"linked={r['linked_id']}")
for s in skipped:
    print(" -", s)
