import json, glob, os, re
os.chdir(r"C:/Users/User/tmp/tg_chat_grow")
tp = tr = 0
for f in sorted(glob.glob("mass_state_*.json")):
    s = json.load(open(f, encoding="utf-8"))
    p, rp = s.get("pairs", 0), s.get("replies", 0)
    tp += p; tr += rp
    print(f, "pairs=", p, "replies=", rp)
print("TOTAL pairs:", tp, "replies:", tr)

# fresh t.me proof links from shard logs
proofs = []
for f in sorted(glob.glob("mass_*.log")):
    txt = open(f, encoding="utf-8", errors="ignore").read()
    for m in re.finditer(r"\[(\w+)\] (\S+) OK \(total (\d+)\)", txt):
        proofs.append((f, m.group(2), m.group(1)))
print("OK-events this run:", len(proofs))
for p in proofs[-15:]:
    print(p)
