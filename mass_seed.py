# -*- coding: utf-8 -*-
"""
Mass parallel seeder. Shards run as separate processes, each with its own
account slice + group slice, no shared session files, shared JSON state with
atomic write + shard suffix files merged at report time.

Target: >=100 actions/day (pairs + replies).
Usage: python mass_seed.py --shards 4 --pairs-per-group 2 --replies-per-group 2
"""
import asyncio, json, os, random, sys, time, datetime

BASE = r"C:/Users/User/tmp/tg_chat_grow"

def load_groups():
    groups = []
    for fn in ["pool_merged.json"]:
        p = os.path.join(BASE, fn)
        if os.path.exists(p):
            groups += json.load(open(p, encoding="utf-8"))
    # dedupe by (channel, linked_id)
    seen = set(); out = []
    for g in groups:
        k = (g.get("channel"), g.get("linked_id"))
        if k in seen: continue
        seen.add(k)
        if (g.get("direct") or g.get("linked_id")) and (g.get("members") or 0) >= 20:
            out.append(g)
    out.sort(key=lambda g: (g.get("direct", False), g.get("recent_human") or 0, g.get("members") or 0), reverse=True)
    return out

def load_accounts():
    import shutil
    SRC = r"C:/Users/User/Desktop/CLEAN_ALIVE_SESSIONS"
    WORK = os.path.join(BASE, "mass")
    os.makedirs(WORK, exist_ok=True)
    clean = json.load(open(os.path.join(BASE, "spambot_classified.json"), encoding="utf-8"))["ok"]
    paths = []
    for stem in clean:
        src_f = os.path.join(SRC, stem + ".session")
        if not os.path.exists(src_f): continue
        dst = os.path.join(WORK, stem)
        if not os.path.exists(dst + ".session"):
            try: shutil.copy(src_f, dst + ".session")
            except Exception: continue
        paths.append(dst)
    return paths

def shard_state(shard):
    return os.path.join(BASE, f"mass_state_{shard}.json")

def load_shard(shard):
    p = shard_state(shard)
    if os.path.exists(p): return json.load(open(p, encoding="utf-8"))
    return {"pairs": 0, "replies": 0, "done_groups": [], "fails": {}, "log": []}

def save_shard(shard, st):
    p = shard_state(shard)
    tmp = p + ".tmp"
    json.dump(st, open(tmp, "w", encoding="utf-8"), ensure_ascii=False)
    os.replace(tmp, p)

def main():
    args = sys.argv[1:]
    shards = int(args[args.index("--shards") + 1]) if "--shards" in args else 4
    ppg = int(args[args.index("--pairs-per-group") + 1]) if "--pairs-per-group" in args else 2
    rpg = int(args[args.index("--replies-per-group") + 1]) if "--replies-per-group" in args else 2

    groups = load_groups()
    accs = load_accounts()
    if len(accs) < shards * 2:
        print(f"not enough accounts: {len(accs)}"); return
    random.shuffle(accs)
    print(f"groups={len(groups)} accounts={len(accs)} shards={shards} pairs/g={ppg} replies/g={rpg}")

    procs = []
    for i in range(shards):
        g_slice = groups[i::shards]
        a_slice = accs[i * (len(accs) // shards):(i + 1) * (len(accs) // shards)]
        log = os.path.join(BASE, f"mass_{i}.log")
        cmd = [
            "python", os.path.join(BASE, "shard_worker.py"),
            "--shard", str(i), "--groups", json.dumps([g["channel"] for g in g_slice]),
            "--pairs-per-group", str(ppg), "--replies-per-group", str(rpg),
            "--accounts", json.dumps([os.path.basename(a) for a in a_slice[:12]]),
        ]
        env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
        p = __import__("subprocess").Popen(cmd, stdout=open(log, "w", encoding="utf-8"),
                                          stderr=__import__("subprocess").STDOUT, env=env, cwd=BASE)
        procs.append(p)
        print(f"shard {i}: pid={p.pid} groups={len(g_slice)} accs={len(a_slice[:12])} -> {os.path.basename(log)}")
    print("all shards launched. monitor: mass_*.log, merge: mass_state_*.json")

if __name__ == "__main__":
    main()
