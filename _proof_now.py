# -*- coding: utf-8 -*-
"""_proof_now.py — collect fresh shill pairs from shard logs + state totals."""
import json, glob, os, re
os.chdir(r"C:/Users/User/tmp/tg_chat_grow")

tp = tr = 0
for f in sorted(glob.glob("mass_state_*.json")):
    try:
        s = json.load(open(f, encoding="utf-8"))
    except Exception:
        continue
    if isinstance(s, dict):
        tp += s.get("pairs", 0); tr += s.get("replies", 0)
print("state TOTAL pairs:", tp, "replies:", tr)

oks = []
for f in sorted(glob.glob("mass_*.log")):
    try:
        txt = open(f, encoding="utf-8", errors="ignore").read()
    except Exception:
        continue
    for m in re.finditer(r"\[pair\] (\S+) OK \(total (\d+)\)", txt):
        oks.append((f, m.group(1)))
seen = set(); uniq = []
for f, ch in oks:
    if ch not in seen:
        seen.add(ch); uniq.append(ch)
print("pair OK events:", len(oks), "unique chats:", len(uniq))
print("latest:", uniq[-20:])

# shill_done delta since clean restart (53 total)
sd = json.load(open("shill_done.json", encoding="utf-8"))
print("shill_done:", len(sd), "| last added:", sorted(sd)[-8:])
