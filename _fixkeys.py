
import json
pm = json.load(open("pool_merged.json", encoding="utf-8"))
out = []
for e in pm:
    if not e.get("channel"):
        u = e.get("username") or e.get("user_name") or ""
        u = str(u).replace("@", "").strip()
        if u:
            e = {**e, "channel": u}
        else:
            continue
    out.append(e)
json.dump(out, open("pool_merged.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("pool:", len(pm), "->", len(out))
